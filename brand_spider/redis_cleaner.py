# coding: utf-8

import settings
import redis

requests_key = 'jd_spider:requests'
filter_key = 'jd_spider:dupefilter'

if __name__ == '__main__':

    input = raw_input("确定要删除redis数据库上的数据？(YES/NO) 是,则输入YES. ")
    if input is None or input != 'YES':
        print('取消清空redis操作.')
    try:
        conn = redis.from_url(settings.REDIS_URL)
    except Exception:
        conn = None

    if conn:
        if requests_key in conn.keys():
            conn.delete(requests_key)
        if filter_key in conn.keys():
            conn.delete(filter_key)
        print('Clean Over')
