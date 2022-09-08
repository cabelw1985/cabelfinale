# -*- coding: UTF-8 -*-

#2021-11-22

import sys, re,  gzip
import hashlib,os,base64,codecs
from sqlite3 import dbapi2 as database
import xbmc, xbmcplugin
from resources.lib.control import py2_encode, is_python2, getKodiVersion
from resources.lib import log_utils, control, playcountDB

try:
    import xmlrpclib as _xmlrpclib
    from StringIO import StringIO
except:
    import xmlrpc.client as _xmlrpclib
    from io import StringIO
# eventuell zur späteren verwendung als meta
#_params = dict(parse_qsl(sys.argv[2].replace('?',''))) if len(sys.argv) > 1 else dict()

class player(xbmc.Player):
    def __init__(self, *args, **kwargs):
        xbmc.Player.__init__(self, *args, **kwargs)
        self.streamFinished = False
        self.totalTime = 0
        self.currentTime = 0
        self.playcount = 0
        self.watcher_control = False
        self.isdebug = True if control.getSetting('status.debug') == 'true' else False


    def run(self, title, url, meta):
        try:
            self.meta = meta
            self.mediatype = meta['mediatype']
            self.title = meta['title']
            self.year = str(meta['year']) if 'year' in meta else '0'
            self.name = control.quote_plus(title) + control.quote_plus(' (%s)' % meta['year']) if meta['mediatype'] == 'movie' else control.quote_plus(title) + control.quote_plus(
                ' S%02dE%02d' % (meta['season'], meta['episode']))
            self.name = control.unquote_plus(self.name)
            if control.is_python2 and type(self.name) != unicode:
                self.name = self.name.decode('utf-8')
            self.imdb = meta['imdb_id'] if 'imdb_id' in meta else None
            self.number_of_seasons = meta['number_of_seasons'] if 'number_of_seasons' in meta else None
            self.season = meta['season'] if 'season' in meta else None
            self.number_of_episodes = meta['number_of_episodes'] if 'number_of_episodes' in meta else None
            self.episode = meta['episode'] if 'episode' in meta else None

            self.playcount = meta['playcount'] if 'playcount' in meta else 0
            self.offset = bookmarks().get(self.name, self.year)

            if int(getKodiVersion()) == 18:
                self.videoDB = os.path.join(control.translatePath('special://database/'), 'MyVideos116.db')
            elif int(getKodiVersion()) >= 19:
                self.videoDB = os.path.join(control.translatePath('special://database/'), 'MyVideos119.db')
            elif int(getKodiVersion()) == 17:
                self.videoDB = os.path.join(control.translatePath('special://database/'), 'MyVideos107.db')

            self.fileID = self.getVideoDB()

            item = control.item(label=self.name, path=url)
            try:
                item.setArt({'poster': meta['poster']})
                item.setInfo(type='Video', infoLabels={'plot': meta['plot']})
            except:
                pass
            item.setProperty('IsPlayable', 'true')

            if int(sys.argv[1]) > 0:
                xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, item)
            else:
                xbmc.Player().play(url, item)
            self.keepPlaybackAlive()
            return
        except:
            return


    def keepPlaybackAlive(self):
        if self.isdebug: log_utils.log('Start - keepPlaybackAlive', log_utils.LOGINFO)
        for i in range(0, 240):
            if self.isPlayingVideo(): break
            xbmc.sleep(1000)

        if self.isPlayingVideo():
            try:
                playcountDB.createEntry(self.mediatype, self.title, self.name, self.imdb, self.number_of_seasons, self.season, self.number_of_episodes, self.episode)
            except:
                pass

        monitor = xbmc.Monitor()
        self.watcher_control = False
        while (not monitor.abortRequested()) & (not self.streamFinished):
            if self.isPlayingVideo():
                self.totalTime = self.getTotalTime()
                self.currentTime = self.getTime()
                watcher = (self.currentTime / self.totalTime >= .9)
                if watcher and not self.watcher_control:
                    playcountDB.updatePlaycount(self.mediatype, self.title, self.name, self.imdb, self.number_of_seasons, self.season, self.number_of_episodes, self.episode, 1)
                    #control.setSetting(id='watcher.control', value='true')
                    self.watcher_control = True
            monitor.waitForAbort(3)

        if self.isdebug: log_utils.log('Ende - keepPlaybackAlive', log_utils.LOGINFO)


    def idleForPlayback(self):
        for i in range(0, 200):
            if control.condVisibility('Window.IsActive(busydialog)') == 1: control.idle()
            else: break
            control.sleep(100)


    def onAVStarted(self):
        if self.isdebug: log_utils.log('Start - onAVStarted', log_utils.LOGINFO)
        control.execute('Dialog.Close(all,true)')
        if not self.offset == '0': self.seekTime(float(self.offset))
        self.idleForPlayback()
        if control.getSetting('subtitles') == 'true':
            subtitles().get(self.name, self.imdb, self.season, self.episode)
            # Subtitles in Player Menü ausschalten - wird dann bei Bedarf per "Hand" eingeschaltet
            # xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "Player.SetSubtitle", "params": {"playerid": 1, "subtitle" : "on"}, "id": "1"}')
            xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "Player.SetSubtitle", "params": {"playerid": 1, "subtitle" : "off"}, "id": "1"}')
        if self.isdebug: log_utils.log('Ende - onAVStarted', log_utils.LOGINFO)


    def onPlayBackStopped(self):
        if self.isdebug: log_utils.log('Start - onPlayBackStopped', log_utils.LOGINFO)
        self.runVideoDB()
        self.streamFinished = True
        bookmarks().reset(self.currentTime, self.totalTime, self.name, self.year)
        if self.isdebug: log_utils.log('vor parentDir - onPlayBackStopped', log_utils.LOGINFO)
        if self.watcher_control:
            self.parentDir()
            self.watcher_control = False
        if self.isdebug: log_utils.log('Ende - onPlayBackStopped', log_utils.LOGINFO)

    def onPlayBackEnded(self):
        self.onPlayBackStopped()
        if self.isdebug: log_utils.log('Ende - onPlayBackEnded', log_utils.LOGINFO)


    def parentDir(self):
        refreshtime = 1200
        ccont = ''
        if control.getSetting('hosts.mode') == '1': # Liste der Streams (Hosterliste) als Verzeichnis
            count = 0
            # prüfen ob Hosterliste aktiv ist - content ist da 'videos'
            for count in range(1, 25+1):
                control.sleep(200)
                ccont = control.getInfoLabel("Container.Content")
                if ccont == 'videos': break

            if self.isdebug: log_utils.log(__name__ + ' - count: %s - Container.Content (1):  %s' % (count, control.getInfoLabel("Container.Content")), log_utils.LOGINFO)
            if count == 25: return

            # zur Film- bzw. Episodenliste wechseln  - von content 'videos' dann zu content 'videos'
            if control.getInfoLabel("Container.Content") != 'movies' and ccont == 'videos':
                control.execute('Action(ParentDir)')
                for count in range(1, 15 + 1):
                    control.sleep(200)
                    ccont = control.getInfoLabel("Container.Content")
                    if ccont == 'movies': break

                if self.isdebug: log_utils.log(__name__ + ' - count: %s - Container.Content (2):  %s' % (count, control.getInfoLabel("Container.Content")), log_utils.LOGINFO)
                if count == 15:
                    return
                else:
                    refreshtime = 0

        if self.playcount == 0:
            ## auch abhängig von control.content()
            refresh = False
            if control.getSetting('status.refresh.movies') == 'true' and self.mediatype == 'movie': # immer!
                refresh = True
            elif control.getSetting('status.refresh.episodes') == 'true' and self.mediatype != 'movie':
                if xbmc.getCondVisibility('system.platform.linux') and xbmc.getCondVisibility('system.platform.android'): refresh = True  # Android
                elif control.getSetting('hosts.mode') == '1': refresh = True

            if refresh:
                if refreshtime != 0:control.sleep(refreshtime)
                control.execute('Container.Refresh')

