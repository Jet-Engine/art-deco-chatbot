import magic
import os
import yaml
from bs4 import BeautifulSoup
from nltk import sent_tokenize
from typing import List  # Add this import


def get_config(config_path="config.template.yaml", secrets_path="secrets.yaml"):
    with open(config_path, "r") as config_file:
        config = yaml.safe_load(config_file)

    if os.path.exists(secrets_path):
        with open(secrets_path, "r") as secrets_file:
            secrets = yaml.safe_load(secrets_file)
        config.update(secrets)

    return config


def read_questions(file_path):
    with open(file_path, 'r') as file:
        questions = [line.strip() for line in file if line.strip()]
    return questions


def read_text(path):
    path = path.rstrip()
    path = path.replace(' \n', '')
    path = path.replace('%0A', '')
    relative_path = path
    filename = os.path.abspath(relative_path)

    filetype = magic.from_file(filename, mime=True)

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


def chunk_text_by_sentences(source_text: str, sentences_per_chunk: int, overlap: int, language="english") -> List[str]:
    """
    Splits text by sentences
    """
    if sentences_per_chunk < 2:
        raise ValueError(
            "The number of sentences per chunk must be 2 or more.")
    if overlap < 0 or overlap >= sentences_per_chunk - 1:
        raise ValueError(
            "Overlap must be 0 or more and less than the number of sentences per chunk.")

    sentences = sent_tokenize(source_text, language=language)
    if not sentences:
        print("Nothing to chunk")
        return []

    chunks = []
    i = 0
    print(len(sentences))
    while i < len(sentences):
        end = min(i + sentences_per_chunk, len(sentences))
        chunk = ' '.join(sentences[i:end])

        if overlap > 0 and i > 1:
            overlap_start = max(0, i - overlap)
            overlap_end = i
            overlap_chunk = ' '.join(sentences[overlap_start:overlap_end])
            chunk = overlap_chunk + ' ' + chunk

        chunks.append(chunk.strip())
        i += sentences_per_chunk

    return chunks
