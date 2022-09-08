# -*- coding: UTF-8 -*-

# 2022-01-13

import os, sys
from resources.lib import control

sysaddon = sys.argv[0]
syshandle = int(sys.argv[1])
artPath = control.artPath()
addonFanart = control.addonFanart()

class navigator:
    def root(self):
        import resolveurl as resolver

        self.addDirectoryItem("Suche Filme", 'moviesSearch', '_search.png', 'DefaultMovies.png')
        self.addDirectoryItem("Suche TV-Serien", 'tvshowsSearch', '_search.png', 'DefaultTVShows.png')
        self.addDirectoryItem("Suche nach Darsteller", 'personSearch', '_people-search.png', 'DefaultTVShows.png')
        self.addDirectoryItem("Filme", 'movieNavigator', 'movies.png', 'DefaultMovies.png')
        self.addDirectoryItem("TV-Serien", 'tvNavigator', 'tvshows.png', 'DefaultTVShows.png')
        self.addDirectoryItem("Werkzeuge", 'toolNavigator', 'tools.png', 'DefaultAddonProgram.png')
        #self.addDirectoryItem("Play URL", 'playURL', 'url.png', '')
        downloads = True if control.getSetting('downloads') == 'true' and (
                len(control.listDir(control.getSetting('download.movie.path'))[0]) > 0 or len(
            control.listDir(control.getSetting('download.tv.path'))[0]) > 0) else False
        if downloads:
            self.addDirectoryItem("Downloads", 'downloadNavigator', 'downloads.png', 'DefaultFolder.png')
        #self.addDirectoryItem("[B]"+control.addonName.upper()+"[/B]: EINSTELLUNGEN", 'addonSettings', 'tools.png', 'DefaultAddonProgram.png', isFolder=False)
        self._endDirectory('')

# TODO vote_count vote_average popularity revenue
    def movies(self):
        self.addDirectoryItem("[B]Filme[/B] - Neu", 'listings&media_type=movie&url=kino', 'in-theaters.png', 'DefaultRecentlyAddedMovies.png')
        self.addDirectoryItem("[B]Filme[/B] - Jahr", 'movieYears', 'years.png', 'DefaultMovies.png')
        self.addDirectoryItem("[B]Filme[/B] - Genres", 'movieGenres', 'genres.png', 'DefaultMovies.png')
        self.addDirectoryItem("[B]Filme[/B] - Am populärsten", 'listings&media_type=movie&url=production_status=released%26sort_by=popularity.desc', 'most-popular.png', 'DefaultMovies.png')
        self.addDirectoryItem("[B]Filme[/B] - Am besten bewertet", 'listings&media_type=movie&url=production_status=released%26sort_by=vote_average.desc', 'highly-rated.png', 'DefaultMovies.png')
        self.addDirectoryItem("[B]Filme[/B] - Meist bewertet", 'listings&media_type=movie&url=production_status=released%26sort_by=vote_count.desc', 'most-voted.png', 'DefaultMovies.png')
        self.addDirectoryItem("[B]Filme[/B] - Bestes Einspielergebnis", 'listings&media_type=movie&url=production_status=released%26sort_by=revenue.desc', 'box-office.png', 'DefaultMovies.png')
        # self.addDirectoryItem("[B]Filme[/B] - Oskar-Gewinner", 'movies&url=oscars', 'oscar-winners.png', 'DefaultMovies.png')

        self._endDirectory('')

    def tvshows(self):
        self.addDirectoryItem("[B]Serien[/B] - Genres", 'tvGenres', 'genres.png', 'DefaultTVShows.png')
        self.addDirectoryItem("[B]Serien[/B] - Am populärsten", 'listings&media_type=tv&url=sort_by=popularity.desc', 'most-popular.png', 'DefaultTVShows.png')
        self.addDirectoryItem("[B]Serien[/B] - Am besten bewertet", 'listings&media_type=tv&url=sort_by=vote_average.desc', 'highly-rated.png', 'DefaultTVShows.png')
        self.addDirectoryItem("[B]Serien[/B] - Meist bewertet", 'listings&media_type=tv&url=sort_by=vote_count.desc', 'most-voted.png', 'DefaultTVShows.png')
        # self.addDirectoryItem("[B]Serien[/B] - Suche nach Darstellern/Crew", 'tvPerson', 'people-search.png', 'DefaultTVShows.png', isFolder=False)
        self._endDirectory()

    def tools(self):
        self.addDirectoryItem("[B]"+control.addonName.upper()+"[/B]: EINSTELLUNGEN", 'addonSettings', 'tools.png', 'DefaultAddonProgram.png', isFolder=False)
        # self.addDirectoryItem("[B]"+control.addonName.upper()+"[/B]: Reset Settings (außer Konten)", 'resetSettings', 'nightly_update.png', 'DefaultAddonProgram.png', isFolder=False)
        self.addDirectoryItem("[B]Resolver[/B]: EINSTELLUNGEN", 'resolverSettings', 'resolveurl.png', 'DefaultAddonProgram.png', isFolder=False)
        self._endDirectory('')    # addons  videos  files

    def downloads(self):
        movie_downloads = control.getSetting('download.movie.path')
        tv_downloads = control.getSetting('download.tv.path')
        if len(control.listDir(movie_downloads)[0]) > 0:
            self.addDirectoryItem("Filme", movie_downloads, 'movies.png', 'DefaultMovies.png', isAction=False)
        if len(control.listDir(tv_downloads)[0]) > 0:
            self.addDirectoryItem("TV-Serien", tv_downloads, 'tvshows.png', 'DefaultTVShows.png', isAction=False)
        self._endDirectory()

#TODO
    def addDirectoryItem(self, name, query, thumb, icon, context=None, queue=False, isAction=True, isFolder=True):
        url = '%s?action=%s' % (sysaddon, query) if isAction == True else query
        thumb = os.path.join(artPath, thumb) if not artPath == None else icon
        #laut kodi doku - ListItem([label, label2, path, offscreen])
        listitem = control.item(name, offscreen=True) # Removed iconImage and thumbnailImage
        listitem.setArt({'poster': thumb})
        if not context == None:
            cm = []
            cm.append((context[0], 'RunPlugin(%s?action=%s)' % (sysaddon, context[1])))
            listitem.addContextMenuItems(cm)
        if isFolder:
            listitem.setInfo('video', {'overlay': 4, 'plot': '[COLOR blue]{0}[/COLOR]'.format(name)})
            listitem.setIsFolder(True)
        listitem.setProperty('fanart_image', addonFanart)
        # listitem.setProperty('Plot', '--')      #10025
        # listitem.setProperty('title', name)
        control.addItem(syshandle, url, listitem, isFolder)

    def _endDirectory(self, content='', cache=True ): # addons  videos  files
        # https://romanvm.github.io/Kodistubs/_autosummary/xbmcplugin.html#xbmcplugin.setContent
        control.content(syshandle, content)
        control.directory(syshandle, succeeded=True, cacheToDisc=cache)

