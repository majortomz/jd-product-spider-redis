# coding: utf-8
# @Author : zjw

from scrapy.spiders import Spider
from scrapy.spiders import Request
from selenium import webdriver
from lxml import etree
import logging
import traceback
import urlparse

from brand_spider.items import GoodInfoItem
from brand_spider.field_config import GoodInfoField as GIF


class KLSpider(Spider):
    """
    网易考拉海购的商品信息爬虫
    """
    name = 'kaola_spider'
    allowed_domains = ['kaola.com']
    main_page_url = 'http://www.kaola.com/'
    source = u'考拉海购'

    def start_requests(self):
        """
        加载考拉海购主页，从主页的商品分类入手开始爬取
        :return: 
        """
        request_list = []
        browser = webdriver.PhantomJS()
        try:
            browser.get(self.main_page_url)
            html = etree.HTML(browser.page_source)
            # print chardet.detect(browser.page_source)['encoding']
            for main_cat in html.xpath('//ul[@class="catitmlst j-catmenu"]//li[@class="catli j-catli"]'):
                # 一级类别名称
                first_category = main_cat.xpath('./span[@class="t"]/text()')[0]
                for sub_cat in main_cat.xpath('.//p[@class="title"]/a'):
                    # 二级类别名称
                    second_category = sub_cat.text
                    # 该二级类别对应的url
                    href = sub_cat.xpath('./@href')[0]
                    print(first_category, second_category, href)
                    req = Request(url=urlparse.urljoin(self.main_page_url, href), dont_filter=True)
                    req.meta[GIF.CATEGORY] = [first_category, second_category]
                    request_list.append(req)
        except Exception as e:
            logging.error("Load kaola main page error, failed to parse category url!!!")
            logging.error(e.message)
            logging.error(traceback.format_exc())
        finally:
            # 关闭webdriver
            if browser:
                browser.quit()
        logging.info(u"-----------得到的二级目录链接数目为：{0}-----------".format(len(request_list)))
        return request_list

    def parse(self, response):
        """
        解析商品类别对应的页面，初步得到商品的部分信息
        :param response: 
        :return: 
        """
        # 解析该商品类别页面中每个商品的信息
        for g_item in response.css('#searchresult li.goods>div>div.desc'):
            item = {
                GIF.URL: g_item.css('div.titlewrap').xpath('./a/@href').extract_first(),
                GIF.NAME: g_item.css('div.titlewrap').xpath('./a/@title').extract_first(),
                GIF.PRICE: g_item.css('p.price span.cur::text').extract_first(),
                GIF.SKUID: g_item.css('div.titlewrap').xpath('./a/@href').re_first('/\w+/(\d+).html'),
                GIF.CATEGORY: response.meta[GIF.CATEGORY]
            }
            item[GIF.URL] = urlparse.urljoin(response.url, item[GIF.URL])
            req = Request(url=urlparse.urljoin(response.url, item[GIF.URL]), callback=self.parse_item_page)
            req.meta[GIF.CATEGORY] = response.meta[GIF.CATEGORY]
            req.meta['item'] = item
            yield req
        # 解析该商品类别页面的下一页
        next_page_url = response.css('div.splitPages a.nextPage::attr(href)').extract_first()
        if next_page_url:
            next_req = Request(url=urlparse.urljoin(response.url, next_page_url), callback=self.parse)
            next_req.meta[GIF.CATEGORY] = response.meta[GIF.CATEGORY]
            yield next_req

    def parse_item_page(self, response):
        """
        解析商品详情页面的信息，得到商品的subTitle，地区，品牌名等信息
        :return: 
        """
        item = response.meta['item']
        item[GIF.COUNTRY] = response.xpath('//dt[@class="orig-country"]/span[1]/text()').extract_first()
        item[GIF.BRAND] = response.css('dt.orig-country a.brand::text').extract_first()
        item[GIF.DESC] = response.css('dl.PInfo dt.subTit::text').extract_first()
        good_item = GoodInfoItem(item)
        yield good_item
