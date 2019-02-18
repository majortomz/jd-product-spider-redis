# coding: utf-8

DEFAULT_CREATOR = 'zjw'


def get_meta(version, url, keywords, create_time, upate_time, app_name,
             craw_method=1, creator=DEFAULT_CREATOR):
    """
    返回es公共字段信息
    :param version: 
    :param url: 
    :param keywords: 
    :param create_time: 
    :param upate_time: 
    :param app_name: 
    :param craw_method: 
    :param creator: 
    :return: 
    """
    return {
        "version": version,
        "url": url,
        "crawler_method": craw_method,
        "keywords": keywords,
        "creator": creator,
        "create_time": create_time,
        "last_update_time": upate_time,
        "app_name": app_name
    }