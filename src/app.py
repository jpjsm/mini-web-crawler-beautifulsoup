from pathlib import Path
import re
from urllib.parse import urljoin
import time

import requests
from bs4 import BeautifulSoup

not_valid_char_in_filename = set([chr(i) for i in range(1,32)])
for c in ['/', '\\', ':', '&', '^', '"', "'", '$', '*']:
    not_valid_char_in_filename.add(c)

visited = set()
pending = set()

def get_title(soup:BeautifulSoup) -> str | None:
    title = soup.find('title')
    if title:
        title = text_cleanup(title.string)

    return title        

def text_cleanup(txt: str) -> str:
    for c in not_valid_char_in_filename:
        txt.replace(c, ' ')
    txt = txt.strip()
    while txt.find('  ') != -1:
        txt = txt.replace('  ', ' ')
    
    return txt

def render_text(soup:BeautifulSoup, filename:str="", output_folder:str='.'):
    for script_or_style in soup(["script", "style"]):
        script_or_style.decompose()  # Remove these elements

    text = soup.get_text()  # Get the text content

    # Clean up the text
    lines = (line.strip() for line in text.splitlines())
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    clean_text = "\n".join(chunk for chunk in chunks if chunk)

    if not filename:
        filename = get_title(soup)
        if filename:
            while filename[-1] not in 

    # Save the text to a file
    txtfile = Path(output_folder).joinpath(f"{filename}.txt")
    with open(txtfile, "w", encoding="utf-8") as file:
        file.write(clean_text)

    print(f"  ->  Text successfully saved to '{filename}.txt'")

def crawl(current_url, output_folder='.'):
    if current_url in visited:
        return
    
    visited.add(current_url)
    
    try:
        response = requests.get(current_url)
        response.raise_for_status()  # Check for HTTP request errors
        soup = BeautifulSoup(response.text, 'html.parser')

        # determine base_url
        base_tag = soup.find('base', href=True) 
        base_url = base_tag['href'] if base_tag else None
        if not base_url:
            base_url = response.url

        if not base_url or not base_url.startswith('http'):
            print(f"WARNING: BASE url '{base_url}' ill-defined.")
            
        print(f"Visiting: {current_url}")
        render_text(soup, output_folder)
        
        # Find all links on the page
        for link in soup.find_all('a', href=True):
            href = link['href']
            full_href = urljoin(base_url, href)
            if full_href in visited:
                continue

            pending.add(full_href)

        print(f"  -> Found {len(pending)} urls in {current_url}")

    except Exception as e:
        print(f"Failed to crawl {current_url}: {e}")





# Example usage
start_url = "https://app.leg.wa.gov/rcw/"
crawl(start_url, output_folder='docs')
while pending:
    time.sleep(3)
    next_url = pending.pop()
    crawl(next_url, output_folder='docs')