import os
import json
import time
import urllib
import argparse

import tqdm

from scrapy import Spider
from PyPDF3 import PdfFileMerger
from urllib.request import urlretrieve


def download_file(download_url, file_name):
    response = urllib.request.urlopen(download_url)
    file = open(file_name, 'wb')
    file.write(response.read())
    file.close()


def pdf_downloader(file_path, url, sup_url):
    _file_path = file_path.replace(':', '-')
    _file_path = _file_path.replace('?', '-')
    _file_path = _file_path.replace('!', '-')
    file_path = _file_path + '.pdf'
    file_path_bak = _file_path + '_bak.pdf'

    try:
        urlretrieve(url, file_path_bak)
    except Exception as e:
        print(url, file_path_bak)

    time.sleep(0.5)
    if len(sup_url) != 0:
        sup_file_path = _file_path + '_sup.pdf'
        
        try:
            urlretrieve(sup_url, sup_file_path)
        except Exception as e:
            print(sup_url, sup_file_path)


def merge_pdfs(file_path, sup_url):
    _file_path = file_path.replace(':', '-')
    _file_path = _file_path.replace('?', '-')
    _file_path = _file_path.replace('!', '-')
    _file_path = _file_path.replace('$', '')
    _file_path = _file_path.replace("\'", '')
    file_path = _file_path + '.pdf'
    file_path_bak = _file_path + '_bak' + '.pdf'
    sup_file_path = _file_path + '_sup.pdf'
    if len(sup_url) != 0:
        merger = PdfFileMerger()
        merger.append(file_path_bak)
        merger.append(sup_file_path)
        with open(file_path, 'wb') as fout:
            merger.write(fout)
        
        merger.close()
        os.remove(file_path_bak)
        os.remove(sup_file_path)
    else:
        os.rename(file_path_bak, file_path)


def check(keywords, file_name):
    file_name = file_name.lower()
    if len(keywords) == 0:
        return True  # download all papers
    
    for key in keywords:
        if key in file_name:
            return True
    return False


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Crawl paper')
    parser.add_argument('--RL', action="store_true", default=False, help='download RL papers')
    parser.add_argument("--data-dir", type=str, default="icml2019", help="data dir")
    parser = parser.parse_args()

    if not os.path.exists(parser.data_dir):
        os.makedirs(parser.data_dir)
    if not os.path.exists(os.path.join(parser.data_dir, 'RL')):
        os.makedirs(os.path.join(parser.data_dir, 'RL'))

    with open("..\\items.json") as json_file:  
        data = json.load(json_file)

    key_words = [
            'reinforcement learning', 'policy', 'multi-agent', 'multiagent', 'off-policy', 'on-policy', 'mdp', 'exploration', 'bellman',
             'dqn', 'optimization', 'meta-learning', 'meta-reinforcement' 'multi-task', 'Representation', 'model-based', 'model-free']

    for item in tqdm.tqdm(data):
        title = item['title']
        pdf_url = item['pdf']
        sup_url = item['sup']
        pdf_url if not pdf_url.startswith('ttp') else 'h' + pdf_url
        sup_url if not sup_url.startswith('ttp') else 'h' + sup_url
        if check(key_words, title) and parser.RL:
            pdf_downloader(os.path.join(os.path.join(parser.data_dir, 'RL'), '19-'+title), pdf_url, sup_url)
        else:
            pdf_downloader(os.path.join(parser.data_dir, '19-'+title), pdf_url, sup_url)

    # merge files
    for item in tqdm.tqdm(data):
        title = item['title']
        pdf_url = item['pdf']
        sup_url = item['sup']
        pdf_url if not pdf_url.startswith('ttp') else 'h' + pdf_url
        sup_url if not sup_url.startswith('ttp') else 'h' + sup_url
        if check(key_words, title) and parser.RL:
            merge_pdfs(os.path.join(os.path.join(parser.data_dir, 'RL'), '19-'+title), sup_url)
        else:
            merge_pdfs(os.path.join(parser.data_dir, '19-'+title), sup_url)
