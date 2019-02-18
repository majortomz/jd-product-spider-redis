# coding: utf-8

from abc import ABCMeta
import random
import json


class PriceTool(object):
    __metaclass__ = ABCMeta

    price_url_format = ''

    def get_price_url(self, url):
        return self.price_url_format.format(url)

    def get_price_from_response(self, response):
        pass


class JDApiPriceTool(PriceTool):
    """
    京东商品价格API查询
    """
    price_url_format = ['http://p.3.cn/prices/get?skuid=J_{0}', 'http://p.3.cn/prices/mgets?skuIds=J_{0}']

    def get_price_url(self, url):
        random.choice(self.price_url_format).foramt(url)

    def get_price_from_response(self, response):
        data = json.loads(response.body)
        price = data[0]['p']
        return price


class ManManBuyPriceTool(PriceTool):
    """
    慢慢买历史价格查询
    """
    price_url_format = 'http://tool.manmanbuy.com/history.aspx?w=951&h=580&h2=420&m=1&e=1&tofanli=0' \
                       '&url={0}'

    def get_price_from_response(self, response):
        return response.xpath('//div[@class="bigwidth"]/span/text()[5]').re_first('(\d+.{0,1}\d*)')


class GWDangPriceTool(PriceTool):
    """
    购物党历史价格查询
    """
    price_url_format = 'http://www.gwdang.com/trend?url={0}'

    def get_price_from_response(self, response):
        pass


class LSJGPriceTool(PriceTool):
    """
    www.lsjgcx.com价格查询
    """
    price_url_format = 'http://ls.wgxdxx.com/price.aspx?url={0}'

    def get_price_from_response(self, response):
        pass