#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pymysql
from bpgsql import bpgsql

class DB(object):

	conn = None
	cur = None
	engine = None
	options = None

	def __init__(self, engine, options):

		self.engine = engine
		self.options = options

		if engine == 'mysqli':
			self.conn = pymysql.connect(
				host = options['host'],
				port = int(options['port']),
				user = options['user'],
				passwd = options['passwd'],
				db = None
			)
			self.cur = self.conn.cursor()

		elif engine == 'pgsql':
			self.conn = bpgsql.connect(
				host = str(options['host']),
				port = str(options['port']),
				username = str(options['user']),
				password = str(options['passwd']),
				dbname = ''
			)
			self.cur = self.conn.cursor()

		else:
			raise Exception('DB engine %s not supported' % engine)

	def columns(self, table):

		columns = []

		if self.engine == 'mysqli':
			self.cur.execute('DESCRIBE %s' % table)
			for column in self.cur.fetchall():
				columns.append(column[0])

		return columns

	def createdb(self, db):

		if self.engine == 'mysqli':
			self.cur.execute('CREATE DATABASE %s DEFAULT CHARACTER SET utf8 COLLATE utf8_general_ci' % db)
		elif self.engine == 'pgsql':
			self.cur.execute('CREATE DATABASE %s WITH ENCODING \'UNICODE\'' % db)

	def dbexists(self, db):

		count = None
		if self.engine == 'mysqli':
			self.cur.execute("SELECT COUNT('*') FROM information_schema.SCHEMATA WHERE SCHEMA_NAME LIKE '%s'" % db)
			count = self.cur.fetchone()[0]

		elif self.engine == 'pgsql':
			self.cur.execute("SELECT COUNT('*') FROM pg_database WHERE datname='%s'" % db)
			count = self.cur.fetchone()[0]

		return count > 0

	def dropdb(self, db):

		self.cur.execute('DROP DATABASE %s' % db)

	def dump(self, fd, prefix = ''):
		"""Dump a database to the file descriptor passed"""

		if self.engine != 'mysqli':
			raise Exception('Function dump not supported by %s' % self.engine)
		if not type(fd) == file:
			raise Exception('Passed parameter is not a file object')

		# Looping over selected tables
		tables = self.tables()
		for table in tables:
			if prefix != '' and not table.startswith(prefix):
				continue

			self.cur.execute('SHOW CREATE TABLE %s' % table)
			schema = self.cur.fetchone()[1]
			fd.write(schema + ';\n')

			# Get the columns
			columns = self.columns(table)

			# Get the field values
			self.cur.execute('SELECT %s FROM %s' % (','.join(columns), table))
			for row in self.cur.fetchall():
				values = []
				for value in row:
					if value == None:
						value = 'null'
					else:
						value = str(self.conn.escape(value))
					values.append(value)
				insert = 'INSERT INTO %s (%s) VALUES(%s)' % (table, ','.join(columns), ','.join(values))
				fd.write(insert + ';\n')

	def selectdb(self, db):

		if self.engine == 'mysqli':
			self.cur.execute('USE %s' % db)

		elif self.engine == 'pgsql':
			if self.cur:
				self.cur.close()
			if self.conn:
				self.conn.close()

			self.conn = bpgsql.connect(
				host=str(self.options['host']),
				port=str(self.options['port']),
				username=str(self.options['user']),
				password=str(self.options['passwd']),
				dbname=str(db)
			)
			self.cur = self.conn.cursor()

	def tables(self):

		tables = []

		if self.engine == 'mysqli':
			self.cur.execute('SHOW TABLES')
			for row in self.cur.fetchall():
				tables.append(row[0])

		return tables
