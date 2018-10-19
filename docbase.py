from hashlib import sha1
from collections import namedtuple
from math import log10
from copy import copy
from vector import cosine_similarity

from analyzer import Analyzer, SourceFilename, pipeline_builder, SourceRawText
import statistics


class DocumentBase:
    class Transaction:

        document_entry_factory = namedtuple('DocumentEntry', ('doc_id', 'raw_text', 'lang', 'name'))
        index_entry_factory = namedtuple('IndexEntry', ('term', 'positions'))

        def __init__(self, docbase):
            self._parent = docbase
            self._docbase_entry = None
            self._terms = dict()
            self._term_features = dict()
            self._vectors = dict()
            self._vector_base_map = dict()

        def add_document(self, doc_id, raw_text, lang, name):
            factory = self.document_entry_factory
            self._docbase_entry = factory(doc_id, raw_text, lang, name)

        def add_terms(self, tokens):
            assert self._docbase_entry is not None

            for pos, tok in enumerate(tokens):
                if tok in self._terms:
                    self._terms[tok].positions[0][1].append(pos)
                else:
                    factory = self.index_entry_factory
                    self._terms[tok] = factory(tok, [(self._docbase_entry.doc_id, [pos])])

        def compute_features(self):
            nb_terms = len(self._terms.keys())
            doc_id = self._docbase_entry.doc_id

            for t, entry in self._terms.items():
                self._term_features[t] = (doc_id, len(entry.positions[0][1]) / nb_terms)

        def get_document_entry(self):
            return self._docbase_entry

        def get_indexed_terms(self):
            return self._terms

        def get_term_features(self):
            return self._term_features

    def _commit(self, transaction):
        assert transaction is not None

        # compute features (idf) before the inverted index is updated
        '''Three cases exist:
        1: a term appears only in the doc being added
        2: a term appears only in the database
        3: a term appears both in the document and in the database'''
        terms_case_1 = set(transaction.get_indexed_terms()) - set(self._inverted_index.keys())
        terms_case_2 = set(self._inverted_index.keys()) - set(transaction.get_indexed_terms())
        terms_case_3 = set(self._inverted_index.keys()) & set(transaction.get_indexed_terms())

        # not so useless sanity checks
        assert terms_case_1.isdisjoint(terms_case_2)
        assert terms_case_2.isdisjoint(terms_case_3)
        assert terms_case_3.isdisjoint(terms_case_1)

        for term in terms_case_1:
            tfs = transaction.get_term_features()[term]
            self._features[term] = (log10((self.document_count + 1) / 2), {tfs[0]: tfs[1]})

        for term in terms_case_2:
            idf = self._features[term][0]
            tfs = self._features[term][1]
            self._features[term] = (log10(self.document_count + 1) - log10(self.document_count) + idf, tfs)

        for term in terms_case_3:
            idf = self._features[term][0]
            tf = transaction.get_term_features()[term]
            tfs = self._features[term][1]
            tfs[tf[0]] = tf[1]
            self._features[term] = (log10(self.document_count + 1) - log10(1 + self.document_count * 10 ** (-idf)), tfs)

        # update document information
        entry = transaction.get_document_entry()
        self._document_base[entry.doc_id] = entry

        # update inverted index information
        terms = transaction.get_indexed_terms()
        for term in terms:
            if term in self._inverted_index:
                self._inverted_index[term].positions.append(terms[term].positions[0])
            else:
                self._inverted_index[term] = terms[term]

        # update vector space model
        new_terms = list(terms_case_1)
        if len(new_terms) > 0:
            dimension = len(self._vector_base_map)
            for dim in range(dimension, dimension + len(new_terms)):
                term = new_terms.pop()
                self._vector_base_map[term] = dim
                for doc_id, vector in self._vectors.items():
                    coordinate = 0
                    if doc_id in self._features[term][1]:
                        coordinate = self._features[term][0] * self._features[term][1][doc_id]

                    vector.append(coordinate)

        # create a vector for the document being added
        # all components are set to 0
        self._vectors[entry.doc_id] = [0] * len(self._vector_base_map)

        # compute vector
        for term in sorted(self._vector_base_map.keys(), key=lambda t: self._vector_base_map[t]):
            j = self._vector_base_map[term]
            coordinate = 0
            if entry.doc_id in self._features[term][1]:
                coordinate = self._features[term][0] * self._features[term][1][entry.doc_id]

            self._vectors[entry.doc_id][j] = coordinate

    @staticmethod
    def create_document_id(text):
        method = sha1()
        method.update(text.encode())
        return method.hexdigest()

    def __init__(self):
        self._document_base = {}
        self._inverted_index = {}
        self._features = {}
        self._vector_base_map = {}
        self._vectors = {}
        self._pdf_analyzer = Analyzer(pipeline_builder, SourceFilename, 'fr')
        self._query_analyzer = Analyzer(pipeline_builder, SourceRawText, 'fr')

    @property
    def document_count(self):
        return len(self._document_base.keys())

    @property
    def term_count(self):
        return len(self._inverted_index.keys())

    @property
    def features(self):
        return copy(self._features)

    @property
    def vectors(self):
        return copy(self._vectors)

    def _analyze_doc_helper(self, filename):
        analyzer = self._pdf_analyzer
        analyzer.analyze(filename)
        transact = self.Transaction(self)
        transact.add_document(self.create_document_id(analyzer.raw_text), analyzer.raw_text, analyzer.lang, filename)
        transact.add_terms(analyzer.get_tokens())
        transact.compute_features()

        report = {'detected lang': analyzer.detected_lang,
                  'processed lang': analyzer.lang,
                  'input size': len(analyzer.raw_text),
                  'term count': len(analyzer.get_tokens())}

        return transact, filename, report

    def analyze_document(self, filename):
        _, filename, report = self._analyze_doc_helper(filename)
        return filename, report

    def add_document(self, filename):
        transact, _, report = self._analyze_doc_helper(filename)
        self._commit(transact)

        return transact.get_document_entry().doc_id, report

    def _prepare_query(self, terms):
        analyzer = self._query_analyzer
        analyzer.analyze(terms)

        assert len(analyzer.get_tokens()) > 0
        # vectorize tokens
        # for all terms in the query, i.e. tokens, compute a vector that has
        # a component of 1 if the term is in the docbase, 0 otherwise
        tokens = set(analyzer.get_tokens())

        vector = [0] * len(self._vector_base_map)
        for term in sorted(self._vector_base_map.keys(), key=lambda t: self._vector_base_map[t]):
            j = self._vector_base_map[term]
            if term in tokens:
                vector[j] = 1

        return vector

    def search(self, query):

        query_vector = self._prepare_query(query)

        def result_generator():
            for doc_id, doc_vector in self._vectors.items():
                yield doc_id, self._document_base[doc_id].name, cosine_similarity(query_vector, doc_vector)

        # ugly pipeline for sorting and filtering the results
        results = list(result_generator())
        results = map(lambda x: (x[2], x[1]), results)
        results = filter(lambda x: x[0] > 0, results)
        results = sorted(results, key=lambda x: x[0], reverse=True)
        return iter(results)

    @property
    def full_report(self):
        """Returns:
        number of docs
        number of terms
        min, max, median content length
        min, max, median number of terms/document #  TODO
        """

        lengths = list(map(lambda e: len(e.raw_text), self._document_base.values()))
        if len(lengths):
            len_stats = min(lengths), max(lengths), statistics.mean(lengths)
        else:
            len_stats = ('n/a', 'n/a', 'n/a')

        return {'documents': self.document_count,
                'terms': self.term_count,
                'min content length': len_stats[0],
                'max content length': len_stats[1],
                'mean content length': len_stats[2], }
