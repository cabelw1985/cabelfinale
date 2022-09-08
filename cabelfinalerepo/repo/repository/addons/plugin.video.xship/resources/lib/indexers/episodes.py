# -*- coding: UTF-8 -*-

#2021-07-15

import sys, re
import datetime, json, time
from resources.lib import control, workers, playcountDB
from resources.lib.tmdb import cTMDB

_params = dict(control.parse_qsl(sys.argv[2].replace('?',''))) if len(sys.argv) > 1 else dict()

class episodes:
    def __init__(self):
        self.list = []
        self.lang = "de"
        self.datetime = (datetime.datetime.utcnow() - datetime.timedelta(hours=5))
        self.systime = (self.datetime).strftime('%Y%m%d%H%M%S%f')
        self.sysmeta = _params['sysmeta']

        self.ePosition = 0

    def get(self, params):
        try:
            data = json.loads(params['sysmeta'])
            self.title = data['title']
            number_of_episodes = data['number_of_episodes']

            if not 'number_of_episodes' in data or not data['number_of_episodes']: return
            #tmdb_id = data['tmdb_id']
            #tvdb_id = data['tvdb_id'] if 'tvdb_id' in data else None
            season = data['season']
            episodes = data['episodes']
            playcount = playcountDB.getPlaycount('season', 'title', self.title, season, None)
            if playcount is None:
                #playcountDB.createEntry('season', self.title, self.title + ' S%02d' % season, None, None, season, number_of_episodes, None)
                playcount = 0
            self.sysmeta = re.sub('"playcount": \d', '"playcount": %s' % playcount, self.sysmeta)

            for i in episodes:
                self.list.append(i)

            # for i in range(1, number_of_episodes+1):
            #     self.list.append({'tmdb_id': tmdb_id, 'tvdb_id': tvdb_id, 'season': season, 'episode': i})
            self.worker()
            self.Directory(self.list)
            return  self.list
        except:
            return


    def worker(self):
        try:
            self.meta = []
            threads = []
            for i in range(0, len(self.list)):
                threads.append(workers.Thread(self.super_meta, i))
            [i.start() for i in threads]
            [i.join() for i in threads]

            self.meta = sorted(self.meta, key=lambda k: k['episode'])
            self.list = [i for i in self.meta] # falls noch eine Filterfunktion kommt
            # self.list = [i for i in self.list if not i['plot'].strip() == '' and not i['poster'] == control.addonPoster()]  # - Filter
        except:
            return


    def super_meta(self, i):
        try:
            #meta = cTMDB().get_meta_episode('episode', '', self.list[i]['tmdb_id'] , self.list[i]['season'], self.list[i]['episode'], advanced='true')
            meta = cTMDB()._format_episodes(self.list[i], self.title)
            try:
                playcount = playcountDB.getPlaycount('episode', 'title', self.title, meta['season'], meta['episode']) # mediatype, column_names, column_value, season=0, episode=0
                playcount = playcount if playcount else 0
                overlay = 7 if playcount > 0 else 6
                meta.update({'playcount': playcount, 'overlay': overlay})
            except:
                pass
            self.meta.append(meta)
        except:
            pass


    def Directory(self, items):
        # if xbmc.getInfoLabel("Container.Viewmode") != 55: xbmc.executebuiltin( "Container.SetViewMode(%i)" % 55 )
        if items == None or len(items) == 0:
            control.idle()
            sys.exit()

        sysaddon = sys.argv[0]
        syshandle = int(sys.argv[1])

        addonPoster, addonBanner = control.addonPoster(), control.addonBanner()
        addonFanart, settingFanart = control.addonFanart(), control.getSetting('fanart')

        watchedMenu = "In %s [I]Gesehen[/I]" % control.addonName
        unwatchedMenu = "In %s [I]Ungesehen[/I]" % control.addonName
        pos = 0
        for i in items:
            try:
                meta = json.loads(self.sysmeta)
                meta.pop('episodes', None)
                sysmeta = json.loads(self.sysmeta)
                sysmeta.pop('episodes', None)
                season = i['season']
                episode = i['episode']

                systitle = sysmeta['title']
                sysname = systitle + ' S%02dE%02d' % (season, episode)
                sysmeta.update({'episode': episode})
                sysmeta.update({'sysname': sysname})

                _sysmeta = control.quote_plus(json.dumps(sysmeta))

                if 'title' in i and i['title']: label = '%sx%02d  %s' % (season, episode, i['title'])
                else: label = '%sx%02d  Episode %s' % (season, episode,  episode)
                if datetime.datetime(*(time.strptime(i['premiered'], "%Y-%m-%d")[0:6])) > datetime.datetime.now():
                    label = '[COLOR=red][I]{}[/I][/COLOR]'.format(label)  # ffcc0000

                poster = i['poster'] if 'poster' in i and 'http' in i['poster'] else sysmeta['poster']
                fanart = sysmeta['fanart'] if 'fanart' in sysmeta else addonFanart
                plot = i['plot'] if 'plot' in i and len(i['plot']) > 50 else ''  #sysmeta['plot']
                plot = '[COLOR blue]%s%sStaffel: %s   Episode: %s[/COLOR]%s%s' % (i['title'], "\n",i['season'], i['episode'], "\n\n", plot)

                meta.update({'poster': poster})
                meta.update({'fanart': fanart})
                meta.update({'plot': plot})
                if 'premiered' in i and i['premiered']: meta.update({'premiered': i['premiered']})

                # try:
                #     meta.update({'title': i['title']})
                # except:
                #     pass
                # meta.update({'episode': i['episode']})

                item = control.item(label=label, offscreen=True)

                if sysmeta['playcount'] == 0: playcount = i['playcount']
                else: playcount = 1

                cm = []
                try:
                    if playcount == 1:
                        cm.append((unwatchedMenu, 'RunPlugin(%s?action=UpdatePlayCount&meta=%s&playCount=0)' % (sysaddon, _sysmeta)))
                        meta.update({'playcount': 1, 'overlay': 7})
                        sysmeta.update({'playcount': 1, 'overlay': 7})
                        pos = episode + 1
                        if len(items) == episode: pos = episode
                    else:
                        cm.append((watchedMenu, 'RunPlugin(%s?action=UpdatePlayCount&meta=%s&playCount=1)' % (sysaddon, _sysmeta)))
                        meta.update({'playcount': 0, 'overlay': 6})
                        sysmeta.update({'playcount': 0, 'overlay': 6})
                except:
                    pass
                cm.append(('Einstellungen', 'RunPlugin(%s?action=addonSettings)' % sysaddon))
                item.addContextMenuItems(cm)

                if 'cast' in sysmeta and sysmeta['cast']: item.setCast(sysmeta['cast'])
                meta.pop('cast', None)
                if settingFanart: item.setProperty('Fanart_Image', fanart)
                item.setArt({'poster': poster, 'banner': addonBanner})


                # # # remove fanart
                meta.pop('fanart', None)
                meta.pop('poster', None)
                # # # remove unsupported InfoLabels
                meta.pop('imdb_id', None)
                meta.pop('tvdb_id', None)
                meta.pop('tmdb_id', None)
                meta.pop('number_of_seasons', None)
                meta.pop('number_of_episodes', None)
                meta.pop('originallanguage', None)
                meta.pop('sysname', None)
                meta.pop('systitle', None)
                meta.pop('year', None)
                # meta.pop('director', None)

                item.setInfo(type='Video', infoLabels = meta)

                # gefakte Video/Audio Infos
                video_streaminfo = {'codec': 'h264', "width": 1920, "height": 1080}
                item.addStreamInfo('video', video_streaminfo)
                audio_streaminfo = {'codec': 'dts','channels':6,'language':'de'}
                item.addStreamInfo('audio', audio_streaminfo)

                sysmeta = control.quote_plus(json.dumps(sysmeta))
                url = '%s?action=play&sysmeta=%s' % (sysaddon, sysmeta)

                control.addItem(handle=syshandle, url=url, listitem=item, isFolder=False)
            except:
                pass

        control.content(syshandle, 'movies')    # 'episodes'
        control.directory(syshandle, cacheToDisc=True)
        control.sleep(200)
        if control.skin == 'skin.estuary': control.execute('Container.SetViewMode(%s)' % str(55))

        # setzt Auswahl nach letzte als gesehen markierte Episode
        if control.getSetting('status.position')== 'true':
            from resources.lib.utils import setPosition
            setPosition(pos, __name__)

