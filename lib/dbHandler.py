#coding:utf-8

from abc import ABCMeta,abstractmethod,abstractproperty
import os
os.environ['NLS_LANG'] = 'SIMPLIFIED CHINESE_CHINA.UTF8' 

class Database(object):
	__metaclass__= ABCMeta

	def __init__(self):
		pass

	@abstractmethod
	def _ReConnect(self):
		pass

	def __del__(self):
		if self._conn:
			self._conn.close()
			self._conn = None

	def _DelCursor(self , cur):
		if cur:
			cur.close()

	def _NewCursor(self):
		cur = self._conn.cursor()
		if cur:
			return cur
		else:
			#print("#Error# Get New Cursor Failed.")
			return None

	# 检查是否允许执行的sql语句
	def _PermitedUpdateSql(self ,sql):
		rt = True
		lrsql = sql.lower()
		sql_elems = lrsql.strip().split()
		#print(sql_elems)
		# update和delete最少有四个单词项
		if len(sql_elems) < 4 :
			rt = False
		# 更新删除语句，判断首单词，不带where语句的sql不予执行
		elif sql_elems[0] in [ 'update', 'delete' ]:
			if 'where' not in sql_elems :
				rt = False
		elif sql_elems[0] == 'insert' and sql_elems[1] == 'into':
			if 'values' not in sql_elems:
				rt = False
		return rt

	# 查询
	def Query(self , sql, nStart=0 , nNum=- 1):
		rt = []

		# 获取cursor
		cur = self._NewCursor()
		if not cur:
			return rt

		# 查询到列表
		cur.execute(sql)
		if( nStart==0) and(nNum==1):
			rt.append( cur.fetchone())
		else:
			rs = cur.fetchall()
			if nNum==- 1:
				rt.extend( rs[nStart:])
			else:
				rt.extend( rs[nStart:nStart +nNum])

		# 释放cursor
		self._DelCursor(cur)

		return rt

	# 插入
	def Insert(self, sql):
		rt = None
		cur = self._NewCursor()
		if not cur:
			return rt
		
		if not self._PermitedUpdateSql(sql):
			return rt
		#print(sql)
		rt = cur.execute(sql)
		rt = cur.execute('commit')
		self._DelCursor(cur)
		return rt

	# 更新
	def Exec(self ,sql):
		# 获取cursor
		rt = None
		cur = self._NewCursor()
		if not cur:
			return rt

		# 判断sql是否允许其执行
		if not self._PermitedUpdateSql(sql):
			#print(sql)
			return rt

		# 执行语句
		#print(sql)
		rt = cur.execute(sql)
		rt = cur.execute('commit')
		# 释放cursor
		self._DelCursor(cur)

		return  rt




