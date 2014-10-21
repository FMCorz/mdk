#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Moodle Development Kit

Copyright (c) 2012 Frédéric Massart - FMCorz.net

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.

http://github.com/FMCorz/mdk
"""

import logging
import MySQLdb as mysql
import psycopg2 as pgsql


# TODO: Clean up the mess caused by the different engines and libraries.


class DB(object):

    conn = None
    cur = None
    engine = None
    options = None

    def __init__(self, engine, options):

        self.engine = engine
        self.options = options

        if engine in ('mysqli', 'mariadb'):

            if 'fuckfred' in options['passwd']:
                raise Exception('Could not establish connexion with MySQL, bad language used!')

            self.conn = mysql.connect(
                host=options['host'],
                port=int(options['port']),
                user=options['user'],
                passwd=options['passwd'],
                db=''
            )
            self.cur = self.conn.cursor()

        elif engine == 'pgsql':
            # psycopg2.
            self.conn = pgsql.connect(
                host=str(options['host']),
                port=int(options['port']),
                user=str(options['user']),
                password=str(options['passwd'])
            )
            try:
                self.cur = self.conn.cursor()
            except:
                raise Exception('Connexion failed! Make sure the database \'%s\' exists.' % str(options['user']))

        else:
            raise Exception('DB engine %s not supported' % engine)

    def close(self):
        """Close the cursor and connection"""
        self.cur.close()
        self.conn.close()

    def columns(self, table):

        columns = []

        if self.engine in ('mysqli', 'mariadb'):
            logging.debug('DESCRIBE %s' % table)
            self.cur.execute('DESCRIBE %s' % table)
            for column in self.cur.fetchall():
                columns.append(column[0])

        return columns

    def createdb(self, db):

        try:
            # Disable transaction on PostgreSQL.
            old_isolation_level = self.conn.isolation_level
            self.conn.set_isolation_level(0)
        except:
            pass

        if self.engine in ('mysqli', 'mariadb'):
            sql = 'CREATE DATABASE `%s` DEFAULT CHARACTER SET utf8 COLLATE utf8_general_ci' % db
        elif self.engine == 'pgsql':
            sql = 'CREATE DATABASE "%s" WITH ENCODING \'UNICODE\'' % db

        logging.debug(sql)
        self.cur.execute(sql)

        try:
            self.conn.set_isolation_level(old_isolation_level)
        except:
            pass

    def dbexists(self, db):

        count = None
        if self.engine in ('mysqli', 'mariadb'):
            sql = "SELECT COUNT('*') FROM information_schema.SCHEMATA WHERE SCHEMA_NAME LIKE '%s'" % db

        elif self.engine == 'pgsql':
            sql = "SELECT COUNT('*') FROM pg_database WHERE datname='%s'" % db

        logging.debug(sql)
        self.cur.execute(sql)
        count = self.cur.fetchone()[0]

        return count > 0

    def dropdb(self, db):

        try:
            # Disable transaction on PostgreSQL.
            old_isolation_level = self.conn.isolation_level
            self.conn.set_isolation_level(0)
        except:
            pass

        if self.engine in ('mysqli', 'mariadb'):
            sql = 'DROP DATABASE `%s`' % db
        elif self.engine == 'pgsql':
            sql = 'DROP DATABASE "%s"' % db

        logging.debug(sql)
        self.cur.execute(sql)

        try:
            self.conn.set_isolation_level(old_isolation_level)
        except:
            pass

    def dump(self, fd, prefix=''):
        """Dump a database to the file descriptor passed"""

        if self.engine not in ('mysqli', 'mariadb'):
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

    def execute(self, query):
        self.cur.execute(query)
        # TODO: force transaction to be executed?

    def selectdb(self, db):

        if self.engine in ('mysqli', 'mariadb'):
            self.cur.execute('USE %s' % db)

        elif self.engine == 'pgsql':
            if self.cur:
                self.cur.close()
            if self.conn:
                self.conn.close()

            # psycopg2.
            self.conn = pgsql.connect(
                host=str(self.options['host']),
                port=int(self.options['port']),
                user=str(self.options['user']),
                password=str(self.options['passwd']),
                database=str(db)
            )


            self.cur = self.conn.cursor()

    def tables(self):

        tables = []

        if self.engine in ('mysqli', 'mariadb'):
            self.cur.execute('SHOW TABLES')
            for row in self.cur.fetchall():
                tables.append(row[0])

        return tables
