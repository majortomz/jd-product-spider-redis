# coding: utf-8

import win32ras
import urllib2
from brand_spider import settings


class VPNConnector(object):
    """
    可以设置自己的拨号...
    """

    test_url = 'http://www.baidu.com'

    def __init__(self):
        self.handle = self._connect()

    @staticmethod
    def _connect():
        return win32ras.Dial(
            None,
            None,
            (settings.VPN_NAME, "", "", "", "", ""),
            None
        )

    def connect(self):
        # 重试3次, 如果连上VPN且能正常访问网页，则返回True
        for n in range(0, 3):
            self.handle = self._connect()
            if self.handle[1] == 0 and self.test_connection():
                return True
        return False

    def disconnect(self):
        if self.handle is None:
            return
        try:
            win32ras.HangUp(self.handle[0])
        finally:
            self.handle = None

    @classmethod
    def test_connection(cls):
        """
        测试网络是否连通
        :return: 
        """
        try:
            urllib2.urlopen(cls.test_url, timeout=20)
            return True
        except urllib2.URLError as err:
            return False

    def test_and_reconnect(self):
        self.connect()
        return self.test_connection()

if __name__ == '__main__':
    vpn = VPNConnector()
    print vpn.handle
    print vpn.test_connection()