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

import abc
from contextlib import contextmanager
import logging
from io import IOBase
from typing import Any, Dict, List

from mdk.tools import process


def get_dbo_from_profile(profile: Dict[str, Any]) -> 'Database':
    engine = profile.get('engine', 'unknown')
    if 'dockername' in profile:
        if engine == 'pgsql':
            return PgSQLDocker(profile['dockername'])
    elif engine == 'pgsql':
        return PgSQLCursor(profile['host'], profile['port'], profile['user'], profile['passwd'])
    elif engine == 'mariadb':
        return MariaDBCursor(profile['host'], profile['port'], profile['user'], profile['passwd'])
    elif engine == 'mysqli':
        return MySQLCursor(profile['host'], profile['port'], profile['user'], profile['passwd'])
    elif engine == 'sqlsrv':
        return SQLServerCursor(profile['host'], profile['port'], profile['user'], profile['passwd'])
    raise ValueError(f"Unsupported engine '{engine}'")


class Database(abc.ABC):

    @abc.abstractmethod
    def createdb(self, dbname, **options):
        pass

    @abc.abstractmethod
    def dropdb(self, dbname):
        pass

    @abc.abstractmethod
    def dbexists(self, dbname) -> bool:
        pass

    @abc.abstractmethod
    def dump(self, dbname, fd):
        pass


class MySQLCursor(Database):

    _host: str
    _port: int
    _user: str
    _passwd: str

    def __init__(self, host, port, user, passwd):
        self._host = str(host)
        self._port = int(port)
        self._user = str(user)
        self._passwd = str(passwd)

    @contextmanager
    def cursor(self):
        import MySQLdb as mysql
        conn = mysql.connect(host=self._host, port=self._port, user=self._user, passwd=self._passwd, db='')
        cursor = conn.cursor()
        yield cursor
        cursor.close()
        conn.close()

    def createdb(self, dbname, **options):
        with self.cursor() as cursor:
            charset = 'utf8mb4' if 'charset' not in options else options['charset']
            collate = 'utf8mb4_unicode_ci' if charset == 'utf8mb4' else 'utf8_unicode_ci'
            sql = f'CREATE DATABASE `{dbname}` CHARACTER SET {charset} COLLATE {collate}'
            logging.debug(sql)
            cursor.execute(sql)

    def dropdb(self, dbname):
        with self.cursor() as cursor:
            sql = f'DROP DATABASE `{dbname}`'
            logging.debug(sql)
            cursor.execute(sql)

    def dbexists(self, dbname):
        with self.cursor() as cursor:
            sql = f"SELECT 1 FROM information_schema.SCHEMATA WHERE SCHEMA_NAME LIKE '{dbname}'"
            logging.debug(sql)
            cursor.execute(sql)
            return cursor.fetchone() is not None

    def dump(self, dbname, fd):
        raise NotImplementedError('This method is not implemented, but it probably should be.')


class MariaDBCursor(MySQLCursor):
    pass


class PgSQLCursor(Database):

    _host: str
    _port: int
    _user: str
    _passwd: str

    def __init__(self, host, port, user, passwd):
        self._host = str(host)
        self._port = int(port)
        self._user = str(user)
        self._passwd = str(passwd)

    @contextmanager
    def cursor(self, autocommit=None):
        import psycopg2 as pgsql
        conn = pgsql.connect(host=self._host, port=self._port, user=self._user, password=self._passwd)
        if autocommit is not None:
            conn.set_session(autocommit=autocommit)
        try:
            cursor = conn.cursor()
            yield cursor
        except:
            raise Exception('Connection failed! Make sure the database \'%s\' exists.' % self._user)
        cursor.close()
        conn.close()

    def createdb(self, dbname, **options):
        with self.cursor(autocommit=True) as cursor:
            sql = f'CREATE DATABASE "{dbname}" WITH ENCODING \'UNICODE\''
            logging.debug(sql)
            cursor.execute(sql)

    def dropdb(self, dbname):
        with self.cursor(autocommit=True) as cursor:
            sql = f'DROP DATABASE IF EXISTS "{dbname}"'
            logging.debug(sql)
            cursor.execute(sql)

    def dbexists(self, dbname):
        with self.cursor() as cursor:
            sql = f"SELECT 1 FROM pg_database WHERE datname='{dbname}'"
            logging.debug(sql)
            cursor.execute(sql)
            return cursor.fetchone() is not None

    def dump(self, dbname, fd):
        raise NotImplementedError('This method is not implemented, but it probably should be.')


class PgSQLDocker(Database):

    def __init__(self, containername):
        self._name = containername

    def createdb(self, dbname, **options):
        self.exec(['createdb', dbname])

    def dropdb(self, dbname):
        self.exec(['dropdb', dbname])

    def dbexists(self, dbname):
        code, stdout, _ = self.exec(['psql', '-t', '-A', '-c', f"SELECT 1 FROM pg_database WHERE datname = '{dbname}'"])
        return code == 0 and stdout.strip() == "1"

    def dump(self, dbname, fd):
        self.exec(['pg_dump', '-d', dbname], stdout=fd)

    def exec(self, command: List[str], **kwargs):
        hostcommand = ['docker', 'exec', '-i', '-u', 'postgres', self._name, *command]
        return process(hostcommand, **kwargs)


