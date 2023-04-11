from url_normalize import url_normalize
from urllib.parse import urljoin, urldefrag, urlparse
from playwright.sync_api import sync_playwright, Page

from utils import is_absolute

pageTree = {};
pagesToVisit = [];
pagesVisited = [];
externalPages = [];
mediaLinks = [];
errorLinks = [];

def crawl_page(p: Page, pageId: int, url: str):
    page.goto(url)

    # wait for page 
    page.wait_for_load_state("networkidle")

    # Create a filename for the page, replace all characters that are not allowed in a filename with a dash
    filename = url.replace("/", "-").replace(":", "-").replace("?", "-").replace("&", "-").replace("=", "-").replace(".", "-")
    
    # Save the entire page as a PDF
    page.pdf(path=f"output/{filename}.pdf", print_background=True)
    
    # Gather all links on the page
    pageLinks = [];
    links = page.query_selector_all("a")
    for link in links:
        href = link.get_attribute("href")

         # if the href is empty, skip it
        if href == "" or href == None:
            continue
        
        pageLinks.append(href)
            
    return page.url, pageLinks


with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()  
    pagesToVisit.append("https://www.hennepin.us/")
    # While there are pages to visit
    while pagesToVisit:
        # Visit the next page
        url = pagesToVisit.pop()
        url = urldefrag(url)[0]

        if (is_absolute(url) == False):
            url = urljoin("https://www.hennepin.us/", url)

        parsedUrl = urlparse(url)
        if parsedUrl.scheme != "http" and parsedUrl.scheme != "https":
            externalPages.append(url)
            continue

        if (parsedUrl.netloc != "www.hennepin.us" and parsedUrl.netloc != "hennepin.us"):
            externalPages.append(url)
            continue

        url = url_normalize(url)

        # If the url is not in hennepin.us, add it to the external pages list
        if url.find("hennepin.us") == -1:
            externalPages.append(url)
            continue

        # if the url contains /-/media/, add it to the media links list
        if url.find("/-/media/") != -1:
            mediaLinks.append(url)
            continue
        
        if url not in pagesVisited:
            # Crawl the page
            print(f"Visiting {url}... ({len(pagesVisited)}/{len(pagesToVisit)})")
            try:
                finalPageUrl, newLinks = crawl_page(page, len(pagesVisited), url)
                # Add the new pages to visit
                for link in newLinks:
                    # populate the page tree
                    if finalPageUrl not in pageTree:
                        pageTree[finalPageUrl] = []
                    
                    pageTree[finalPageUrl].append(link)

                    if link not in pagesToVisit and link not in pagesVisited:
                        pagesToVisit.append(link)
                
                pagesVisited.append(url)

                if url != finalPageUrl:
                    pagesVisited.append(finalPageUrl)
            except Exception as e:
                print("Error visiting " + url)
                errorLinks.append(url)

        else:
            print("Already visited " + url)
    # Close the browser
    browser.close()

    # Write the external pages to a file
    with open("output/external-pages.csv", "w") as f:
        for page in externalPages:
            f.write(page + ",\r\n")
    
    # Write the pages visited to a file
    with open("output/pages-visited.csv", "w") as f:
        for page in pagesVisited:
            f.write(page + ",\r\n")
    # Write the media links to a file
    with open("output/media-links.csv", "w") as f:
        for page in mediaLinks:
            f.write(page + ",\r\n")

    # Write the error links to a file
    with open("output/error-links.csv", "w") as f:
        for page in errorLinks:
            f.write(page + ",\r\n")

    # Write the page tree to a file
    with open("output/page-tree.csv", "w") as f:
        for page in pageTree:
            for link in pageTree[page]:
                f.write(page + "," + link + ",\r\n")

