# -*- coding: utf-8 -*-

# Scrapy settings for brand_spider project
#
# For simplicity, this file contains only settings considered important or
# commonly used. You can find more settings consulting the documentation:
#
#     http://doc.scrapy.org/en/latest/topics/settings.html
#     http://scrapy.readthedocs.org/en/latest/topics/downloader-middleware.html
#     http://scrapy.readthedocs.org/en/latest/topics/spider-middleware.html

BOT_NAME = 'brand_spider'

SPIDER_MODULES = ['brand_spider.spiders']
NEWSPIDER_MODULE = 'brand_spider.spiders'

ROBOTSTXT_OBEY = False

COOKIES_ENABLED = False

CONCURRENT_REQUESTS = 32
# DOWNLOAD_DELAY = 0

REDIRECT_ENABLED = True

RETRY_ENABLED = True
RETRY_TIMES = 3

DOWNLOADER_MIDDLEWARES = {
   'brand_spider.middlewares.NormalResponseHandlerMiddleware': 110,
   'scrapy.downloadermiddlewares.useragent.UserAgentMiddleware': None,
   'brand_spider.middlewares.UserAgentMiddleware': 450,
   'scrapy.downloadermiddlewares.retry.RetryMiddleware': None,
   'brand_spider.middlewares.FailureRetryMiddleware': 501
}

ITEM_PIPELINES = {
   'brand_spider.pipelines.BrandSpiderPipeline': 300,
}

# DUPEFILTER_CLASS = 'brand_spider.duplicate_filter.CustomDupeFilterDB'
DUPEFILTER_CLASS = "scrapy_redis.dupefilter.RFPDupeFilter"
DUPEFILTER_DEBUG = True

SCHEDULER = "brand_spider.scheduler.MyScheduler"
SCHEDULER_QUEUE_CLASS = 'scrapy_redis.queue.SpiderPriorityQueue'
SCHEDULER_PERSIST = True
REDIS_URL = 'redis://root:PASSWORD_HERE@localhost:6379/2'

MONGO_URI = 'localhost:27017'      # localhost:27017
MONGO_DB = 'ebweb'    # items_redis_test
# MONGO_DUP_URL_TB = 'urls_dup'    # 用于去重的url集合名称, 配合自定义的CustomDupeFilterDB
MONGO_FAILED_REQ_TB = 'failed_requests'
MONGO_JD_COLLECTION = 'jd'
MONGO_KAOLA_COLLECTION = 'kaola'

LOG_ENABLED = True
LOG_LEVEL = 'DEBUG'
LOG_FILE = 'log.txt'
LOG_STDOUT = False

MAIL_HOST = 'SMPT HOST'
MAIL_FROM = 'EMAIL_ADDRESS'
MAIL_USER = 'EMAIL_ADDRESS'
MAIL_PASS = 'EMAIL_PASSWORD'
MAIL_TO = 'EMAIL_TO_ADDRESS'

ES_HOST_LIST = ['ES_HOST_LIST']
ES_JD_INDEX = 'crawler-jd'
ES_KL_INDEX = 'crawler-kaola'
ES_JDGOODS_TYPE = 'product_info'
ES_KLGOODS_TYPE = 'product_info'


# Crawl responsibly by identifying yourself (and your website) on the user-agent
#USER_AGENT = 'brand_spider (+http://www.yourdomain.com)'

# Obey robots.txt rules


# Configure maximum concurrent requests performed by Scrapy (default: 16)
#CONCURRENT_REQUESTS = 32

# Configure a delay for requests for the same website (default: 0)
# See http://scrapy.readthedocs.org/en/latest/topics/settings.html#download-delay
# See also autothrottle settings and docs
#DOWNLOAD_DELAY = 3
# The download delay setting will honor only one of:
#CONCURRENT_REQUESTS_PER_DOMAIN = 16
#CONCURRENT_REQUESTS_PER_IP = 16

# Disable Telnet Console (enabled by default)
#TELNETCONSOLE_ENABLED = False

# Override the default request headers:
#DEFAULT_REQUEST_HEADERS = {
#   'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
#   'Accept-Language': 'en',
#}

# Enable or disable spider middlewares
# See http://scrapy.readthedocs.org/en/latest/topics/spider-middleware.html
#SPIDER_MIDDLEWARES = {
#    'brand_spider.middlewares.BrandSpiderSpiderMiddleware': 543,
#}

# Enable or disable downloader middlewares
# See http://scrapy.readthedocs.org/en/latest/topics/downloader-middleware.html
#DOWNLOADER_MIDDLEWARES = {
#    'brand_spider.middlewares.MyCustomDownloaderMiddleware': 543,
#}

# Enable or disable extensions
# See http://scrapy.readthedocs.org/en/latest/topics/extensions.html
#EXTENSIONS = {
#    'scrapy.extensions.telnet.TelnetConsole': None,
#}

# Configure item pipelines
# See http://scrapy.readthedocs.org/en/latest/topics/item-pipeline.html
#ITEM_PIPELINES = {
#    'brand_spider.pipelines.BrandSpiderPipeline': 300,
#}

# Enable and configure the AutoThrottle extension (disabled by default)
# See http://doc.scrapy.org/en/latest/topics/autothrottle.html
#AUTOTHROTTLE_ENABLED = True
# The initial download delay
#AUTOTHROTTLE_START_DELAY = 5
# The maximum download delay to be set in case of high latencies
#AUTOTHROTTLE_MAX_DELAY = 60
# The average number of requests Scrapy should be sending in parallel to
# each remote server
#AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0
# Enable showing throttling stats for every response received:
#AUTOTHROTTLE_DEBUG = False

# Enable and configure HTTP caching (disabled by default)
# See http://scrapy.readthedocs.org/en/latest/topics/downloader-middleware.html#httpcache-middleware-settings
#HTTPCACHE_ENABLED = True
#HTTPCACHE_EXPIRATION_SECS = 0
#HTTPCACHE_DIR = 'httpcache'
#HTTPCACHE_IGNORE_HTTP_CODES = []
#HTTPCACHE_STORAGE = 'scrapy.extensions.httpcache.FilesystemCacheStorage'
