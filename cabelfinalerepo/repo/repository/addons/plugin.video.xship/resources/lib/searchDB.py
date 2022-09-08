# -*- coding: UTF-8 -*-

#2021-02-18

import sys
from os import path, stat
from sqlite3 import Error as sqlError
from sqlite3 import dbapi2 as db

from xbmcvfs import mkdir, exists

from resources.lib import control
from resources.lib.control import py2_decode, quote_plus

if not exists(control.dataPath): mkdir(control.dataPath)

# DB für Suche
searchDB = path.join(control.dataPath, 'search.db')

def _get_connection(filename):
    conn = db.connect(filename)
    conn.row_factory = _dict_factory
    return conn

def _dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

#conn = db.connect(searchDB) # tulpe
# conn = _get_connection(searchDB) # dict

# einmalig Tabellen in der DB anlegen wenn die Dateigröße von der Datenbank Datei 0 ist
if not exists(searchDB) or  stat(searchDB).st_size == 0:# size DB
    conn = _get_connection(searchDB)  # dict
    try:
        cursor = conn.cursor()
        tables = ['movies','tvshows', 'person']
        for t in tables:
            sql = 'CREATE TABLE IF NOT EXISTS %s (ID Integer PRIMARY KEY AUTOINCREMENT, term)' % t
            cursor.execute(sql)
        cursor.close()
    except sqlError as e:
        print (e)   # test
    except Exception as e:
        print (e)   # test
    finally:
        if not (conn is None):
            conn.close()

def getSearchTerms(table):
    conn = _get_connection(searchDB)  # dict
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM %s ORDER BY ID DESC" % table)
    matched = cursor.fetchall()
    cursor.close()
    conn.close()
    return matched

def insertSearchTerm(table, term):
    conn = _get_connection(searchDB)  # dict
    cursor = conn.cursor()
    cursor.execute("INSERT INTO %s VALUES (?,?)" % table, (None, py2_decode(term)))
    conn.commit()
    cursor.close()
    conn.close()

def delSearchTerm(table, term):
    conn = _get_connection(searchDB)  # dict
    cursor = conn.cursor()
    cursor.execute("DELETE FROM %s WHERE term = '%s'" % (table, term))
    conn.commit()
    cursor.close()
    conn.close()

def clearSearch(table=None):
    conn = _get_connection(searchDB)  # dict
    cursor = conn.cursor()
    try:
        if table is None: tables = ['tvshows', 'movies', 'person']
        else: tables = [table]
        for t in tables:
            cursor.execute("DROP TABLE IF EXISTS %s" % t)
            cursor.execute("VACUUM")
            cursor.execute("CREATE TABLE IF NOT EXISTS %s (ID Integer PRIMARY KEY AUTOINCREMENT, term)" % t)
            #conn.commit() # ist nicht notwendig
        cursor.close()
    except:
        pass
    finally:
        if not (conn is None):
            conn.close()

def search_new(table): # 'movies','tvshows', 'person'
    k = control.keyboard('', "Suche")
    k.doModal()
    term = k.getText() if k.isConfirmed() else None
    if term is None or term == '': return
    term = term.strip()
    insertSearchTerm(table, term)
    url = '%s?action=%s&page=1&query=%s' % (sys.argv[0], table, quote_plus(term))
    control.execute('Container.Update(%s)' % url)

def search_clear(table):
    clearSearch(table)
    url = '%s?action=%sSearch' % (sys.argv[0], table)
    control.execute('Container.Update(%s)' % url)

def search_del_term(table, term):
    delSearchTerm(table, term)
    url = '%s?action=%sSearch' % (sys.argv[0], table)
    control.execute('Container.Update(%s)' % url)

