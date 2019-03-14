#coding:utf-8

from .dbHandler import Database
import pymysql

class Mysql(Database):
    # 从cfg中获取基本信息
    # *parameters为4元字符组，分别对应另外给定的host、port、user、password
    def __init__(self, uname, pwd, host, port):
        self._user = uname
        self._password = pwd
        self._host = host
        self._port = int(port)
        self._conn = None
        self._ReConnect()

    def _ReConnect(self):
        if not self._conn :
            self._conn = pymysql.connect(host=self._host, port=self._port, user=self._user, password=self._password, charset='utf8')
        else:
            pass


