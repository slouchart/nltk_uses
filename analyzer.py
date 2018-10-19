from langdetect import detect
from importlib import import_module
from converters import extract_raw_text
import filters
from copy import copy


class Analyzer:
    def __init__(self, builder, source, default_lang):
        self._pipeline = list()
        self._tokenizer = None

        self._source = source

        self._builder = builder
        self._input_text = None
        self._input_lang = None
        self._default_lang = default_lang
        self._tokens = []

    def _prepare_source(self, source):
        src_handler = self._source(source)
        self._input_text = src_handler.extract_raw_text()
        self._input_lang = src_handler.detect_lang()
        self._detected_lang = self._input_lang

    def _build_elements(self):
        self._tokenizer, self._pipeline, self._input_lang = self._builder(self._input_lang, self._default_lang)
        assert self._tokenizer is not None
        assert len(self._pipeline) > 0

    def analyze(self, source):
        self._prepare_source(source)
        self._build_elements()
        self._tokens = self._tokenizer(self._input_text)
        for op in self._pipeline:
            self._tokens = op(self._tokens)

    def get_tokens(self):
        return copy(self._tokens)

    @property
    def lang(self):
        return self._input_lang

    @property
    def detected_lang(self):
        return self._detected_lang

    @property
    def raw_text(self):
        return self._input_text


def pipeline_builder(lang, default_lang):
    pipeline = list()

    try:
        lang_mod = import_module(f'lang.{lang}')
    except ImportError:
        lang = default_lang
        try:
            lang_mod = import_module(f'lang.{lang}')
        except ImportError:
            lang = 'en'
            lang_mod = import_module(f'lang.{lang}')

    tokenizer = getattr(lang_mod, 'tokenize')

    pipeline.append(filters.filter_punctuation)
    pipeline.append(getattr(lang_mod, 'filter_stopwords'))
    pipeline.append(filters.filter_numerals)
    pipeline.append(getattr(lang_mod, 'stem'))
    return tokenizer, pipeline, lang


class SourceFilename:
    def __init__(self, filename):
        self._filename = filename
        self._text = None

    def extract_raw_text(self):
        self._text = extract_raw_text(self._filename)
        return self._text

    def detect_lang(self):
        return detect(self._text)


class SourceRawText:
    def __init__(self, text):
        self._text = text

    def extract_raw_text(self):
        return self._text

    def detect_lang(self):
        return detect(self._text)
