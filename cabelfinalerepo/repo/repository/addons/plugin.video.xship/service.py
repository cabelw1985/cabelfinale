# -*- coding: UTF-8 -*-

#2022-01-14

import os, time, sys, hashlib
import json, re
import xbmc, xbmcgui, xbmcaddon, xbmcvfs
from xbmc import LOGDEBUG, LOGERROR
from resources.lib import updateManager

Addon = xbmcaddon.Addon()
AddonName = Addon.getAddonInfo('name')
getSetting = Addon.getSetting

currentTime = int(time.time())

if sys.version_info[0] == 2:
    from xbmc import LOGNOTICE as LOGINFO
    from xbmc import translatePath
    profilePath = translatePath(Addon.getAddonInfo('profile')).decode('utf-8')
    ADDON_DATA_DIR = translatePath(os.path.join('special://home/userdata/addon_data', '%s')).decode('utf-8')  # plugin_id
    ADDON_PATH = translatePath(os.path.join('special://home/addons/', '%s')).decode('utf-8')
    thumbnails = translatePath('special://thumbnails').decode('utf-8')
    dbpath = translatePath("special://database/Textures13.db").decode('utf-8')
    dir_packages = translatePath('special://home/addons/packages/').decode('utf-8')
else:
    from xbmc import LOGINFO
    from xbmcvfs import translatePath
    profilePath = translatePath(Addon.getAddonInfo('profile'))
    ADDON_DATA_DIR = translatePath(os.path.join('special://home/userdata/addon_data', '%s'))
    ADDON_PATH = translatePath(os.path.join('special://home/addons/', '%s'))
    thumbnails = translatePath('special://thumbnails')
    dbpath = translatePath("special://database/Textures13.db")
    dir_packages = translatePath('special://home/addons/packages/')

NIGHTLY_VERSION_CONTROL = os.path.join(profilePath, "update_sha")
PROFIL_RELOAD = os.path.join(profilePath, "profil_reload")
INSTALL_CONTROL = os.path.join(profilePath, "addons_installed")
ADDON_XML_FILE = os.path.join(ADDON_PATH % Addon.getAddonInfo('id'), "addon.xml")
MD5_FILE = ADDON_XML_FILE

isdebug = True if getSetting('status.debug') == 'true' else False
if isdebug: from resources.lib import log_utils, control

if int(xbmc.getInfoLabel("System.BuildVersion").split(".")[0]) >= 18:
    def idle():
        return xbmc.executebuiltin('Dialog.Close(busydialognocancel)')
    def busy():
        return xbmc.executebuiltin('ActivateWindow(busydialognocancel)')
else:
    def idle():
        return xbmc.executebuiltin('Dialog.Close(busydialog)')
    def busy():
        return xbmc.executebuiltin('ActivateWindow(busydialog)')

STATUS = 0

# ------------ edit ------------------
ADDONS = []

silent=True

def plugin_video_xship(ADDONID):
    username = 'watchone'
    plugin_id = ADDONID
    branch = 'master'
    token = Addon.getSetting('update.token')
    if token == '':
        Addon.setSetting('update.Addon', 'false')
        return True
    status = updateManager.Update(username, plugin_id, branch, token, silent)
    if token == 'Z2hwX2Y2am9TYlJnWVRMSHJRYWlRd0ZJTlNxVUIxUEVpdjNlQ1RLTg==' or token == '':
        Addon.setSetting('update.token', '')
        Addon.setSetting('update.Addon', 'false')
        status = True
    return status

def script_module_resolveurl(ADDONID):
    username = 'jsergio123'
    plugin_id = ADDONID
    branch = 'master'
    token = ''
    #return updateManager.Update(username, plugin_id, branch, token, silent)
    return True
# ------------------------------------

