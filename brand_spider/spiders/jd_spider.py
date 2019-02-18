# coding: utf-8
# @Author: zjw

from scrapy.spiders import Request, Spider
from scrapy_redis.spiders import RedisSpider
from scrapy.exceptions import CloseSpider
from scrapy.spidermiddlewares.httperror import HttpError
from twisted.internet.error import TimeoutError, DNSLookupError, TCPTimedOutError
from scrapy.utils.reqser import request_to_dict, request_from_dict
from pymongo import MongoClient
from datetime import datetime
import urlparse
import logging
import traceback
import random

from brand_spider.field_config import JDGoodInfoField as GIF
from brand_spider.items import JDGoodInfoItem as GItem
from brand_spider.price_helper import JDApiPriceTool, ManManBuyPriceTool
from brand_spider.utils import mail_helper


class JdSpider(RedisSpider):
    """
    京东上商品信息的爬虫
    """

    name = 'jd_spider'
    redis_key = "jd_spider:start_urls"
    # start_urls = ['https://www.jd.com/allSort.aspx']

    # price_req_count = 0
    # price_req_index = 0
    # price_url_format = ['http://p.3.cn/prices/get?skuid=J_{0}', 'http://p.3.cn/prices/mgets?skuIds=J_{0}']
    ptIndex = 0
    ptCount = 0
    priceToolList = [ManManBuyPriceTool()]
    jdPriceTool = JDApiPriceTool()

    source = u'京东'

    excluded_cat_list = {u'图书、音像、电子书刊', u'彩票、旅行、充值、票务', u'整车'}
    # included_cat_list = {u'母婴', u'礼品箱包', u'珠宝', u'玩具乐器', u'个护化妆', u'服饰内衣',
    # u'钟表', u'鞋靴', u'手机', u'数码', u'电脑办公', u'家用电器'}
    included_cat_list = {u'食品饮料、保健食品'}

    FAILURE_EXCEPTIONS = (TimeoutError, TCPTimedOutError, HttpError, DNSLookupError)

    def __init__(self, mongo_uri, mongo_db, failed_req_col, stats, name=None, **kwargs):
        super(JdSpider, self).__init__(name, **kwargs)
        self.client = MongoClient(mongo_uri, socketKeepAlive=True)
        self.db = self.client[mongo_db]
        self.col_failed_req = failed_req_col
        self.stats = stats

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        print('from_crawler')
        spider = cls(mongo_uri=crawler.settings.get('MONGO_URI'),
                     mongo_db=crawler.settings.get('MONGO_DB'),
                     failed_req_col=crawler.settings.get('MONGO_FAILED_REQ_TB'),
                     stats=crawler.stats,
                     *args, **kwargs)
        spider.setup_redis(crawler)
        spider._set_crawler(crawler)
        return spider

    def errback_http(self, failure):
        # log all failures
        self.logger.error(repr(failure))

        # handle special error
        if failure.check(HttpError, DNSLookupError, TimeoutError, TCPTimedOutError):
            request = failure.request
            req_dict = request_to_dict(request, self)
            # save failed request in database
            print ('-------------------failure request-------------------')
            if not self.db[self.col_failed_req].find_one({'url': req_dict['url']}):
                self.db[self.col_failed_req].insert(req_dict)
            # self.db[self.col_failed_req].update({'url': req_dict['url']}, req_dict, upsert=True)

    def start_requests(self):
        print('qqqqq')
        return self.next_requests()
        # for start_url in self.start_urls:
        #     yield Request(url=start_url, callback=self.parse, dont_filter=True)

    def parse(self, response):
        """
        解析京东商品的分类页面
        """
        selectors = response.css('.category-items .col .category-item')
        logging.info(u'------------从主页上获取的一级类别数目为：{0}------------'.format(len(selectors)))
        url_count = 0
        for main_cat_sel in selectors:
            # 第一级类别名称
            first_cat = main_cat_sel.css('.mt .item-title span::text').extract_first()
            if first_cat not in self.included_cat_list:
                continue
            logging.info(first_cat)
            # 找到二级类别名称，以及其下面的三级类别名称列表和对应的页面
            for items_sel in main_cat_sel.css('.mc div.items dl.clearfix'):
                # 二级类别名称
                second_cat = items_sel.css('dt a::text').extract_first()
                # 三级类别名称，技改类别下面商品列表的链接
                for item_sel in items_sel.css('dd a'):
                    url_count += 1
                    third_cat = item_sel.xpath('./text()').extract_first()
                    url = item_sel.xpath('./@href').extract_first()
                    req = Request(url=urlparse.urljoin(response.url, url), callback=self.parse_good_list,
                                  errback=self.errback_http, dont_filter=True)
                    req.meta[GIF.CATEGORY] = [first_cat, second_cat, third_cat]
                    yield req
        logging.info(u'------------从主页上获取的三级类别数目为：{0}------------'.format(url_count))

    def parse_good_list(self, response):
        """
        解析三级类别下的商品列表页面
        """
        for g_item in response.css('div#plist li.gl-item div.j-sku-item'):
            item = {
                GIF.SKUID: g_item.xpath('./@data-sku').extract_first(),
                GIF.NAME: ''.join(g_item.css('div.p-name a em::text').extract()),
                GIF.URL: g_item.css('div.p-name a::attr(href)').extract_first(),
                GIF.CATEGORY: response.meta[GIF.CATEGORY]
            }
            # 判断sku-id是否是京东自营，如果非自营，则不爬取
            if not self.is_sku_self_supported(item[GIF.SKUID]):
                continue
            item[GIF.URL] = urlparse.urljoin(response.url, item[GIF.URL])
            req = Request(item[GIF.URL], callback=self.parse_good_brand, errback=self.errback_http)
            req.meta['item'] = item
            # req.meta['dont_redirect'] = True
            yield req
        # 解析该商品类别页面的下一页
        next_page_url = response.css('#J_bottomPage span.p-num a.pn-next::attr(href)').extract_first()
        if next_page_url:
            req = Request(url=urlparse.urljoin(response.url, next_page_url), callback=self.parse_good_list,
                          errback=self.errback_http, dont_filter=True)
            req.meta[GIF.CATEGORY] = response.meta[GIF.CATEGORY]
            yield req

    def parse_good_brand(self, response):
        """
        解析商品详情页面的商品品牌和描述信息、规格信息
        """
        item = response.meta['item']
        brand = response.css('ul#parameter-brand li[title]::attr(title)').extract_first()
        name = item[GIF.NAME].strip()
        if len(name) <= 0:
            item[GIF.NAME] = ''.join(response.css('div.sku-name::text').extract()).strip()
        item[GIF.BRAND] = brand
        item[GIF.DESC] = self.get_good_desc(response)
        item[GIF.SPEC] = self.get_good_spec(response)
        item[GIF.UPDATE_TIME] = datetime.now()
        # 不请求商品的价格
        item[GIF.PRICE] = None
        good_item = GItem(item)
        yield good_item
        # 发送请求, 从价格查询网站中选择一个
        # pt_index = self.get_price_tool_index()
        # req = Request(url=self.priceToolList[pt_index].get_price_url(item[GIF.URL]),
        #               callback=self.parse_good_price)
        # req.meta['item'] = item
        # req.meta['is_jd_api'] = False
        # req.meta['pt_index'] = pt_index
        # yield req

    @staticmethod
    def get_good_desc(response):
        """
        解析商品详情页面的商品描述信息
        :param response: 
        :return: 
        """
        desc = dict()
        for li in response.css('ul.parameter2 li'):
            para = ''.join(li.xpath('.//text()').extract())
            arr = para.split(u'：', 1)
            if len(arr) == 2:
                # mongo does not support dot field
                # such as 'USB 2.0': '*2',  replace '.' with '-' 'USB 2.0' -> 'USB 2_0'
                arr[0] = arr[0].replace('.', '_')
                desc[arr[0]] = arr[1]
            else:
                logging.warning("Parsing product desc meets unexpected condition! URL: " + response.url)
        return desc

    @staticmethod
    def get_good_spec(response):
        """
        解析商品详情页面的规格信息
        :param response: 
            <div class="Ptable-item">
                <h3>特性</h3>
                <dl>
                    <dt>特性</dt> <dd>打破容量和性能界限，推动NVMe时代大众化的新一代SSD</dd>
                    <dt>尺寸</dt> <dd>80.15*22.15*2.38</dd>
                    <dt>工作温度</dt> <dd>0 - 70 ℃ Operating Temperature</dd>
                    <dt>TRIM</dt> <dd>支持</dd>
                </dl>
            </div>
        :return: 
        """
        spec = dict()
        for tb_item in response.css('div.Ptable div.Ptable-item'):
            head = tb_item.xpath('./h3/text()').extract_first()
            dt = tb_item.css('dl dt::text').extract()
            dd = tb_item.css('dl dd::text').extract()
            content = dict()
            for i, key in enumerate(dt):
                key = key.replace('.', '_')
                content[key] = dd[i]
            spec[head] = content
        return spec

    def parse_good_price(self, response):
        """
        解析每个商品的价格
        """
        try:
            pt_index = response.meta['pt_index']
            if response.meta['is_jd_api']:
                price = self.jdPriceTool.get_price_from_response(response)
            else:
                price = self.priceToolList[pt_index].get_price_from_response(response)
            item = response.meta['item']
            item[GIF.PRICE] = price
            item[GIF.UPDATE_TIME] = datetime.utcnow()
            item[GIF.SOURCE] = self.source
            good_item = GItem(item)
            yield good_item
        except Exception as e:
            # 返回的数据格式：[{"id":"J_4426168","p":"23.90","m":"32.01","op":"32.00"}]
            logging.error(u"解析价格错误，链接为： " + response.url)
            logging.error(e.message)
            logging.error(traceback.format_exc())
            if response.meta['is_jd_api']:
                raise CloseSpider(u'解析价格错误， 返回数据为： ' + response.body)
            else:
                # 使用京东API进行查询
                item = response.meta['item']
                req = Request(url=self.jdPriceTool.get_price_url(item[GIF.SKUID]), callback=self.parse_good_price)
                req.meta['item'] = item
                req.meta['is_jd_api'] = True
                yield req

    def close(self, reason):
        try:
            self.client.close()
        except Exception as err:
            logging.error(err.message)
        try:
            logging.info(u"Sending mail!")
            body = reason
            for key, value in self.crawler.stats.get_stats().items():
                body += '\n' + key + ':' + str(value)
            mail_helper.send_mail(u'Scrapy爬虫关闭状态', body)
        except Exception as err:
            logging.error(u'Fail to send email! Detail: ' + err.message)

    @classmethod
    def get_price_tool_index(cls):
        """
        返回price tool 的引用
        :return: 
        """
        if cls.ptCount <= 0:
            cls.ptCount = random.randint(2000, 3000)
            cls.ptIndex = (cls.ptIndex + 1) % len(cls.priceToolList)
        cls.ptCount -= 1
        return cls.ptIndex

    @staticmethod
    def is_sku_self_supported(sku_id):
        """
        判断商品sku是否是京东自营,
        京东自营：6~7位, 8位(图书、音像)
        第三方：10位即以上
        :return: 
        """
        if 0 < len(sku_id) <= 8:
            return True
        return False

