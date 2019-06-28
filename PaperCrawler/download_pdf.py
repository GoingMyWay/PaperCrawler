import os
import json
import time
import urllib
import requests
import argparse
import traceback
import threading

import tqdm

from scrapy import Spider
from pdfrw import PdfReader, PdfWriter
from urllib.request import urlretrieve


# For downloading files from Google Drive
def download_file_from_google_drive(id, save_path):
    """
    Downloading files from Google Drive is not such straightforward, for example:
        https://drive.google.com/file/d/1I05c4-d9OsNwGZnLx85fR8dnX-yVoTWe/view
    You cannot download it but read it, this links contains id=1I05c4-d9OsNwGZnLx85fR8dnX-yVoTWe,
    you can use this id to download it.

    >>> download_file_from_google_drive(id='1I05c4-d9OsNwGZnLx85fR8dnX-yVoTWe', save_path='demo.pdf')
    """

    URL = "https://docs.google.com/uc?export=download"

    session = requests.Session()

    response = session.get(URL, params = { 'id' : id }, stream = True)
    token = _get_confirm_token(response)

    if token:
        params = { 'id' : id, 'confirm' : token }
        response = session.get(URL, params = params, stream = True)

    _save_response_content(response, save_path)    

def _get_confirm_token(response):
    for key, value in response.cookies.items():
        if key.startswith('download_warning'):
            return value

    return None

def _save_response_content(response, save_path):
    CHUNK_SIZE = 32768

    with open(save_path, "wb") as f:
        for chunk in response.iter_content(CHUNK_SIZE):
            if chunk: # filter out keep-alive new chunks
                f.write(chunk)


# For normal download
def preprocess_title(title):
    title = title.replace(':', '-')
    title = title.replace('?', '-')
    title = title.replace('!', '-')
    title = title.replace("$", "")  # latex
    title = title.replace("\'", "")
    title = title.replace("/", "")
    return title


def urlretrieve_v2(url, filename):
    """
    For stable download.
    """
    try:
        urlretrieve(url,filename)
    except urllib.error.ContentTooShortError:
        print('[INFO] Network is not good, re-download it')
        urlretrieve_v2(url, filename)


def download_file(download_url, file_name):
    response = urllib.request.urlopen(download_url)
    file = open(file_name, 'wb')
    file.write(response.read())
    file.close()


def pdf_downloader(file_path, url, sup_url):
    _file_path = file_path
    file_path = _file_path + '.pdf'
    file_path_bak = _file_path + '_bak.pdf'

    try:
        if not os.path.exists(file_path_bak) and not os.path.exists(file_path):
            urlretrieve_v2(url, file_path_bak)
            time.sleep(0.3)
    except Exception as e:
        print('ERROR', url, file_path_bak)
        traceback.print_exc()
    
    if len(sup_url) != 0:
        sup_file_path = _file_path + '_sup.pdf'
        try:
            if not os.path.exists(sup_file_path) and not os.path.exists(file_path):
                urlretrieve_v2(sup_url, sup_file_path)
                time.sleep(0.3)
        except Exception as e:
            print(sup_url, sup_file_path)
            traceback.print_exc()


# For merging PDF files
def merge_pdfs(file_path, sup_url):
    _file_path = file_path
    file_path = _file_path + '.pdf'
    file_path_bak = _file_path + '_bak.pdf'
    if len(sup_url) != 0 and not os.path.exists(file_path):
        sup_file_path = _file_path + '_sup.pdf'

        writer = PdfWriter()
        for inpfn in [file_path_bak, sup_file_path]:
            try:
                writer.addpages(PdfReader(inpfn).pages)
            except Exception:
                print(inpfn)
                traceback.print_exc()
                exit(-1)

        writer.write(file_path)
        os.remove(file_path_bak)
        os.remove(sup_file_path)
    else:
        if os.path.exists(file_path_bak):
            os.rename(file_path_bak, file_path)


def check(keywords, file_name):
    file_name = file_name.lower()
    if len(keywords) == 0:
        return True  # download all papers
    
    for key in keywords:
        if key in file_name:
            return True
    return False


def thread_worker(items):
    for title, pdf_url, sup_url in tqdm.tqdm(items):
        pdf_downloader(os.path.join(os.path.join(parser.data_dir, 'RL'), YEAR+'-'+preprocess_title(title)), pdf_url, sup_url)


if __name__ == '__main__':
    YEAR = '18'

    parser = argparse.ArgumentParser(description='Crawl paper')
    parser.add_argument('--RL', action="store_true", default=False, help='download RL papers')
    parser.add_argument("--data-dir", type=str, default="icml20%s" %  YEAR, help="data dir")
    parser = parser.parse_args()

    if not os.path.exists(parser.data_dir):
        os.makedirs(parser.data_dir)
    if not os.path.exists(os.path.join(parser.data_dir, 'RL')):
        os.makedirs(os.path.join(parser.data_dir, 'RL'))

    with open(os.path.join(os.path.abspath('..'), 'items_icml%s.json' % YEAR)) as json_file:  
        data = json.load(json_file)

    rl_key_words = [
            'reinforcement learning', 'policy', 'multi-agent', 'multiagent', 'off-policy', 'on-policy', 'mdp', 'exploration', 'bellman',
             'dqn', 'meta-learning', 'meta-reinforcement' 'multi-task', 'multi-goal', 'model-based', 'model-free']

    threads = []  # 4 threads
    items = []
    if len(rl_key_words) != 0 and parser.RL:
        for item in data:
            title = item['title']
            pdf_url = item['pdf']
            sup_url = item['sup']
            if check(rl_key_words, title):
                items.append((title, pdf_url, sup_url))
        thread_num = 4
        _step = int(len(items)/thread_num)
        _offset = len(items) % thread_num
        for i in range(thread_num):
            _j = _offset if i+1 == thread_num else 0
            threads.append(threading.Thread(target=thread_worker, args=(items[i*_step:(i+1)*_step+_j], )))
        
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        print("Download finished, Now merge them!", len(items))
    else:
        for item in tqdm.tqdm(data):
            title, pdf_url, sup_url = item['title'], item['pdf'], item['sup']
            pdf_downloader(os.path.join(parser.data_dir, YEAR+'-'+preprocess_title(title)), pdf_url, sup_url)

    # merge files
    if len(rl_key_words) != 0 and parser.RL:
        for title, pdf_url, sup_url in tqdm.tqdm(items):
            merge_pdfs(os.path.join(os.path.join(parser.data_dir, 'RL'), YEAR+'-'+preprocess_title(title)), sup_url)
    else:
        for item in tqdm.tqdm(data):
            title = item['title']
            pdf_url = item['pdf']
            sup_url = item['sup']
            merge_pdfs(os.path.join(parser.data_dir, YEAR+'-'+preprocess_title(title)), sup_url)
