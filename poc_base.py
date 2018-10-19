import glob
from docbase import DocumentBase


if __name__ == '__main__':
    path = r'D:\Users\slouchart\Documents\cv_sources\*.pdf'

    """
    Step one: preparing the database from documents
    In this PoC, it's done every time because there is no persistance of the doc base
    In a real production env, this step is done only when a new document is received
    """
    docbase = DocumentBase()
    nbfiles = 0
    for filename in glob.iglob(path, recursive=False):
        tokens = []
        doc = None
        print(f'processing file {filename}...')
        try:
            docbase.add_document(filename)
        except ModuleNotFoundError as e:
            print(f'exception {e} occurred while processing {filename}')
            print('processing next file')
            continue
        except BaseException as e:  # the class of exception is too broad, yeah. Like who cares.
            print(f'unexpected exception {e} occurred while processing {filename}')
            print('process aborted...')
            break
        nbfiles += 1

    # some sanity checks
    assert docbase.document_count == nbfiles
    assert len(docbase.features) == docbase.term_count

    assert len(docbase.vectors) == docbase.document_count
    assert docbase.document_count > 0

    """
    Step two: put together a request and match it against the doc base
    This is where lies the real value of the service: getting relevant entries
    from the doc base based on the similarity of their contents with the request
    and ranking the results on their degree of relevancy i.e. similarity
    """
    query_text = "python machine learning scikit-learn"

    for r in docbase.search(query_text):
        print(r)