def md5(fname):
    hash_md5 = hashlib.md5()
    with open(fname, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def infoDialog(message, heading=AddonName, icon='', time=5000, sound=False):
    if icon == '': icon = Addon.getAddonInfo('icon')
    elif icon == 'INFO': icon = xbmcgui.NOTIFICATION_INFO
    elif icon == 'WARNING': icon = xbmcgui.NOTIFICATION_WARNING
    elif icon == 'ERROR': icon = xbmcgui.NOTIFICATION_ERROR
    xbmcgui.Dialog().notification(heading, message, icon, time, sound=sound)

def _status(status):
    global STATUS
    #print(STATUS)
    if status == False: status = 2
    elif status == True: status = 1
    else: status = 0 #None
    if status > STATUS: STATUS = status
    # print(STATUS)

def enableAddon(ADDONID):
    struktur = json.loads(xbmc.executeJSONRPC('{"jsonrpc":"2.0","method":"Addons.GetAddonDetails","id":1,"params": {"addonid":"%s", "properties": ["enabled"]}}' % ADDONID))
    if 'error' in struktur or struktur["result"]["addon"]["enabled"] != True:
        count = 0
        while True:
            if count == 5: break
            count += 1
            xbmc.executebuiltin('EnableAddon(%s)' % (ADDONID))
            xbmc.executebuiltin('SendClick(11)')
            xbmc.executeJSONRPC('{"jsonrpc":"2.0","method":"Addons.SetAddonEnabled","id":1,"params":{"addonid":"%s", "enabled":true}}' % ADDONID)
            xbmc.sleep(500)
            try:
                struktur = json.loads(xbmc.executeJSONRPC('{"jsonrpc":"2.0","method":"Addons.GetAddonDetails","id":1,"params": {"addonid":"%s", "properties": ["enabled"]}}' % ADDONID))
                if struktur["result"]["addon"]["enabled"] == True: break
            except:
                pass

def checkDependence(ADDONID):
    if isdebug: log_utils.log(__name__ + ' - %s - checkDependence ' % ADDONID, log_utils.LOGINFO)
    try:
        addon_xml = os.path.join(ADDON_PATH % ADDONID, 'addon.xml')
        with open(addon_xml, 'rb') as f:
            xml = f.read()
        pattern = '(import.*?addon[^/]+)'
        allDependence = re.findall(pattern, str(xml))
        #if isdebug: log_utils.log(__name__ + '%s - allDependence ' % str(allDependence), log_utils.LOGINFO)
        for i in allDependence:
            try:
                if 'optional' in i or 'xbmc.python' in i: continue
                pattern = 'import.*?"([^"]+)'
                IDdoADDON = re.search(pattern, i).group(1)
                if os.path.exists(ADDON_PATH % IDdoADDON) == True and Addon.getSetting('update.enforceUpdate') != 'true':
                    enableAddon(IDdoADDON)
                else:
                    xbmc.executebuiltin('InstallAddon(%s)' % (IDdoADDON))
                    xbmc.executebuiltin('SendClick(11)')
                    enableAddon(IDdoADDON)
            except:
                pass
    except Exception as e:
        xbmc.log(__name__ + '  %s - Exception ' % e, LOGERROR)

def reload_profile(makefile=True):
    if isdebug: log_utils.log(__name__ + ' - Start reload_profile()', log_utils.LOGINFO)
    busy()
    if makefile:
        open(PROFIL_RELOAD, "w+").write('Profil reload')
        #xbmc.sleep(100)
    profil=xbmc.getInfoLabel('System.ProfileName')
    xbmc.sleep(500)
    #if profil:
    xbmc.executebuiltin('LoadProfile('+profil+',prompt)')
    idle()

# Wartung
def check_del():
    dayfornextcheck = int(Addon.getSetting('service.dayfornextcheck'))
    enforceRefresh = Addon.getSetting('service.enforceRefresh')
    try:
        if enforceRefresh == 'true':
            Addon.setSetting('service.old_dayfornextcheck', str(dayfornextcheck))
            # Addon.setSetting('service.enforceRefresh', 'false')
            _del_thumbnails(dayfornextcheck)
            _del_more()
            Addon.setSetting('service.enforceRefresh', 'false')
            return

        old_dayfornextcheck = int(Addon.getSetting('service.old_dayfornextcheck'))
        if dayfornextcheck != old_dayfornextcheck:
            Addon.setSetting('service.old_dayfornextcheck', str(dayfornextcheck))
            _del_thumbnails(dayfornextcheck)
            return

        nextcheck = int(Addon.getSetting('service.nextcheck'))
        currentTime = int(time.time())
        if currentTime >= nextcheck:
            _del_more()
            _del_thumbnails(dayfornextcheck)
            return
    except:
        Addon.setSetting('service.old_dayfornextcheck', str(dayfornextcheck))
        # _del_more()
        # _del_thumbnails(dayfornextcheck)

def _del_thumbnails(dayfornextcheck): #    """kodi texture cache / thumbnails - del images"""
    import sqlite3
    connection = sqlite3.connect(dbpath, timeout=30, isolation_level=None)
    try:
        cache_images = connection.execute('SELECT cachedurl FROM texture').fetchall()
        if cache_images:
            for cache_image in cache_images:
                if xbmcvfs.exists(thumbnails + cache_image[0]):
                    xbmcvfs.delete(thumbnails + cache_image[0])

        connection.execute('DELETE FROM texture')
        connection.close()

        nextcheck = str(int(time.time()) + 60*60*24*dayfornextcheck)
        Addon.setSetting(id='service.nextcheck', value=nextcheck) # sek min stunden, tage

        infoDialog("Thumbnails und File Cache gelöscht", sound=False, icon='INFO', time=2000)
    except Exception as e:
        pass
        #log_exception(__name__, e)
    finally:
        del connection

def _del_more():
    dirs,files = xbmcvfs.listdir(dir_packages) # addons\packages
    for file in files: xbmcvfs.delete(dir_packages + file)

    cachePath = os.path.join(profilePath, 'htmlcache')
    if xbmcvfs.exists(cachePath):
        dirs, files = xbmcvfs.listdir(cachePath)
        for file in files: xbmcvfs.delete(cachePath + file)

def run():
    if isdebug: log_utils.log(__name__ + ' - Start run()', log_utils.LOGINFO)
    # check_addons = None
    #
    # if os.path.isfile(INSTALL_CONTROL) == False: check_addons = True

    # if check_addons != True:
    #     for ADDONID in ADDONS:
    #         if os.path.isdir(ADDON_PATH % ADDONID) == False: check_addons = True

    # if check_addons != True:
    #     for ADDONID in ADDONS:
    #         try:
    #             struktur = json.loads(xbmc.executeJSONRPC('{"jsonrpc":"2.0","method":"Addons.GetAddonDetails","id":1,"params": {"addonid":"%s", "properties": ["enabled"]}}' % ADDONID))
    #             if struktur["result"]["addon"]["enabled"] != True:
    #                 check_addons = True
    #         except:
    #             check_addons = True
    #             pass

    # if check_addons == True:
    #     infoDialog("Überprüfe Installation", sound=False, icon='INFO', time=10000)
    # else:

    infoDialog("Suche Updates", sound=False, icon='INFO', time=10000)

    for ADDONID in ADDONS:
        if Addon.getSetting('update.enforceUpdate') == 'true':
            LOCAL_PLUGIN_VERSION = os.path.join(ADDON_DATA_DIR % ADDONID, "update_sha")
            if os.path.exists(LOCAL_PLUGIN_VERSION): os.remove(LOCAL_PLUGIN_VERSION)

        cmd = ADDONID.replace('.', '_') + '("' + ADDONID + '")'
        status = eval(cmd)
        checkDependence(ADDONID)
        enableAddon(ADDONID)
        _status(status)

    # if check_addons == True:
    #     if STATUS <= 1:
    #         if not xbmcvfs.exists(profilePath): xbmcvfs.mkdir(profilePath)
    #         open(INSTALL_CONTROL, "w+").write('Addons sind installiert')
    #         xbmc.sleep(500)
    #         infoDialog("Vorgang ist abgeschlossen", sound=False, icon='INFO', time=1000)
    #         if Addon.getSetting('update.enforceUpdate') == 'true': Addon.setSetting('update.enforceUpdate', 'false')
    #         if Addon.getSetting('service.reloadProfil') == 'true' and Addon.getSetting('service.md5') != md5(MD5_FILE):
    #             Addon.setSetting('service.md5', md5(MD5_FILE))
    #             reload_profile()
    #     else:
    #         infoDialog("Vorgang mit Fehler beendet", sound=True, icon='ERROR')
    #
    # else:

    if STATUS == 0: infoDialog("Keine neuen Updates gefunden", sound=False, icon='INFO', time=3000)
    elif STATUS == 1:
        infoDialog("Vorgang erfolgreich abgeschlossen", sound=False, icon='INFO', time=1000)
        if Addon.getSetting('update.enforceUpdate') == 'true': Addon.setSetting('update.enforceUpdate', 'false')
        # if Addon.getSetting('service.reloadProfil') == 'true' and Addon.getSetting('service.md5') != md5(MD5_FILE):
        #     Addon.setSetting('service.md5', str(os.path.getsize(MD5_FILE)))
        #     reload_profile()
    else:  infoDialog("Auto Update mit Fehler beendet", sound=True, icon='ERROR')


# Main
try:
    busy()
    ## kodi17 - set Hdfilme on
    #if int(xbmc.getInfoLabel("System.BuildVersion").split(".")[0]) == 17:
    #    Addon.setSetting('provider.hdfilme', 'true')

    # check reload
    if os.path.isfile(PROFIL_RELOAD):
        for ADDONID in ADDONS:
            enableAddon(ADDONID)
        os.remove(PROFIL_RELOAD)
        if Addon.getSetting('update.enforceUpdate') == 'true': Addon.setSetting('update.enforceUpdate', 'false')

    # Do check for Updates
    else:
        # save old md5
        Addon.setSetting('service.md5', md5(MD5_FILE))

        # Update Resolver on/off
        if os.path.exists(ADDON_PATH % 'plugin.video.xstream'):
            try:
                struktur = json.loads(xbmc.executeJSONRPC('{"jsonrpc":"2.0","method":"Addons.GetAddonDetails","id":1,"params": {"addonid":"plugin.video.xstream", "properties": ["enabled"]}}'))
                if struktur["result"]["addon"]["enabled"] and xbmcaddon.Addon('plugin.video.xstream').getSetting('githubUpdateResolver') == 'true':
                    Addon.setSetting('update.Resolver', 'false')
                else:
                    Addon.setSetting('update.Resolver', 'true')
            except:
                if Addon.getSetting('update.Resolver') != 'true': Addon.setSetting('update.Resolver', 'true')
        else:
            if Addon.getSetting('update.Resolver') != 'true': Addon.setSetting('update.Resolver', 'true')

        if getSetting('update.Resolver') == 'true': ADDONS.append('script.module.resolveurl')
        if getSetting('update.Addon') == 'true': ADDONS.append(Addon.getAddonInfo('id'))
        # if getSetting('update.MediathekViewWeb') == 'true': ADDONS.append('plugin.video.mediathekviewweb')
        if os.path.isfile(NIGHTLY_VERSION_CONTROL) == False:
            run()
        elif Addon.getSetting('service.autoupdate') == 'true'or Addon.getSetting('update.enforceUpdate') == 'true':
            try: old_nextupdateday = int(Addon.getSetting('service.old_nextupdateday'))
            except: old_nextupdateday = int(Addon.getSetting('service.nextupdateday'))
            if Addon.getSetting('service.check_del') == 'true' or Addon.getSetting('service.enforceRefresh') == 'true':
                check_del()
                if isdebug: log_utils.log(__name__ + ' - Ende  check_del()', log_utils.LOGINFO)
            if currentTime >= int(Addon.getSetting('service.nextupdate')) or \
                    old_nextupdateday != int(Addon.getSetting('service.nextupdateday')) or \
                    Addon.getSetting('update.enforceUpdate') == 'true':

                run()
                if isdebug: log_utils.log(__name__ + ' - Ende  run()', log_utils.LOGINFO)
                nextupdate = currentTime + 60 * 60 * 24 * int(Addon.getSetting('service.nextupdateday'))
                Addon.setSetting('service.nextupdate', str(nextupdate))
                Addon.setSetting('service.old_nextupdateday', Addon.getSetting('service.nextupdateday'))
    if isdebug: log_utils.log(__name__ + ' - run idle()', log_utils.LOGINFO)
    idle()
    #sys.exit()
except Exception as e:
    #if isdebug: log_utils.log(__name__ + ' - %s - Exception ' % e, log_utils.LOGERROR)
    xbmc.log(__name__ + ' Ende:  %s - Exception ' % e, LOGERROR)
    idle()
    #sys.exit()