# keine Einträge für bookmarks und files in die Kodi DB 'MyVideos116.db' anlegen bzw. sofort löschen
    def runVideoDB(self):
        idFile = self.getVideoDB()
        if idFile != self.fileID:
            self.removeVideoDB(idFile)

    def getVideoDB(self):
        dbcon = database.connect(self.videoDB)
        dbcur = dbcon.cursor()
        dbcur.execute("SELECT * FROM files")
        match = dbcur.fetchall()
        dbcon.close()
        if match and len(match) > 0: idFile = len(match)
        else: idFile = 0
        return idFile

    def removeVideoDB(self, idFile):
        dbcon = database.connect(self.videoDB)
        dbcur = dbcon.cursor()
        dbcur.execute("DELETE FROM files WHERE idFile = '%s'" % idFile) # in DB vorhandener Trigger löscht auch den bookmark
        dbcon.commit()
        dbcon.close()


class subtitles:
    def get(self, name, imdb, season, episode):
        season = str(season)
        episode = str(episode)
        try:
            langDict = {'Afrikaans': 'afr', 'Albanian': 'alb', 'Arabic': 'ara', 'Armenian': 'arm', 'Basque': 'baq', 'Bengali': 'ben', 'Bosnian': 'bos', 'Breton': 'bre', 'Bulgarian': 'bul', 'Burmese': 'bur', 'Catalan': 'cat', 'Chinese': 'chi', 'Croatian': 'hrv', 'Czech': 'cze', 'Danish': 'dan', 'Dutch': 'dut', 'English': 'eng', 'Esperanto': 'epo', 'Estonian': 'est', 'Finnish': 'fin', 'French': 'fre', 'Galician': 'glg', 'Georgian': 'geo', 'German': 'ger', 'Greek': 'ell', 'Hebrew': 'heb', 'Hindi': 'hin', 'Hungarian': 'hun', 'Icelandic': 'ice', 'Indonesian': 'ind', 'Italian': 'ita', 'Japanese': 'jpn', 'Kazakh': 'kaz', 'Khmer': 'khm', 'Korean': 'kor', 'Latvian': 'lav', 'Lithuanian': 'lit', 'Luxembourgish': 'ltz', 'Macedonian': 'mac', 'Malay': 'may', 'Malayalam': 'mal', 'Manipuri': 'mni', 'Mongolian': 'mon', 'Montenegrin': 'mne', 'Norwegian': 'nor', 'Occitan': 'oci', 'Persian': 'per', 'Polish': 'pol', 'Portuguese': 'por,pob', 'Portuguese(Brazil)': 'pob,por', 'Romanian': 'rum', 'Russian': 'rus', 'Serbian': 'scc', 'Sinhalese': 'sin', 'Slovak': 'slo', 'Slovenian': 'slv', 'Spanish': 'spa', 'Swahili': 'swa', 'Swedish': 'swe', 'Syriac': 'syr', 'Tagalog': 'tgl', 'Tamil': 'tam', 'Telugu': 'tel', 'Thai': 'tha', 'Turkish': 'tur', 'Ukrainian': 'ukr', 'Urdu': 'urd'}
            codePageDict = {'ara': 'cp1256', 'ar': 'cp1256', 'ell': 'cp1253', 'el': 'cp1253', 'heb': 'cp1255', 'he': 'cp1255', 'tur': 'cp1254', 'tr': 'cp1254', 'rus': 'cp1251', 'ru': 'cp1251'}
            quality = ['bluray', 'hdrip', 'brrip', 'bdrip', 'dvdrip', 'webrip', 'hdtv']

            # opensubtitles.org
            os_user = control.getSetting('subtitles.os_user')
            os_pass = control.getSetting('subtitles.os_pass')
            os_useragent = control.getSetting('subtitles.os_useragent') or 'TemporaryUserAgent'

            langs = []
            try:
                try: langs = langDict[control.getSetting('subtitles.lang.1')].split(',')
                except: langs.append(langDict[control.getSetting('subtitles.lang.1')])
            except: pass

            try:
                try: langs = langs + langDict[control.getSetting('subtitles.lang.2')].split(',')
                except: langs.append(langDict[control.getSetting('subtitles.lang.2')])
            except: pass

            try: subLang = xbmc.Player().getSubtitles()
            except: subLang = ''
            if subLang == langs[0]: raise Exception()
            server = _xmlrpclib.Server('http://api.opensubtitles.org/xml-rpc', verbose=0)

            #token = server.LogIn('', '', 'en', 'XBMC_Subtitles_v1')['token']
            token = server.LogIn(os_user, os_pass, 'en', os_useragent)['token']
            #sublanguageid = ','.join(langs)
            imdbid = re.sub('[^0-9]', '', imdb)

            if season == 'None' or episode == 'None':
                # result = server.SearchSubtitles(token, [{'sublanguageid': sublanguageid, 'imdbid': imdbid}])['data']
                result = server.SearchSubtitles(token, [{'sublanguageid': langs[0], 'imdbid': imdbid}])['data']
                if result == []: result = server.SearchSubtitles(token, [{'sublanguageid': langs[1], 'imdbid': imdbid}])['data']
                try: vidPath = xbmc.Player().getPlayingFile()
                except: vidPath = ''
                fmt = re.split('\.|\(|\)|\[|\]|\s|-', vidPath) # TODO prüfen
                fmt = [i.lower() for i in fmt]
                fmt = [i for i in fmt if i in quality]
            else:
                result = server.SearchSubtitles(token, [{'sublanguageid': langs[0], 'imdbid': imdbid, 'season': season, 'episode': episode}])['data']
                if result == []: result = server.SearchSubtitles(token, [{'sublanguageid': langs[1], 'imdbid': imdbid, 'season': season, 'episode': episode}])['data']
                fmt = ['hdtv']

            filter = []
            result = [i for i in result if i['SubSumCD'] == '1']

            for lang in langs:
                filter += [i for i in result if i['SubLanguageID'] == lang and any(x in i['MovieReleaseName'].lower() for x in fmt)]
                filter += [i for i in result if i['SubLanguageID'] == lang and any(x in i['MovieReleaseName'].lower() for x in quality)]
                filter += [i for i in result if i['SubLanguageID'] == lang]

            try: lang = xbmc.convertLanguage(filter[0]['SubLanguageID'], xbmc.ISO_639_1)
            except: lang = filter[0]['SubLanguageID']

            content = [filter[0]['IDSubtitleFile'],]
            content = server.DownloadSubtitles(token, content)
            content = base64.b64decode(content['data'][0]['data'])
            content = gzip.GzipFile(fileobj=StringIO(content)).read()

            subtitle = control.translatePath('special://temp/')
            subtitle = os.path.join(subtitle, 'TemporarySubs.%s.srt' % lang)

            codepage = codePageDict.get(lang, '')
            if codepage and control.getSetting('subtitles.utf') == 'true':
                try:
                    content_encoded = codecs.decode(content, codepage)
                    content = codecs.encode(content_encoded, 'utf-8')
                except:
                    pass

            file = control.openFile(subtitle, 'w')
            file.write(str(content))
            file.close()

            xbmc.sleep(1000)
            xbmc.Player().setSubtitles(subtitle)
        except:
            pass


