# -*- coding: UTF-8 -*-

#2021-06-09

import sys
import json
from six import iteritems
from resources.lib.tmdb import cTMDB
from resources.lib.indexers import navigator
from resources.lib import searchDB, control, utils, playcountDB

_params = dict(control.parse_qsl(sys.argv[2].replace('?', ''))) if len(sys.argv) > 1 else dict()


class person:
    def __init__(self):
        self.list = []
        self.total_pages = 0
        self.next_pages = 0
        self.query = ''
        self.activeSearchDB = ''
        #self.setSearchDB() # TODO different search providers
        self.playcount = 0

    def get(self, params):
        try:
            self.next_pages = int(params.get('page')) + 1
            self.query = params.get('query')
            # Suche nach 'willis'
            # https://api.themoviedb.org/3/search/person?language=de&api_key=be7e192d9ff45609c57344a5c561be1d&query=willis&page=1
            self.list, self.total_pages = cTMDB().search_term('person', params.get('query'), params.get('page'))
            if self.list == None or len(self.list) == 0:  # nichts gefunden
                 return control.infoDialog("Nichts gefunden", time=2000)
            #self.list = sorted(self.list, key=lambda k: k['popularity'])
            self.personDirectory(self.list)
            return self.list
        except:
            pass

    def search(self):
        # TODO different search providers
        #navigator.navigator().addDirectoryItem("DB für Suche auswählen", 'personChangeSearchDB', self.activeSearchDB + '.png', 'DefaultMovies.png', isFolder=False)
        navigator.navigator().addDirectoryItem("Neue Suche (%s)" % self.activeSearchDB, 'searchNew&table=person', self.activeSearchDB + '_people-search.png', 'DefaultMovies.png', isFolder=False)
        match = searchDB.getSearchTerms('person')
        lst = []
        delete_option = False
        for i in match:
            term = i['term']
            if term not in lst:
                delete_option = True
                navigator.navigator().addDirectoryItem(term, 'person&page=1&query=%s' % control.quote_plus(term), self.activeSearchDB + '_people-search.png',
                                                       'DefaultMovies.png', isFolder=True,
                                                       context=("Suchanfrage löschen", 'searchDelTerm&table=person&name=%s' % term))
                lst += [(term)]

        if delete_option:
            navigator.navigator().addDirectoryItem("Suchverlauf l\xc3\xb6schen", 'searchClear&table=person', 'tools.png', 'DefaultAddonProgram.png', isFolder=False)
        navigator.navigator()._endDirectory('')  # addons  videos  files


