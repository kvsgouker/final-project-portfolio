"""
Overview:

This module, `download.py`, is used to handle the downloading of data files from the web.
It includes functions that ensure each file is downloaded fresh every time and implements
retry logic for handling failed requests.

Functions:

1. fetch_url_with_retry():
   - Fetches a URL with retry logic in case of failure or rate limiting.
   - Parameters:
     - url (str): The URL to fetch.
     - raw (bool): If True, appends `?raw=true` to the URL for GitHub raw content.
   - Returns:
     - response (Response or None): The response object if successful; otherwise, None.
   - Logic:
     - Retries up to `max_retries` times.
     - Implements exponential backoff (`retry_delay` doubles after each failed attempt).
     - Prints status messages for failed attempts and rate-limiting responses (HTTP 429).

2. download_file():
   - Downloads a text file from a given URL and saves it with the specified filename.
   - Parameters:
     - url (str): The URL to download the file from.
     - output_filename (str): The path to save the downloaded file.
     - raw (bool): If True, fetches raw content.
     - encoding (str): The encoding to use when writing the file. Defaults to 'utf-8'.
   - Logic:
     - Checks if the file already exists. If it does, a message is printed and the function returns.
     - Fetches the URL and writes the content to the specified file if successful.
     - Prints a confirmation message when writing the file.

3. download_binary_file():
   - Downloads a binary file (e.g., images, PDFs) from a given URL and saves it with the specified filename.
   - Parameters:
     - url (str): The URL to download the file from.
     - output_filename (str): The path to save the downloaded file.
     - raw (bool): If True, fetches raw content.
   - Logic:
     - Checks if the file already exists. If it does, a message is printed and the function returns.
     - Fetches the URL and writes the binary content to the specified file if successful.
     - Prints a confirmation message when writing the file.
     - Prints an error message if the download fails.

Usage:
- Use `download_file()` to download text files, such as CSVs or HTML pages.
- Use `download_binary_file()` for binary files like images, PDFs, or executable files.
- Both functions check for file existence to avoid redundant downloads and notify users with printed messages.

Dependencies:
- `os`: Used for file existence checks.
- `time`: Implements retry delay for exponential backoff.
- `requests`: Handles HTTP requests to fetch data from URLs.

Retry Logic:
- Retries up to 3 times for failed or rate-limited requests.
- Uses exponential backoff to increase delay between retries (2, 4, 8 seconds).

Notes:
- `fetch_url_with_retry()` appends `?raw=true` when `raw=True`, useful for GitHub raw content.
- HTTP response status codes are logged for easy debugging.
"""

# File system searches, etc.
import os

# time is important in this universe
import time

import requests


def fetch_url_with_retry(url, raw=False):
    max_retries = 3
    retry_delay = 2  # seconds

    # Add GitHub-specific header only if URL is from GitHub
    headers = {}
    if raw:
        url = url + "?raw=true"
    for retry_count in range(max_retries):
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response
        elif response.status_code == 429:
            print("Too many requests. Waiting and retrying...")
            time.sleep(retry_delay)
            retry_delay *= 2  # Exponential backoff
        else:
            print(f"Failed to fetch URL: {url}. Status code: {response.status_code}")

    return None


def download_file(url, output_filename, raw=False, encoding='utf-8'):
    # Check if file already exists
    if not os.path.exists(output_filename):
        response = fetch_url_with_retry(url, raw)
        if response:
            with open(output_filename, "w", encoding=encoding) as output_file:
                print("writing " + output_filename)
                output_file.write(response.text)
    else:
        print(f"Already downloaded {output_filename}")


def download_binary_file(url, output_filename, raw=False):
    # Check if file already exists
    if not os.path.exists(output_filename):
        response = fetch_url_with_retry(url, raw)
        if response and response.status_code == 200:
            with open(output_filename, "wb") as output_file:
                print("writing " + output_filename)
                output_file.write(response.content)
        else:
            print(f"Failed to download {url}: Status code {response.status_code}")
    else:
        print(f"Already downloaded {output_filename}")
