# -*- coding: utf-8 -*-
from __future__ import print_function
import logging
from pymongo import MongoClient

from scrapy.dupefilters import RFPDupeFilter


class CustomDupeFilterDB(RFPDupeFilter):

    def __init__(self, debug=False, mongo_uri=None, mongo_db=None, tb_dup=None):
        self.file = None
        self.fingerprints = set()
        self.logdupes = True
        self.debug = debug
        self.logger = logging.getLogger(__name__)
        # get visited urls from db
        self.client = MongoClient(mongo_uri)
        self.tb_dup_url = self.client[mongo_db][tb_dup]
        for obj in self.tb_dup_url.find({}, {"finger_print": 1, "_id": 0}):
            self.fingerprints.add(obj["finger_print"])

    def close(self, reason):
        if self.client:
            self.client.close()

    @classmethod
    def from_settings(cls, settings):
        debug = settings.getbool('DUPEFILTER_DEBUG')
        mongo_uri = settings.get('MONGO_URI')
        mongo_db = settings.get('MONGO_DB')
        tb_dup = settings.get('MONGO_DUP_URL_TB')
        return cls(debug, mongo_uri, mongo_db, tb_dup)

    def request_seen(self, request):
        fp = self.request_fingerprint(request)
        # if self.tb_dup_url.find_one({"finger_print": fp}):
        #     return True
        if fp in self.fingerprints:
            return True
        self.fingerprints.add(fp)
        self.tb_dup_url.insert({"finger_print": fp})

