# -*- coding: utf-8 -*-
#
# hls.py by Loki (Hls Cache) - new for openscrapers by ka 
#2020-08-25

from __future__ import print_function
import os, sys, requests
import json, time
from resources.lib import workers
import xbmc, xbmcgui, xbmcaddon, xbmcvfs
from requests.packages.urllib3.exceptions import InsecureRequestWarning

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

__addon_handle__ = int(sys.argv[1])


# hier anpassen!
# ---------------
dialog = 'on'  # on / off
__addon__ = xbmcaddon.Addon()
__addon_id__ = __addon__.getAddonInfo('id')

def setWebSrv(ADDONID):
    while True:
        xbmc.executeJSONRPC(
            '{"jsonrpc":"2.0", "method":"Settings.SetSettingValue", "params":{"setting":"services.webskin", "value":"%s"}, "id":1}' % ADDONID)
        struktur = json.loads(xbmc.executeJSONRPC(
            '{"jsonrpc":"2.0","method":"Settings.GetSettingValue","params":{"setting":"services.webskin"},"id":1}'))
        try:
            if struktur["result"]["value"] == ADDONID:
                break
            else:
                xbmc.sleep(1000)
        except:
            pass

def clear_dir(dir_path):
    try:
        for name in xbmcvfs.listdir(dir_path)[1]:
            path = os.path.join(dir_path, name)
            xbmcvfs.delete(path)
    except:
        pass

m3u8_timeout = int(10)
m3u8_segment_timeout = int(5)

if __addon__.getSetting('hlscache.enabled') == '1':
    cache_path = xbmc.translatePath('special://home/addons/%s/cache') % __addon_id__
    new_m3u8_file = xbmc.translatePath('special://home/addons/%s/cache/hls.m3u8') % __addon_id__
    if not os.path.isdir(cache_path): xbmcvfs.mkdir(cache_path)
    ip = __addon__.getSetting('hlscache.ip')
    if not ip:
        ip = xbmc.getIPAddress()
        __addon__.setSetting('hlscache.ip', ip)
    port = __addon__.getSetting('hlscache.port')

    currentWebSrv = json.loads(xbmc.executeJSONRPC(
        '{"jsonrpc":"2.0","method":"Settings.GetSettingValue","params":{"setting":"services.webskin"},"id":1}'))[
        "result"]["value"]
    if currentWebSrv != __addon_id__:
        setWebSrv(__addon_id__)

else:
    cache_path = xbmc.translatePath(__addon__.getSetting('hlscache.nfs_path'))
    new_m3u8_file =  os.path.join(cache_path, 'hls.m3u8')

sess = requests.Session()

#-------------------------------------------------


def cache_loader(m3u8_url, m3u8_headers={''}, segment_headers={''}):

    clear_dir(cache_path)

    req = sess.get(url=m3u8_url, stream=False, allow_redirects=True, verify=False, timeout=m3u8_timeout,
                   headers=m3u8_headers)
    if req.status_code == 200:
        try:
            data = ''
            count = 0
            for line in req.iter_lines():
                line = line.strip()
                if line:
                    if line.startswith('http'):
                        if __addon__.getSetting('hlscache.enabled') == '1':
                            data = data + ('{0}\n'.format('http://' + ip + ':' + port + '/cache/' + str(count)))
                        else:
                            data = data + ('{0}\n'.format(os.path.join(__addon__.getSetting('hlscache.extWebSrv'), str(count))))
                        count += 1
                    else:
                        data = data + ('{0}\n'.format(line))

            m3u8 = xbmcvfs.File(new_m3u8_file, 'w')
            m3u8.write(data)
            m3u8.close()

            t = workers.Thread(thread_cache_loader, req, segment_headers)
            t.start()

        except Exception as e:
            print(e)


def thread_cache_loader(req, segment_headers):
    if xbmcvfs.exists(new_m3u8_file) == 1:
        # starte webserver
        if __addon__.getSetting('hlscache.enabled') == '1':
            xbmc.startServer(iTyp=xbmc.SERVER_WEBSERVER, bStart=True, bWait=False)

        min_diff = float(90)
        max_runtime = float(0)

        count = 0
        start_time = time.time()

        try:
            for line in req.iter_lines():
                line = line.strip()
                if line:

                    if line.startswith('http'):
                        try:
                            req = sess.get(url=line, stream=True, allow_redirects=True, verify=False,
                                           timeout=m3u8_segment_timeout, headers=segment_headers)
                            if req.status_code == 200:

                                fi = xbmcvfs.File(os.path.join(cache_path, str(count)), 'w')
                                fi.write(req.content)
                                fi.close()

                        except Exception as e:
                            print(e)
                            pass

                        count += 1
                        xbmc.sleep(100)

                if 10 == count: xbmc.sleep(5000) # Verzögerung f. "von Anfang abspielen"
                if not xbmc.Player().isPlaying() and count >= 10: break

            req.close()


            while True:
                if not xbmc.Player().isPlaying():
                    clear_dir(cache_path)

                    if __addon__.getSetting('hlscache.enabled') == '1':
                        xbmc.startServer(iTyp=xbmc.SERVER_WEBSERVER, bStart=False, bWait=False)
                        if json.loads(xbmc.executeJSONRPC(
                                '{"jsonrpc":"2.0","method":"Settings.GetSettingValue","params":{"setting":"services.webskin"},"id":1}'))["result"]["value"] != currentWebSrv:
                            setWebSrv(currentWebSrv)
                    break
                else:
                    xbmc.sleep(1500)

        except Exception as e:
            if dialog == 'on':
                xbmcgui.Dialog().ok('[COLOR red]CACHE LOARDER ERROR[/COLOR]', str(e))
            print(str(e))
            clear_dir(cache_path)

            if __addon__.getSetting('hlscache.enabled') == '1':
                xbmc.startServer(iTyp=xbmc.SERVER_WEBSERVER, bStart=False, bWait=False)
                if json.loads(xbmc.executeJSONRPC(
                        '{"jsonrpc":"2.0","method":"Settings.GetSettingValue","params":{"setting":"services.webskin"},"id":1}'))[
                    "result"]["value"] != currentWebSrv:
                    setWebSrv(currentWebSrv)

    else:
        return
