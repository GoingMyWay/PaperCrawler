import os
import json
import time
import urllib
import argparse
import traceback

import tqdm

from scrapy import Spider
from pdfrw import PdfReader, PdfWriter
from urllib.request import urlretrieve


def download_file(download_url, file_name):
    response = urllib.request.urlopen(download_url)
    file = open(file_name, 'wb')
    file.write(response.read())
    file.close()


def pdf_downloader(file_path, url, sup_url):

    url = url if not url.startswith('ttp') else 'h' + url
    sup_url = sup_url if not sup_url.startswith('ttp') else 'h' + sup_url

    _file_path = file_path.replace(':', '-')
    _file_path = _file_path.replace('?', '-')
    _file_path = _file_path.replace('!', '-')
    _file_path = _file_path.replace("$", "")
    _file_path = _file_path.replace("\'", "")
    file_path = _file_path + '.pdf'
    file_path_bak = _file_path + '_bak.pdf'

    try:
        if not os.path.exists(file_path_bak):
            urlretrieve(url, file_path_bak)
            time.sleep(0.3)
    except Exception as e:
        print('ERROR', url, file_path_bak)
        traceback.print_exc()
    
    time.sleep(0.5)
    if len(sup_url) != 0:
        sup_file_path = _file_path + '_sup.pdf'
        try:
            if not os.path.exists(sup_file_path):
                urlretrieve(sup_url, sup_file_path)
                time.sleep(0.3)
        except Exception as e:
            print(sup_url, sup_file_path)
            traceback.print_exc()


def merge_pdfs(file_path, sup_url):
    sup_url = sup_url if not sup_url.startswith('ttp') else 'h' + sup_url

    _file_path = file_path.replace(':', '-')
    _file_path = _file_path.replace('?', '-')
    _file_path = _file_path.replace('!', '-')
    _file_path = _file_path.replace('$', '')
    _file_path = _file_path.replace("\'", '')
    file_path = _file_path + '.pdf'
    file_path_bak = _file_path + '_bak.pdf'
    if len(sup_url) != 0:
        sup_file_path = _file_path + '_sup.pdf'
        writer = PdfWriter()
        for inpfn in [file_path_bak, sup_file_path]:
            writer.addpages(PdfReader(inpfn).pages)
        
        writer.write(file_path)
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

    with open(os.path.join(os.path.abspath('..'), 'items.json')) as json_file:  
        data = json.load(json_file)

    rl_key_words = [
            'reinforcement learning', 'policy', 'multi-agent', 'multiagent', 'off-policy', 'on-policy', 'mdp', 'exploration', 'bellman',
             'dqn', 'meta-learning', 'meta-reinforcement' 'multi-task', 'representation', 'model-based', 'model-free']

    items = []
    if len(rl_key_words) != 0 and parser.RL:
        for item in data:
            title = item['title']
            pdf_url = item['pdf']
            sup_url = item['sup']
            if check(rl_key_words, title):
                items.append((title, pdf_url, sup_url))
    
        for title, pdf_url, sup_url in tqdm.tqdm(items):
            pdf_downloader(os.path.join(os.path.join(parser.data_dir, 'RL'), '19-'+title), pdf_url, sup_url)
    else:
        for item in tqdm.tqdm(data):
            title, pdf_url, sup_url = item['title'], item['pdf'], item['sup']
            pdf_downloader(os.path.join(parser.data_dir, '19-'+title), pdf_url, sup_url)

    # merge files
    if len(rl_key_words) != 0 and parser.RL:
        for title, pdf_url, sup_url in tqdm.tqdm(items):
            merge_pdfs(os.path.join(os.path.join(parser.data_dir, 'RL'), '19-'+title), sup_url)
    else:
        for item in tqdm.tqdm(data):
            title = item['title']
            pdf_url = item['pdf']
            sup_url = item['sup']
            merge_pdfs(os.path.join(parser.data_dir, '19-'+title), sup_url)
