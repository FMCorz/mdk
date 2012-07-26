#!/usr/bin/env python
# -*- coding: utf-8 -*-

class DB():

	conn = None
	cur = None
	engine = None
	options = None

	def __init__(self, engine, options):

		self.engine = engine
		self.options = options

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

		elif engine == 'pgsql':
			from bpgsql import bpgsql
			self.conn = bpgsql.connect(
				host=str(options['host']),
				port=str(options['port']),
				username=str(options['user']),
				password=str(options['passwd']),
				dbname=''
			)
			self.cur = self.conn.cursor()

		else:
			raise Exception('DB engine %s not supported' % engine)

	def createdb(self, db):

		if self.engine == 'mysqli':
			self.cur.execute('CREATE DATABASE %s DEFAULT CHARACTER SET utf8 COLLATE utf8_general_ci' % db)
		elif self.engine == 'pgsql':
			self.cur.execute('CREATE DATABASE %s WITH ENCODING \'UNICODE\'' % db)

	def dropdb(self, db):

		self.cur.execute('DROP DATABASE %s' % db)

	def dbexists(self, db):

		count = None
		if self.engine == 'mysqli':
			self.cur.execute("SELECT COUNT('*') FROM information_schema.SCHEMATA WHERE SCHEMA_NAME LIKE '%s'" % db)
			count = self.cur.fetchone()[0]

		elif self.engine == 'pgsql':
			self.cur.execute("SELECT COUNT('*') FROM pg_database WHERE datname='%s'" % db)
			count = self.cur.fetchone()[0]

		return count > 0

	def selectdb(self, db):

		if self.engine == 'mysqli':
			self.cur.execute('USE %s' % db)

		elif self.engine == 'pgsql':
			if self.cur:
				self.cur.close()
			if self.conn:
				self.close()

			self.conn = bpgsql.connect(
				host=self.options['host'],
				port=int(self.options['port']),
				username=self.options['user'],
				password=self.options['passwd'],
				dbname=db
			)
			self.cur = self.conn.cursor()