class bookmarks:
    def get(self, name, year='0'):
        offset = '0'
        try:
            if not control.getSetting('bookmarks') == 'true': raise Exception()

            idFile = hashlib.md5()
            for i in name:
                try:
                    idFile.update(str(i).encode('utf-8'))
                except:
                    idFile.update(str(i))
            for i in year:
                try:
                    idFile.update(str(i).encode('utf-8'))
                except:
                    idFile.update(str(i))
            idFile = str(idFile.hexdigest())

            dbcon = database.connect(control.bookmarksFile)
            dbcur = dbcon.cursor()
            dbcur.execute("CREATE TABLE IF NOT EXISTS bookmark (""idFile TEXT, ""timeInSeconds TEXT, ""UNIQUE(idFile)"");")
            dbcur.execute("SELECT * FROM bookmark WHERE idFile = '%s'" % idFile)
            match = dbcur.fetchone()
            dbcon.commit()
            dbcon.close()
            if match: self.offset = str(match[1])
            if self.offset == '0': raise Exception()
            minutes, seconds = divmod(float(self.offset), 60)
            hours, minutes = divmod(minutes, 60)
            label = '%02d:%02d:%02d' % (hours, minutes, seconds)
            label = py2_encode("Fortsetzen ab : %s" % label)

            if control.getSetting('bookmarks.auto') == 'false':
                try:
                    yes = control.dialog.contextmenu([label, "Vom Anfang abspielen", ])
                except:
                    yes = control.yesnoDialog(label, '', '', str(name), "Fortsetzen",
                                              "Vom Anfang abspielen")
                if yes: self.offset = '0'

            return self.offset
        except:
            return offset


    def reset(self, currentTime, totalTime, name, year='0'):
        try:
            #if not control.getSetting('bookmarks') == 'true': raise Exception()
            if control.getSetting('bookmarks') == 'true' and int(currentTime) > 180:
                timeInSeconds = str(currentTime)
                idFile = hashlib.md5()
                for i in name:
                    try:
                        idFile.update(str(i).encode('utf-8'))
                    except:
                        idFile.update(str(i))
                for i in year:
                    try:
                        idFile.update(str(i).encode('utf-8'))
                    except:
                        idFile.update(str(i))
                idFile = str(idFile.hexdigest())
                dbcon = database.connect(control.bookmarksFile)
                dbcur = dbcon.cursor()
                dbcur.execute("CREATE TABLE IF NOT EXISTS bookmark (""idFile TEXT, ""timeInSeconds TEXT, ""UNIQUE(idFile)"");")
                if (currentTime / totalTime) <= .92:
                    dbcur.execute("DELETE FROM bookmark WHERE idFile = '%s'" % idFile)
                    dbcur.execute("INSERT INTO bookmark Values (?, ?)", (idFile, timeInSeconds))
                else:
                    dbcur.execute("DELETE FROM bookmark WHERE idFile = '%s'" % idFile)
                dbcon.commit()
                dbcon.close()
        except:
            pass

