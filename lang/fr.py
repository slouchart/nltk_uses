from nltk.corpus import stopwords
from nltk.stem import SnowballStemmer
from nltk.tokenize import RegexpTokenizer
import re


def filter_stopwords(tokens):
    regexp_apo = re.compile(r"(\w+)'")
    filtered = []
    for tok in tokens:
        temp_tok = tok
        if regexp_apo.match(tok):
            temp_tok = tok[:-1]

        # removing stop words
        if temp_tok not in stopwords.words('french'):
            filtered.append(temp_tok)

    return filtered


def stem(tokens):
    stemmer = SnowballStemmer('french')
    return [stemmer.stem(tok) for tok in tokens]


def tokenize(text):
    regexp_fr = r'''(?x)
                 \w+' |  # mots suivis d'une apostrophe sans cette dernière (élisions)
                 \w+  |  # mots pleins
                 [^\w\s] # ponctuation
                 '''
    tokenizer = RegexpTokenizer(regexp_fr)
    return tokenizer.tokenize(text.lower())
