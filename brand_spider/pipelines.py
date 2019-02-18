# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html

from pymongo.errors import AutoReconnect
from pymongo import MongoClient
from elasticsearch import Elasticsearch
from brand_spider.items import GoodInfoItem, JDGoodInfoItem
from brand_spider.field_config import JDGoodInfoField as JGif, GoodInfoField as Gif
import logging
import random
import traceback


class BrandSpiderPipeline(object):

    goods_collect_info = 'kaola'
    jd_info_collect = 'jd'

    def __init__(self, mongo_uri, mongo_db, failed_req):
        self.mongo_uri = mongo_uri
        self.mongo_db = mongo_db
        self.failed_req_col = failed_req

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            mongo_uri=crawler.settings.get('MONGO_URI'),
            mongo_db=crawler.settings.get('MONGO_DB', 'items'),
            failed_req=crawler.settings.get('MONGO_FAILED_REQ_TB')
        )

    def open_spider(self, spider):
        self.client = MongoClient(self.mongo_uri, socketKeepAlive=True)
        self.db = self.client[self.mongo_db]

    def close_spider(self, spider):
        self.client.close()

    def process_item(self, item, spider):
        if isinstance(item, GoodInfoItem):
            self.db[self.goods_collect_info].insert(dict(item))
        elif isinstance(item, JDGoodInfoItem):
            query = {JGif.SKUID: item[JGif.SKUID]}
            try:
                self.db[self.jd_info_collect].update(query, {"$set": dict(item)}, upsert=True)
            except AutoReconnect as err:
                wait_t = random.randint(5, 20) / 10.0
                logging.error(err.message + ' URL: ' + item[JGif.URL])
                logging.error(traceback.format_exc())
                logging.info("Pymongo auto reconnecting. Waiting for %.1f seconds", wait_t)
                self.db[self.jd_info_collect].update(query, {"$set": dict(item)}, upsert=True)
            except Exception as err:
                logging.error(err.message + ' URL: ' + item[JGif.URL])
                logging.error(traceback.format_exc())
                logging.info(dict(item))
        return item


class EsPipeline(object):

    def __init__(self, es_hosts, es_jd_index, es_kl_index, es_jd_good_type, es_kl_good_type):
        self.es_hosts = es_hosts
        self.es_jd_index = es_jd_index
        self.es_kl_index = es_kl_index
        self.es_jd_good_type = es_jd_good_type
        self.es_kl_good_type = es_kl_good_type

        self.create_time = '2017-06-15T15:30:25.117000+08:00'

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            es_hosts=crawler.settings.get('ES_HOST_LIST'),
            es_jd_index=crawler.settings.get('ES_JD_INDEX'),
            es_kl_index=crawler.settings.get('ES_KL_INDEX'),
            es_jd_good_type=crawler.settings.get('ES_JDGOODS_TYPE'),
            es_kl_good_type=crawler.settings.get('ES_KLGOODS_TYPE')
        )

    def open_spider(self, spider):
        self.es = Elasticsearch(hosts=self.es_hosts)

    def close_spider(self, spider):
        pass

    def process_item(self, item, spider):
        if isinstance(item, GoodInfoItem):
            pass
        elif isinstance(item, JDGoodInfoItem):
            try:
                pass
            except Exception as err:
                logging.error(err.message)
                logging.error(traceback.format_exc())
                logging.info(dict(item))
        return item