# TODO https://forum.kodi.tv/showthread.php?tid=199579
#     def setSearchDB(self, new=''):
#         if control.getSetting('active.SearchDB.person'):
#             _searchDB = control.getSetting('active.SearchDB.person')
#             if new != '':
#                 control.setSetting('active.SearchDB.person', new)
#                 _searchDB = new
#             self.activeSearchDB = _searchDB
#         else:
#             control.setSetting('active.SearchDB.person', 'tmdb')
#             self.activeSearchDB = 'tmdb'
#
#     def changeSearchDB(self):
#         active = control.getSetting('active.SearchDB.person')
#         data = []
#         for i in ['tmdb', 'trakt']:
#             if i == active: continue
#             data.append('wechseln zu ' + i.upper())
#         index = control.dialog.contextmenu(data)
#         if index == -1:
#             return
#         term = data[index].lower().split()[-1]
#         self.setSearchDB(term)
#         url = '%s?action=personSearch' % sys.argv[0]
#         control.execute('Container.Update(%s)' % url)


    def personDirectory(self, items):
        if items == None or len(items) == 0:
            control.idle()
            sys.exit()
        sysaddon = sys.argv[0]
        syshandle = int(sys.argv[1])

        addonBanner = control.addonBanner()
        addonFanart, settingFanart = control.addonFanart(), control.getSetting('fanart')
        addonNoPicture = control.addonNoPicture()
        for i in items:
            try:
                label = i['name'] # show in list

                meta = dict((k, v) for k, v in iteritems(i))

                poster = i['poster'] if 'poster' in i and i['poster'] != None else addonNoPicture
                fanart = i['fanart'] if 'fanart' in i and 'http' in i['fanart'] else addonFanart
                meta.update({'poster': poster})
                meta.update({'fanart': fanart})

                sysmeta = control.quote_plus(json.dumps(meta))

                url = '%s?action=personCredits&sysmeta=%s&number=0' % (sysaddon, sysmeta) #TODO

                item = control.item(label=label, offscreen=True)

                if 'plot' in i:
                    plot = i['plot']
                else:
                    plot = label

                meta.update({'plot': plot})

                item.setArt({'poster': poster, 'banner': addonBanner})
                item.setProperty('Fanart_Image', fanart)

                ## supported infolabels: https://codedocs.xyz/AlwinEsch/kodi/group__python__xbmcgui__listitem.html#ga0b71166869bda87ad744942888fb5f14
                # remove unsupported infolabels
                meta.pop('fanart', None)
                meta.pop('poster', None)
                meta.pop('id', None)
                meta.pop('name', None)
                meta.pop('popularity', None)

                item.setInfo(type='Video', infoLabels=meta)

                control.addItem(handle=syshandle, url=url, listitem=item, isFolder=True)
            except:
                pass

        # nächste Seite
        try:
            if self.next_pages <= self.total_pages:
                url = '%s?action=person&url=&page=%s&query=%s' % (sys.argv[0], self.next_pages, self.query)
                item = control.item(label="Nächste Seite")
                icon = control.addonNext()
                item.setArt({'icon': icon, 'thumb': icon, 'poster': icon, 'banner': icon})
                if not addonFanart == None: item.setProperty('Fanart_Image', addonFanart)
                #  -> gesehen/ungesehen im cm und "Keine Informationen verfügbar" ausblenden (abhängig von control.content() )
                item.setInfo('video', {'overlay': 4, 'plot': ' '})  # alt255
                control.addItem(handle=syshandle, url=url, listitem=item, isFolder=True)
        except:
            pass

        control.content(syshandle, 'videos')
        control.directory(syshandle, cacheToDisc=True)


    def getCredits(self, params):
        try:
            if 'items' in params:
                list = json.loads(params['items'])
                self.creditsDirectory(list, int(params['number']))
            else:
                meta = json.loads(params.get('sysmeta'))
                # Suche nach Filme mit "Bruce Willis" -> 62
                # https://api.themoviedb.org/3/person/62/movie_credits?api_key=86dd18b04874d9c94afadde7993d94e3&language=de
                self.list = cTMDB().search_credits('movie_credits', meta['id']) # "combined_credits", "tv_credits", "movie_credits"

                if self.list == None or len(self.list) == 0:  # nichts gefunden
                     control.infoDialog("Nichts gefunden", time=8000)
                #self.list = sorted(self.list, key=lambda k: k['vote_average'], reverse=True)
                self.list = utils.multikeysort(self.list, ['-vote_average', '-popularity'])
                self.creditsDirectory(self.list)
                return self.list
        except:
            pass


    def creditsDirectory(self, items, number=0):
        if items == None or len(items) == 0:
            control.idle()
            sys.exit()
        sysaddon = sys.argv[0]
        syshandle = int(sys.argv[1])

        addonPoster, addonBanner = control.addonPoster(), control.addonBanner()
        addonFanart, settingFanart = control.addonFanart(), control.getSetting('fanart')
        for i in range(number, number + 20):
            if i >= len(items) - 1: break
            try:
                #label = i['name'] # show in list
                meta = cTMDB()._formatSuper(items[i], '')
                if meta['genre'] == '': continue
                poster = meta['poster'] if 'poster' in meta and meta['poster'] != None else addonPoster
                fanart = meta['fanart'] if 'fanart' in meta and 'http' in meta['fanart'] else addonFanart
                meta.update({'poster': poster})
                meta.update({'fanart': fanart})

                sysmeta = control.quote_plus(json.dumps(meta))

                url = '%s?action=playfromPerson&sysmeta=%s' % (sysaddon, sysmeta) #playPerson

                year = str(meta['year']) if 'year' in meta else '1900'
                label = meta['title'] + ' (' + year + ')' #+ meta['mediatype']
                try:
                    playcount = playcountDB.getPlaycount('movie', 'name', label)  # mediatype, column_names, column_value, season=0, episode=0
                    meta.update({'playcount': playcount})
                except:
                    pass

                item = control.item(label=label, offscreen=True)

                if 'plot' in meta:
                    plot = meta['plot']
                else:
                    plot = label

                meta.update({'plot': plot})

                item.setArt({'poster': poster, 'banner': addonBanner})
                item.setProperty('Fanart_Image', fanart)

                ## supported infolabels: https://codedocs.xyz/AlwinEsch/kodi/group__python__xbmcgui__listitem.html#ga0b71166869bda87ad744942888fb5f14
                # remove unsupported infolabels
                meta.pop('fanart', None)
                meta.pop('poster', None)
                meta.pop('id', None)
                meta.pop('name', None)
                meta.pop('popularity', None)
                meta.pop('tmdb_id', None)
                meta.pop('genre_ids', None)
                meta.pop('originallanguage', None)

                item.setInfo(type='Video', infoLabels=meta)

                control.addItem(handle=syshandle, url=url, listitem=item, isFolder=False)
            except Exception as e:
                print(e)
                pass

        # nächste Seite
        try:
            if i < len(items)-1:
                number = number + 20
                url = '%s?action=personCredits&items=%s&number=%s' % (sys.argv[0], control.quote_plus(json.dumps(items)), number)
                item = control.item(label="Nächste Seite")
                icon = control.addonNext()
                item.setArt({'icon': icon, 'thumb': icon, 'poster': icon, 'banner': icon})
                if not addonFanart == None: item.setProperty('Fanart_Image', addonFanart)
                #  -> gesehen/ungesehen im cm und "Keine Informationen verfügbar" ausblenden (abhängig von control.content() )
                item.setInfo('video', {'overlay': 4, 'plot': ' '})  # alt255
                control.addItem(handle=syshandle, url=url, listitem=item, isFolder=True)
        except:
            pass

        control.content(syshandle, 'movies')
        control.directory(syshandle, cacheToDisc=True)

