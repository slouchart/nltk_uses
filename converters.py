import pdfminer.layout
import pdfminer.high_level
import io


def extract_raw_text(pdf_filename):
    output = io.StringIO()
    params = pdfminer.layout.LAParams()  # Using the defaults seems to work fine

    with open(pdf_filename, "rb") as file:
        pdfminer.high_level.extract_text_to_fp(file, output, laparams=params)

    return output.getvalue()
