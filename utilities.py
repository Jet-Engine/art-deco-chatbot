import re, os, requests, magic
from urllib.parse import unquote, urlparse
from bs4 import BeautifulSoup

import yaml


def get_config(path="config.yaml"):
    with open(path, "r") as file:
        config = yaml.safe_load(file)
    return config


def read_questions(file_path):
    with open(file_path, 'r') as file:
        questions = [line.strip() for line in file if line.strip()]
    return questions


def read_text(path):
    path = path.rstrip()
    path = path.replace(' \n', '')
    path = path.replace('%0A', '')
    if re.match(r'^https?://', path):
        filename = download_file(path)
    else:

        relative_path = path
        filename = os.path.abspath(relative_path)

    filetype = magic.from_file(filename, mime=True)
    print(f"\nEmbedding {filename} as {filetype}")
    text = ""
    if filetype == 'application/pdf':
        print('PDF not supported yet')
    if filetype == 'text/plain':
        with open(filename, 'rb') as f:
            text = f.read().decode('utf-8')
    if filetype == 'text/html':
        with open(filename, 'rb') as f:
            soup = BeautifulSoup(f, 'html.parser')
            text = soup.get_text()

    if os.path.exists(filename) and filename.find('content/') > -1:
        os.remove(filename)

    return text


def download_file(url):
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        filename = get_filename_from_cd(r.headers.get('content-disposition'))
        if not filename:
            filename = urlparse(url).geturl().replace('https://', '').replace('/', '-')
        filename = 'content/' + filename
        with open(filename, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
        return filename


def get_filename_from_cd(cd):
    """
    Get filename from content-disposition
    """
    if not cd:
        return None
    file_name = cd.split('filename=')[1]
    if file_name.lower().startswith(("utf-8''", "utf-8'")):
        file_name = file_name.split("'")[-1]
    return unquote(file_name)
