#!/usr/bin/env python
# -*- coding: utf-8 -*-

class DB():

	conn = None
	cur = None
	engine = None

	def __init__(self, engine, options):

		self.engine = engine

		if engine == 'mysqli':
			import pymysql
			self.conn = pymysql.connect(
				host=options['host'],
				port=int(options['port']),
				user=options['user'],
				passwd=options['passwd'],
				db=None
			)
			self.cur = self.conn.cursor()
		else:
			raise Exception('DB engine %s not supported' % engine)

	def createdb(self, db):

		if self.engine == 'mysqli':
			self.cur.execute('CREATE DATABASE %s DEFAULT CHARACTER SET utf8 COLLATE utf8_general_ci' % db)

	def dropdb(self, db):

		if self.engine == 'mysqli':
			self.cur.execute('DROP DATABASE %s' % db)

	def dbexists(self, db):

		if self.engine == 'mysqli':
			self.cur.execute("SELECT COUNT('*') FROM information_schema.SCHEMATA WHERE SCHEMA_NAME LIKE '%s'" % db)
			count = self.cur.fetchone()
			return count[0] > 0

	def selectdb(self, db):

		if self.engine == 'mysqli':
			self.cur.execute('USE %s' % db)
