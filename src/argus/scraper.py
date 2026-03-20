import requests
import trafilatura
from trafilatura.readability_lxml import is_probably_readerable
from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth

def get_page(url: str) -> str:
    try:
        resp = requests.get(url)
        content_type = resp.headers.get("Content-Type", "").lower().split(";")[0].strip()

        if content_type not in ("text/html", "application/xhtml+xml"):
            # okay, this isn't an html page? let's try to figure out if it's a pdf or something else we can handle
            match content_type:
                case "application/pdf":
                    # return extract_pdf(resp.content)
                    pass
                case "application/msword" | "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                    pass # TODO: handle word docs
                case "application/vnd.ms-excel" | "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet":
                    pass # TODO: handle excel sheets
                case "application/vnd.ms-powerpoint" | "application/vnd.openxmlformats-officedocument.presentationml.presentation":
                    pass # TODO: handle powerpoint presentations
                case "application/vnd.oasis.opendocument.text":
                    pass # TODO: handle open document text
                case "application/vnd.oasis.opendocument.spreadsheet":
                    pass # TODO: handle open document spreadsheet
                case "application/vnd.oasis.opendocument.presentation":
                    pass # TODO: handle open document presentation
                case "text/plain" | "text/markdown":
                    return resp.text # fair enough
                case "text/rtf":
                    pass # TODO: handle rtf
                case "application/json":
                    return resp.text # sure, why not
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
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url)
        html = page.content()
        browser.close()

    if not is_probably_readerable(html):
        raise NotImplementedError("scraper - page isn't readerable (even with fallback).")
    
    markdown = trafilatura.extract(html, output_format='markdown')
    return markdown

if __name__ == "__main__":
    from sys import argv
    print(get_page(argv[1]))
