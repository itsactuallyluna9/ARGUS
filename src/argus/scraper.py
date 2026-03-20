from io import BytesIO, StringIO

import requests
import trafilatura
from trafilatura.readability_lxml import is_probably_readerable
from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth
from pdf_oxide import PdfDocument
from tempfile import NamedTemporaryFile
import pyexcel
import docx

def get_page(url: str) -> str:
    try:
        resp = requests.get(url)
        content_type = resp.headers.get("Content-Type", "").lower().split(";")[0].strip()

        print(f"Fetched page with content type: {content_type}")
        print(f"Response status code: {resp.status_code} (OK: {resp.ok})")

        if content_type not in ("text/html", "application/xhtml+xml"):
            # okay, this isn't an html page? let's try to figure out if it's a pdf or something else we can handle
            match content_type:
                case "application/pdf":
                    return extract_pdf(resp.content)
                case "application/msword":
                     pass # TODO: handle classic word docs
                case "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                    return extract_docx(resp.content)
                case "text/csv" | "application/vnd.ms-excel" | "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" | "application/vnd.oasis.opendocument.spreadsheet":
                    return extract_sheet(resp.content, content_type)
                case "application/vnd.ms-powerpoint" | "application/vnd.openxmlformats-officedocument.presentationml.presentation":
                    pass # TODO: handle powerpoint presentations
                case "application/vnd.oasis.opendocument.text":
                    return extract_openword(resp.content)
                case "application/vnd.oasis.opendocument.presentation":
                    pass # TODO: handle open document presentation
                case "text/plain" | "text/markdown":
                    return resp.text # fair enough
                case "text/rtf":
                    pass # TODO: handle rtf
                case "application/json":
                    return resp.text # sure, why notpass # TODO: handle word docs
                # images?
                case _:
                     raise NotImplementedError(f"scraper - unsupported content type: {resp.headers.get('Content-Type', '')}")

        if not resp.ok or not is_probably_readerable(resp.text):
            # try again with a headless browser?
            # either something's wrong, or the page is on to us
            return get_page_chrome(url)

        markdown = trafilatura.extract(resp.text, output_format='markdown')
        return markdown
    
    except Exception as e:
        print(f"Error fetching page with requests: {e}. Returning default message.")
        return "Unable to fetch article content. This may be due to the website's structure or anti-scraping measures."
    

def get_page_chrome(url: str) -> str:
    # this should beat the "the simplest of bot detection methods."
    # it does work on cornell.
    # this is probably a commentary on something, but i'm not sure what.
    with Stealth().use_sync(sync_playwright()) as p:
        with p.chromium.launch(headless=True) as browser:
            page = browser.new_page()
            try:
                page.goto(url)
                html = page.content()
            except Exception as e:
                print(e)

    if not is_probably_readerable(html):
        raise NotImplementedError("scraper - page isn't readerable (even with fallback).")
    
    markdown = trafilatura.extract(html, output_format='markdown')
    return markdown

# MARK: - Parsers

def extract_pdf(content: bytes) -> str:
    with NamedTemporaryFile(suffix=".pdf") as tmpfile:
        tmpfile.write(content)
        tmpfile.flush()
        tmpfile.seek(0)
        with PdfDocument(tmpfile.name) as doc:
            # TODO: look into OCR support
            # cant count on everyone having nice pdfs :c
            return doc.to_markdown_all(detect_headings=True, embed_images=False)

def extract_sheet(content: bytes, content_type: str) -> str:
    lookup = {
        "application/vnd.ms-excel": "xls",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": "xlsx",
        "application/vnd.oasis.opendocument.spreadsheet": "ods",
        "text/csv": "csv"
    }
    extension = lookup.get(content_type)
    if extension is None:
        raise NotImplementedError(f"scraper - unsupported spreadsheet content type: {content_type} (how did we get here?)")
    with NamedTemporaryFile(suffix=f".{extension}") as tmpfile:        
        tmpfile.write(content)
        tmpfile.flush()
        tmpfile.seek(0)
        book_dict = pyexcel.get_book_dict(file_name=tmpfile.name)
        markdown = "*A table was found. Here is the content of the table in markdown format:*\n\n"
        for sheet_name, sheet_contents in book_dict.items():
            # sheet contents: list of lists. [0] is row 1, [0][0] is cell A1
            markdown += f"## {sheet_name}\n\n"
            # now we get to generate a table by hand. fun.
            if len(sheet_contents) == 0:
                markdown += "*This sheet is empty.*\n\n"
                continue
            # alright, we can't really assume there's a formal header row.
            # we're... just going to not worry about it! it cant harm us
            # if we don't think about it.
            for row in sheet_contents:
                markdown += "| " + " | ".join(str(cell) for cell in row) + " |\n"
            markdown += "\n\n"
        return markdown

def extract_docx(content: bytes) -> str:
    with BytesIO(content) as tmpfile, StringIO() as output:
        doc = docx.Document(tmpfile)
        for paragraph in doc.paragraphs:
            for run in paragraph.runs:
                # we're gonna try to keep the formatting here!
                # might be useful?
                # TODO: consider more formatting options!
                # namely: lists.
                wrapping = ""
                if run.bold or (paragraph.style and paragraph.style.font.bold):
                    wrapping += "**"
                if run.italic or (paragraph.style and paragraph.style.font.italic):
                    wrapping += "*"
                if run.underline or (paragraph.style and paragraph.style.font.underline):
                    wrapping += "__"
                output.write(f"{wrapping}{run.text}{wrapping}")
            output.write("\n\n")
        return output.getvalue()

if __name__ == "__main__":
    from sys import argv
    print(get_page(argv[1]))
