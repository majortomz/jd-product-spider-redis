# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class BrandSpiderItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    pass


class BaseGoodInfoItem(scrapy.Item):
    # source = scrapy.Field()
    url = scrapy.Field()
    name = scrapy.Field()
    price = scrapy.Field()
    sku_id = scrapy.Field()
    category = scrapy.Field()
    brand = scrapy.Field()
    last_update_time = scrapy.Field()


class GoodInfoItem(BaseGoodInfoItem):

    country = scrapy.Field()
    desc = scrapy.Field()


class JDGoodInfoItem(BaseGoodInfoItem):
    desc = scrapy.Field()
    spec = scrapy.Field()
