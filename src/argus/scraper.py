import requests
import trafilatura
from trafilatura.readability_lxml import is_probably_readerable
from playwright.sync_api import sync_playwright

def get_page(url: str) -> str:
    resp = requests.get(url)

    if not is_probably_readerable(resp.text):
         return get_page_chrome(url)

    markdown = trafilatura.extract(resp.text, output_format='markdown')
    return markdown
    

def get_page_chrome(url: str) -> str:
    with sync_playwright() as p:
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
