from pathlib import Path
import re
from typing import List
from urllib.parse import urljoin
import time

import requests
from bs4 import BeautifulSoup

not_valid_char_in_filename = set([chr(i) for i in range(1,32)])
for c in ['/', '\\', ':', '&', '^', '"', "'", '$', '*']:
    not_valid_char_in_filename.add(c)

visited = set()
in_process = set()
pending = set()

def download_pdf(url, save_path):
    """
    Downloads a PDF file from a given URL and saves it to a specified path.

    Args:
        url (str): The URL of the PDF file.
        save_path (str): The local path where the PDF will be saved, including the filename.
    """
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)

        with open(save_path, 'wb') as pdf_file:
            for chunk in response.iter_content(chunk_size=8192):
                pdf_file.write(chunk)
        print(f"PDF downloaded successfully to: {save_path}")

    except requests.exceptions.RequestException as e:
        print(f"Error downloading PDF: {e}")
    except IOError as e:
        print(f"Error saving PDF file: {e}")

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
            while filename[-1] in not_valid_char_in_filename:
                filename = filename[:-1]

    # Save the text to a file
    filepath = Path(output_folder).joinpath(f"{filename}.txt")
    with open(filepath, "w", encoding="utf-8") as file:
        file.write(clean_text)

    print(f"  ->  Text successfully saved to '{filename}.txt'")

def crawl(current_url:str, save_text:bool=False, output_folder:str='.') -> List[str]:
    if current_url in visited or current_url in in_process:
        return
    
    in_process.add(current_url)
    
    try:
        response = requests.get(current_url)
        response.raise_for_status()  # Check for HTTP request errors
        soup = BeautifulSoup(response.text, 'html.parser')

        if save_text:
            render_text(soup, output_folder=output_folder)

        # determine base_url
        base_tag = soup.find('base', href=True) 
        base_url = base_tag['href'] if base_tag else None
        if not base_url:
            base_url = response.url

        if not base_url or not base_url.startswith('http'):
            print(f"WARNING: BASE url '{base_url}' ill-defined for current '{current_url}'.")
            
        print(f"Visiting: {current_url}")
        
        # Find all links on the page
        links_found = set()
        for link in soup.find_all('a', href=True):
            href = link['href']

            if href.startswith('http'):
                links_found.add(href)

            else:
                full_href = urljoin(base_url, href)
                links_found.add(full_href)

        print(f"  -> Found {len(links_found)} urls in {current_url}")

        in_process.remove(current_url)
        visited.add(current_url)
        return list(links_found)

    except Exception as e:
        print(f"Failed to crawl {current_url}: {e}")

def crawler(focus_pattern:str, download_pdfs:bool=False, download_pattern:str="pdf$", download_folder:str=".") -> None:
    while pending:
        next_url:str = pending.pop()
        if download_pdfs:
            match = re.search(download_pattern, next_url, re.IGNORECASE)
            if match:
                download_pdf(next_url, "")
        urls = crawl(next_url)




# Example usage
start_url = "https://app.leg.wa.gov/rcw/"
focus_pattern = '^https://app.leg.wa.gov/rcw/default.aspx'
download_pattern = '^https://app\\.leg\\.wa.gov/rcw/default.aspx'
# https://app.leg.wa.gov/RCW/default.aspx?cite=74.13B&full=true&pdf=true
# crawl(start_url, output_folder='docs')
# while pending:
#     time.sleep(3)
#     next_url = pending.pop()
#     crawl(next_url, output_folder='docs')

download_pdf("https://app.leg.wa.gov/RCW/default.aspx?cite=74.13B&full=true&pdf=true", 'rcw_74-13B.pdf')