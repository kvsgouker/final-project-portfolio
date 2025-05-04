"""
web_utils.py

A polite, modular web downloader with retry, backoff, rotating user agents,
and support for Google Drive and GitHub raw content. Safe for use in research-grade
scraping and analysis.

Author: Kyle Salgado-Gouker

"""

import os
import time
from urllib.request import urlretrieve

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

try:
    from fake_useragent import UserAgent
    ua = UserAgent()
except ImportError:
    ua = None

FALLBACK_UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36'

# --- User Agent ---
def get_user_agent_headers():
    if ua:
        return {'User-Agent': ua.random}
    return {'User-Agent': FALLBACK_UA}

# --- Retry Logic ---
def fetch_url_with_retry(url, retries=10, backoff_factor=0.3):
    session = requests.Session()
    retry_strategy = Retry(
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=backoff_factor,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["HEAD", "GET", "OPTIONS"]
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount('http://', adapter)
    session.mount('https://', adapter)

    try:
        response = session.get(url, headers=get_user_agent_headers())
        response.raise_for_status()
        return response
    except requests.exceptions.HTTPError as he:
        if response.status_code == 429:
            retry_after = int(response.headers.get("Retry-After", 10))
            print(f"Rate limit exceeded. Retrying in {retry_after} seconds...")
            time.sleep(retry_after * 2)
            return fetch_url_with_retry(url, retries - 1, backoff_factor)
        print(f"HTTP error occurred: {he}")
    except requests.exceptions.RequestException as re:
        print(f"Request failed for {url}: {re}")
    return None


# --- Save Response ---
def save_response_to_file(response, filename):
    if hasattr(response, 'headers'):
        # It's a full HTTP response object
        if 'text' in response.headers.get('Content-Type', ''):
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(response.text)
        else:
            with open(filename, 'wb') as f:
                f.write(response.content)
    else:
        # Raw content bytes already
        with open(filename, 'wb') as f:
            f.write(response)

    print(f"Saved: {filename}")


# --- Public Download ---
def download_file(url, filename, force=False):
    if not os.path.exists(filename) or force:
        print(f"Downloading from {url} → {filename}")
        response = fetch_url_with_retry(url)
        if response:
            save_response_to_file(response, filename)
    else:
        print(f"Already exists: {filename}")


# --- GitHub Raw Content ---
def download_raw_file(github_url, filename):
    if not os.path.exists(filename):
        raw_url = github_url + "?raw=true"
        download_file(raw_url, filename)

# --- Google Drive Utilities ---
def get_google_drive_download_link(share_link_url):
    file_id = share_link_url.split("/d/")[1].split("/")[0]
    return f"https://drive.google.com/uc?id={file_id}&export=download"

def download_google_drive_file(share_link_url, filename):
    direct_url = get_google_drive_download_link(share_link_url)
    download_file(direct_url, filename)

# --- Simple Fallback for URLs like images or zips ---
def download_urlretrieve(url, filename):
    if not os.path.exists(filename):
        local, _ = urlretrieve(url, filename)
        print(f"Downloaded using urlretrieve: {local}")
        return local
    print(f"Already exists: {filename}")
    return filename
