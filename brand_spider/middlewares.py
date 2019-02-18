# -*- coding: utf-8 -*-

# Define here the models for your spider middleware
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/spider-middleware.html

from scrapy import signals
from scrapy.exceptions import CloseSpider
from scrapy.utils.reqser import request_to_dict
from scrapy.downloadermiddlewares.retry import RetryMiddleware
from twisted.internet.error import TimeoutError, DNSLookupError, ConnectionRefusedError,\
    TCPTimedOutError, ConnectionLost
from twisted.web.http import PotentialDataLoss
from pymongo import MongoClient
import random
import logging

from brand_spider.user_agent import user_agents
from brand_spider.spiders.jd_spider import JdSpider
from brand_spider.utils.vpn_connector import VPNConnector


class NormalResponseHandlerMiddleware(object):
    """
    该中间件位于最接近引擎的位置，处理得到正常响应的情况
    """
    def __init__(self, settings):
        self.client = MongoClient(settings.get('MONGO_URI'), socketKeepAlive=True)
        self.db = self.client[settings.get('MONGO_DB')]
        self.failed_req_col = settings.get('MONGO_FAILED_REQ_TB')

    @classmethod
    def from_crawler(cls, crawler):
        handler = cls(crawler.settings)
        crawler.signals.connect(handler.spider_closed, signal=signals.spider_closed)
        return handler

    def process_request(self, request, spider):
        return None

    def process_response(self, request, response, spider):
        """
        查看数据库中是否有该请求失败的记录，如果存在，则去除
        """
        url = request.url
        self.db[self.failed_req_col].delete_one({'url': url})
        if 'item' in request.meta:
            url = request.meta['item']['url']
            self.db[self.failed_req_col].delete_one({'url': url})
        return response

    def spider_closed(self, spider):
        try:
            self.client.close()
        except Exception as err:
            logging.info(err.message)


class UserAgentMiddleware(object):

    def process_request(self, request, spider):
        agent = random.choice(user_agents)
        request.headers['User-Agent'] = agent
        return None

    def process_response(self, request, response, spider):
        return response


class RetryPriceMiddleware(RetryMiddleware):

    price_url = 'http://p.3.cn/prices/'
    err_msg = '{"error":"pdos_captcha"}'
    reason = u'请求价格时遇到{"error": "pdos_capcha"}的情况'

    def __init__(self, crawler):
        super(RetryPriceMiddleware, self).__init__(crawler.settings)
        self.crawler = crawler

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler)

    def process_response(self, request, response, spider):
        """
        处理请求价格时遇到{"error": "pdos_capcha"}的情况
        """
        if spider.name is not JdSpider.name or not response.url.startswith(self.price_url):
            return response
        if self.err_msg in response.body:
            self.crawler.engine.pause()
            logging.warning(u'爬虫暂停，原因：' + self.reason)
            self.crawler.engine.unpause()
            return self._retry(request, self.reason, spider) or response


class FailureRetryMiddleware(RetryMiddleware):

    vpn_conn = VPNConnector()

    # 要处理的网络相关异常，如超时、连接拒绝、网站无法找到等
    NETWORDK_EXCEPTIONS = (TimeoutError, DNSLookupError, ConnectionRefusedError, TCPTimedOutError,
                           ConnectionLost, PotentialDataLoss)

    def __init__(self, crawler):
        super(FailureRetryMiddleware, self).__init__(crawler.settings)
        self.crawler = crawler
        settings = crawler.settings
        self.client = MongoClient(settings.get('MONGO_URI'), socketKeepAlive=True)
        self.db = self.client[settings.get('MONGO_DB')]
        self.failed_req_col = settings.get('MONGO_FAILED_REQ_TB')

    @classmethod
    def from_crawler(cls, crawler):
        ware = cls(crawler)
        crawler.signals.connect(ware.spider_closed, signal=signals.spider_closed)
        return ware

    def process_exception(self, request, exception, spider):
        if isinstance(exception, self.NETWORDK_EXCEPTIONS) and not request.meta.get('dont_retry', False):
            retries = request.meta.get('retry_times', 0) + 1
            retry_times = self.max_retry_times
            if retries > 1 or not self.db[self.failed_req_col].find_one({'url': request.url}):
                logging.info('Save failed request to database, URL: ' + request.url)
                self.db[self.failed_req_col].insert(request_to_dict(request, spider))
            # 否则，判断网络连接是否通畅，处理断网情况
            if not self.vpn_conn.test_connection():
                self.crawler.engine.pause()
                logging.info(u'爬虫暂停，重新连接VPN')
                if not self.vpn_conn.connect():
                    logging.warning("Gave up retrying %(request)s (failed %(retries)d times): %(exception)s %(reason)s",
                                    {'request': request, 'retries': retries, 'exception': exception,
                                     'reason': u'无法连接网络'}, extra={'spider': spider})
                    self.crawler.engine.close_spider(spider, 'Network unreachable, can not connect to network!!!')
                self.crawler.engine.unpause()
                logging.info(u'爬虫unpause, 结束暂停')
            # 如果重试次数小于最大次数，则继续重试
            if retries <= retry_times:
                return self._retry(request, exception, spider)
            else:
                logging.warning("Gave up retrying %(request)s (failed %(retries)d times): %(exception)s",
                             {'request': request, 'retries': retries, 'exception': exception},
                             extra={'spider': spider})
                self.crawler.engine.close_spider(spider, 'Retry many times, and still fail: ' + request.url)
        elif isinstance(exception, self.EXCEPTIONS_TO_RETRY) \
                and not request.meta.get('dont_retry', False):
            return self._retry(request, exception, spider)

    def spider_closed(self, spider):
        try:
            self.client.close()
        except Exception as err:
            logging.info(err.message)
