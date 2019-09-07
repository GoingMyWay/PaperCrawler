from scrapy import Spider
from scrapy.selector import Selector
from PaperCrawler.items import PapercrawlerItem


class PaperCrawler(Spider):
    name = "PaperCrawler"
    allowed_domains = ["proceedings.mlr.press"]
    start_urls = ["http://proceedings.mlr.press/v80/", ]

    def parse(self, response):
        papers = Selector(response).xpath('//*[@id="content"]/div/div[@class="paper"]')

        for paper in papers:
            item = PapercrawlerItem()
            item['title'] = paper.xpath('p[1]/text()').extract()[0]
            _pdf_link = paper.xpath('p[3]/a[2]/@href').extract()[0]
            item['pdf'] = _pdf_link if not _pdf_link.startswith('ttp') else 'h' + _pdf_link
            _sup_data = paper.xpath('p[3]/a[3]/@href').extract()
            _sup_data = '' if len(_sup_data) == 0 else ('' if 
                ('github' in _sup_data[0] or 'gitlab' in _sup_data[0] or 'bitbucket' in _sup_data[0] or 'proceedings' not in _sup_data[0] or not _sup_data[0].endswith('pdf')) else _sup_data[0])
            _sup_data = _sup_data if not _sup_data.startswith('ttp') else 'h' + _sup_data
            item['sup'] = _sup_data
            yield item


class ICLRCrawler(Spider):
    name = "ConCrawler"
    allowed_domains = ["iclr.cc"]
    start_urls = ["https://iclr.cc/Conferences/2018/Schedule?type=Poster", "https://iclr.cc/Conferences/2018/Schedule?type=Oral"]

    def parse(self, response):

        for poster in response.xpath('//div[starts-with(@id, "maincard_")]'):
            item = PapercrawlerItem()
            item["title"] = poster.xpath('.//div[@class="maincardBody"]/text()[1]').get()
            item["pdf"] = poster.xpath('.//a[@title="PDF"]/@href').get()
            item['sup'] = ''
            yield item
