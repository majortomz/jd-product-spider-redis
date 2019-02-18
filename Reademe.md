# brand_spider_redis

## 1. 环境说明

```
python 2.7.12
mongodb
redis
```

python库依赖：

```
scrapy 1.4.0
scrapy_redis
```

## 2. 启动过程

### 2.1 启动redis-server

本爬虫在windows环境下运行，因此安装的是windows版本的Redis，如有需要可以安装linux版本，其他设置如安全、备份等，具体教程参见[Redis中文参考文档](http://www.runoob.com/redis/redis-install.html)。

#### （a）进入redis安装目录，执行下面的命令：

**注：linux下面会有区别**

```shell
redis-server.exe redis.windows.conf
```

#### （b）启动redis-cli：

建立一个客户端连接，用于测试和查看，执行下面的命令，不是必须。

**注：由于是本地安装redis，爬虫也运行在本地，因此redis地址设置为127.0.0.1，实际运行时设置为redis所部署的服务器的地址**

```
redis-cli.exe -h 127.0.0.1 -p 6379
```

```
C:\Program Files\Redis>redis-cli.exe -h 127.0.0.1 -p 6379  # 登录
127.0.0.1:6379> AUTH "PASSWORD"							   # 验证密码
OK
127.0.0.1:6379> SELECT 2								   # 切换当前数据库，默认是0，本爬虫使用2 
OK
127.0.0.1:6379[2]> KEYS *								   # 列举当前数据库下面所有键
1) "jd_spider:dupefilter"								   # 用于scrapy_redis去重
2) "jd_spider:requests"									   # 用于存储requests请求队列
127.0.0.1:6379[2]>
```

### 2.2 维护start_url和请求队列

#### (a) 插入start_url

以**jd_spider**为例，每次重新爬取前，需要插入start_url否则爬虫一直处于idle状态。

爬虫每次启动时，或者idle时，从`jd_spider:start_urls`读取起始url，其数据结构采用Redis列表（List），因此需要用到`LPUSH`命令。

**命令格式：**

```
LPUSH KEY_NAME VALUE1[VALUE2]
```

**举例：**

```
127.0.0.1:6379[2]> LPUSH jd_spider:start_urls https://www.jd.com/allSort.aspx
```

#### (b) 查看请求队列

爬虫使用的队列是scrapy_redis的`scrapy_redis.queue.SpiderPriorityQueue`，如果要在请求队列插入一条，其采用Redis的有序集合（sorted set）,因此需要使用`ZADD`命令，一般不会用到这样的命令行手动插入，通常是在爬虫中代码读取保存的失败请求，将这些请求插入到redis队列。

**命令格式：**

```
ZADD KEY_NAME SCORE1 MEMBER1[SCORE2 MEMBER2]
```

```
127.0.0.1:6379[2]> ZADD jd_spider:requests 5 https://www.jd.com/allSort.aspx
```

### 2.3 启动爬虫

进入爬虫工程目录，启动爬虫。相关爬虫配置修改详见源码settings.py

```shell
scrapy crawl jd_spider
```