class SQLServerCursor(Database):

    _host: str
    _port: int
    _user: str
    _passwd: str

    def __init__(self, host, port, user, passwd):
        self._host = str(host)
        self._port = int(port)
        self._user = str(user)
        self._passwd = str(passwd)

    @contextmanager
    def cursor(self, autocommit=True):
        import pyodbc

        # Look for installed ODBC Driver for SQL Server.
        drivers = pyodbc.drivers()
        sqlsrvdriver = next((driver for driver in drivers if "for SQL Server" in driver), None)
        if sqlsrvdriver is None:
            installurl = 'https://sqlchoice.azurewebsites.net/en-us/sql-server/developer-get-started/python'
            raise Exception("You need to install an ODBC Driver for SQL Server. Check out %s for more info." % installurl)

        logging.debug('Using %s' % sqlsrvdriver)

        connectionstr = f"DRIVER={sqlsrvdriver};SERVER={self._host};PORT={self._port};UID={self._user};PWD={self._passwd}"
        conn = pyodbc.connect(connectionstr)
        conn.autocommit = autocommit
        cursor = conn.cursor()
        yield cursor
        cursor.close()
        conn.close()

    def createdb(self, dbname, **options):
        with self.cursor(autocommit=False) as cursor:
            sql = 'CREATE DATABASE "%s" COLLATE Latin1_General_CS_AS;' \
                  'ALTER DATABASE "%s" SET ANSI_NULLS ON;' \
                  'ALTER DATABASE "%s" SET QUOTED_IDENTIFIER ON;' \
                  'ALTER DATABASE "%s" SET READ_COMMITTED_SNAPSHOT ON;' % (dbname, dbname, dbname, dbname)
            logging.debug(sql)
            cursor.execute(sql)

    def dropdb(self, dbname):
        with self.cursor(autocommit=False) as cursor:
            sql = f'DROP DATABASE "{dbname}"'
            logging.debug(sql)
            cursor.execute(sql)

    def dbexists(self, dbname):
        with self.cursor() as cursor:
            sql = f"SELECT COUNT('*') FROM master.dbo.sysdatabases WHERE name = '{dbname}'"
            logging.debug(sql)
            cursor.execute(sql)
            return cursor.fetchone()[0] > 0

    def dump(self, dbname, fd):
        raise NotImplementedError('This method is not implemented, but it probably should be.')


class DB(object):
    """
    .. deprecated:: 2.2 Use another class.
    """

    conn = None
    cur = None
    engine = None
    options = None

    def __init__(self, engine, options):

        self.engine = engine
        self.options = options

        if engine in ('mysqli', 'mariadb'):
            import MySQLdb as mysql

            if 'fuckfred' in options['passwd']:
                raise Exception('Could not establish connexion with MySQL, bad language used!')

            self.conn = mysql.connect(
                host=options['host'],
                port=int(options['port']),
                user=options['user'],
                passwd=options['passwd'],
                db='',
            )
            self.cur = self.conn.cursor()

        elif engine == 'pgsql':
            import psycopg2 as pgsql

            self.conn = pgsql.connect(
                host=str(options['host']),
                port=int(options['port']),
                user=str(options['user']),
                password=str(options['passwd']),
            )
            try:
                self.cur = self.conn.cursor()
            except:
                raise Exception('Connexion failed! Make sure the database \'%s\' exists.' % str(options['user']))

        elif engine == 'sqlsrv':
            import pyodbc

            host = str(options['host'])
            port = int(options['port'])
            user = str(options['user'])
            password = str(options['passwd'])

            # Look for installed ODBC Driver for SQL Server.
            drivers = pyodbc.drivers()
            sqlsrvdriver = next((driver for driver in drivers if "for SQL Server" in driver), None)
            if sqlsrvdriver is None:
                installurl = 'https://sqlchoice.azurewebsites.net/en-us/sql-server/developer-get-started/python'
                raise Exception("You need to install an ODBC Driver for SQL Server. Check out %s for more info." % installurl)

            logging.debug('Using %s' % sqlsrvdriver)

            connectionstr = "DRIVER=%s;SERVER=%s;PORT=%d;UID=%s;PWD=%s" \
                            % (sqlsrvdriver, host, port, user, password)
            self.conn = pyodbc.connect(connectionstr)
            self.conn.autocommit = True
            self.cur = self.conn.cursor()

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

            if 'charset' in self.options and self.options['charset'] == 'utf8mb4':
                placeholders = (db, 'utf8mb4', 'utf8mb4_unicode_ci')
            else:
                placeholders = (db, 'utf8', 'utf8_unicode_ci')

            sql = 'CREATE DATABASE `%s` CHARACTER SET %s COLLATE %s' % placeholders
        elif self.engine == 'pgsql':
            sql = 'CREATE DATABASE "%s" WITH ENCODING \'UNICODE\'' % db
        elif self.engine == 'sqlsrv':
            sql = 'CREATE DATABASE "%s" COLLATE Latin1_General_CS_AS;' \
                  'ALTER DATABASE "%s" SET ANSI_NULLS ON;' \
                  'ALTER DATABASE "%s" SET QUOTED_IDENTIFIER ON;' \
                  'ALTER DATABASE "%s" SET READ_COMMITTED_SNAPSHOT ON;' % (db, db, db, db)

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

        elif self.engine == 'sqlsrv':
            sql = "SELECT COUNT('*') FROM master.dbo.sysdatabases WHERE name = '%s'" % db

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
        elif self.engine in ('pgsql', 'sqlsrv'):
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
        if not isinstance(fd, IOBase):
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
            import psycopg2 as pgsql

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
