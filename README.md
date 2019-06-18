# PaperCrawler


1. Crawl the data in the root of directory

```
scrapy crawl PaperCrawler -o items.json -t json
```

2. Download paper

```
python download_pdf.py --RL # download RL papers
```

3. You can change the code in `crawler.py` to crawl other academic conferences or journals.