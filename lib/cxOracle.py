#coding:utf-8
import cx_Oracle
#import rsa

from .dbHandler import Database
import os
os.environ['NLS_LANG'] = 'SIMPLIFIED CHINESE_CHINA.UTF8' 

class cxOracle(Database):
    def __init__(self, uname, pwd, tns):
        self._uname = uname
        self._pwd = pwd
        self._tns = tns
        self._conn = None
        self._ReConnect()

    def _ReConnect(self):
        if not self._conn :
            #print('aaa')
            self._conn = cx_Oracle.connect(self._uname, self._pwd, self._tns)
        else:
            pass
