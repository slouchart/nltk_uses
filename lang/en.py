from nltk.corpus import stopwords
from nltk.stem import PorterStemmer
from nltk.tokenize import WordPunctTokenizer
import re


def filter_stopwords(tokens):
    regexp_apo = re.compile(r"(\w+)'")
    filtered = []
    for tok in tokens:
        temp_tok = tok
        if regexp_apo.match(tok):
            temp_tok = tok[:-1]

        # removing stop words
        if temp_tok not in stopwords.words('english'):
            filtered.append(temp_tok)

    return filtered


def stem(tokens):
    stemmer = PorterStemmer()
    return [stemmer.stem(tok) for tok in tokens]


def tokenize(text):
    tokenizer = WordPunctTokenizer()
    return tokenizer.tokenize(text.lower())
