# coding: utf-8

from pymongo import MongoClient
from scrapy_redis.scheduler import Scheduler
from scrapy.utils.reqser import request_from_dict
from scrapy_redis import connection, queue

from scrapy.utils.misc import load_object
import importlib
import six

from brand_spider.field_config import JDGoodInfoField as GIF
from brand_spider.spiders.jd_spider import JdSpider


class MyScheduler(Scheduler):
    """
    继承scrapy-redis默认的Scheduler，增加启动的时候从数据库读取上次关闭时候失败的请求
    """

    def __init__(self, server, settings, **kwargs):
        super(MyScheduler, self).__init__(server=server, **kwargs)
        # Mongo Server Connection
        self.client = MongoClient(settings.get('MONGO_URI'))
        self.col = self.client[settings.get('MONGO_DB')][settings.get('MONGO_FAILED_REQ_TB')]

    @classmethod
    def from_settings(cls, settings):
        kwargs = {
            'persist': settings.getbool('SCHEDULER_PERSIST'),
            'flush_on_start': settings.getbool('SCHEDULER_FLUSH_ON_START'),
            'idle_before_close': settings.getint('SCHEDULER_IDLE_BEFORE_CLOSE'),
        }

        # If these values are missing, it means we want to use the defaults.
        optional = {
            # TODO: Use custom prefixes for this settings to note that are
            # specific to scrapy-redis.
            'queue_key': 'SCHEDULER_QUEUE_KEY',
            'queue_cls': 'SCHEDULER_QUEUE_CLASS',
            'dupefilter_key': 'SCHEDULER_DUPEFILTER_KEY',
            # We use the default setting name to keep compatibility.
            'dupefilter_cls': 'DUPEFILTER_CLASS',
            'serializer': 'SCHEDULER_SERIALIZER',
        }
        for name, setting_name in optional.items():
            val = settings.get(setting_name)
            if val:
                kwargs[name] = val

        # Support serializer as a path to a module.
        if isinstance(kwargs.get('serializer'), six.string_types):
            kwargs['serializer'] = importlib.import_module(kwargs['serializer'])

        # Redis Server connection
        server = connection.from_settings(settings)
        # Ensure the connection is working.
        server.ping()

        return cls(server=server, settings=settings, **kwargs)

    def open(self, spider):
        self.spider = spider

        try:
            self.queue = load_object(self.queue_cls)(
                server=self.server,
                spider=spider,
                key=self.queue_key % {'spider': spider.name},
                serializer=self.serializer,
            )
        except TypeError as e:
            raise ValueError("Failed to instantiate queue class '%s': %s",
                             self.queue_cls, e)

        try:
            # for req_dict in self.col.find({"meta.category": {"$in": list(JdSpider.included_cat_list)}},
            #                               {'_id': 0}):
            count = 0
            for req_dict in self.col.find({"meta.item.category": {"$in": list(JdSpider.included_cat_list)}},
                                          {'_id': 0}):
                # for req_dict in self.col.find({}, {'_id': 0}):
                # if 'item' in req_dict['meta'] and len(req_dict['meta']['item'][GIF.SKUID]) >= 10:
                #     continue
                print ('-------------------add failure request to queue-------------------')
                count += 1
                req = request_from_dict(req_dict, spider)
                req.dont_filter = True
                req.meta['dont_redirect'] = False
                req.priority = 2
                self.enqueue_request(req)
            print(count)
        finally:
            self.client.close()

        try:
            self.df = load_object(self.dupefilter_cls)(
                server=self.server,
                key=self.dupefilter_key % {'spider': spider.name},
                debug=spider.settings.getbool('DUPEFILTER_DEBUG'),
            )
        except TypeError as e:
            raise ValueError("Failed to instantiate dupefilter class '%s': %s",
                             self.dupefilter_cls, e)

        if self.flush_on_start:
            self.flush()
        # notice if there are requests already in the queue to resume the crawl
        if len(self.queue):
            spider.log("Resuming crawl (%d requests scheduled)" % len(self.queue))