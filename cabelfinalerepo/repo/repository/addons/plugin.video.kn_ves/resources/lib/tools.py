#!/usr/bin/python

import json
import re
import time

import xbmc
import xbmcgui
import xbmcaddon
import xbmcvfs

from contextlib import contextmanager

ADDON = xbmcaddon.Addon(id='plugin.video.kn_ves')
ADDON_NAME = ADDON.getAddonInfo('name')
ID = ADDON.getAddonInfo('id')
VERSION = ADDON.getAddonInfo('version')
PATH = xbmcvfs.translatePath(ADDON.getAddonInfo('path'))
PROFILE = xbmcvfs.translatePath(ADDON.getAddonInfo('profile'))
LS = ADDON.getLocalizedString

# Constants

STRING = 0
BOOL = 1
NUM = 2


def writeLog(message, level=xbmc.LOGDEBUG):
    xbmc.log('[%s %s] %s' % (ID, VERSION, message), level)


def notify(header, message, icon=xbmcgui.NOTIFICATION_INFO, dispTime=5000):
    xbmcgui.Dialog().notification(header, message, icon=icon, time=dispTime)


def dialogOK(header, message):
    xbmcgui.Dialog().ok(header, message)


def dialogYesNo(header, message):
    return xbmcgui.Dialog().yesno(header, message)


def jsonrpc(query):
    querystring = {"jsonrpc": "2.0", "id": 1}
    querystring.update(query)
    try:
        response = json.loads(xbmc.executeJSONRPC(json.dumps(querystring)))
        if 'result' in response: return response['result']
    except TypeError as e:
        writeLog('Error executing JSON RPC: {}'.format(e), xbmc.LOGFATAL)
    return None


def strToBool(par):
    return True if par.upper() == 'TRUE' else False


def getAddonSetting(setting, sType=STRING, multiplicator=1):
    if sType == BOOL:
        return strToBool(ADDON.getSetting(setting))
    elif sType == NUM:
        try:
            return int(re.match('\d+', ADDON.getSetting(setting)).group()) * multiplicator
        except AttributeError:
            return 0
    else:
        return ADDON.getSetting(setting)


def setAddonSetting(setting, value, sType=STRING):
    if sType == BOOL:
        ADDON.setSetting(setting, str(value).lower())
    else:
        ADDON.setSetting(setting, str(value))


@contextmanager
def busy_dialog():
    xbmc.executebuiltin('ActivateWindow(busydialognocancel)')
    try:
        yield
    finally:
        xbmc.executebuiltin('Dialog.Close(busydialognocancel)')

def str2datetime(sDateTime, sFormat):
    try:
        return time.strptime(sDateTime, sFormat)
    except (ImportError, ValueError,) as e:
        writeLog(str(e))
        return False

def datetime2str(sDatetime, sFormat):
    try:
        return time.strftime(sFormat, sDatetime)
    except ValueError as e:
        writeLog(str(e))
        return False
