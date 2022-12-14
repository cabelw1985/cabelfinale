# -*- coding: utf-8 -*-
"""
The local SQlite database module

Copyright 2017-2019, Leo Moll
SPDX-License-Identifier: MIT
"""

# pylint: disable=too-many-lines,line-too-long
import os
import time
import sqlite3
import resources.lib.mvutils as mvutils
import resources.lib.appContext as appContext
from resources.lib.storeQuery import StoreQuery


class StoreSQLite(StoreQuery):
    """
    The local SQlite database class

    """

    def __init__(self):
        super(StoreSQLite, self).__init__()
        self.logger = appContext.MVLOGGER.get_new_logger('StoreSQLite')
        self.notifier = appContext.MVNOTIFIER
        self.settings = appContext.MVSETTINGS
        self.databaseFilename = 'filmliste-v3.db'
        # internals
        self.conn = None
        self.dbfile = os.path.join(self.settings.getDatapath(), self.databaseFilename)
        self.logger.debug('StoreSQLite DBFile: {}', self.dbfile)

    def getConnection(self):
        if self.conn is None:
            if (not mvutils.file_exists(self.dbfile)):
                self.settings.setDatabaseStatus('UNINIT')
                self.logger.debug('Missing StoreSQLite DBFile: {}', self.dbfile)
            self.conn = sqlite3.connect(self.dbfile, timeout=60)
            self.conn.execute('pragma synchronous=off')
            self.conn.execute('pragma journal_mode=off')
            self.conn.execute('pragma page_size=16384')
            self.conn.execute('pragma encoding="UTF-8"')
        return self.conn

    def exit(self):
        if self.conn is not None:
            self.conn.commit()
            self.conn.close()
            self.conn = None

    def reset(self):
        mvutils.file_remove(self.dbfile)
        # last version
        mvutils.file_remove(os.path.join(self.settings.getDatapath(), 'filmliste-v2.db'))
        self.conn = None

    # ABSTRACT
    def getDatabaseStatus(self):
        updateStatus = {
            'lastUpdate': self.settings.getLastUpdate(),
            'status': self.settings.getDatabaseStatus(),
            'lastFullUpdate': self.settings.getLastFullUpdate(),
            'version': self.settings.getDatabaseVersion()
        }
        return updateStatus
