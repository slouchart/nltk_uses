import re


def filter_punctuation(tokens):
    regexp_punct = re.compile(r'[^\w\s]')
    return [tok for tok in tokens if not regexp_punct.match(tok)]


def filter_numerals(tokens):
    regexp_nums = re.compile(r'\d+')
    return [tok for tok in tokens if not regexp_nums.match(tok)]
