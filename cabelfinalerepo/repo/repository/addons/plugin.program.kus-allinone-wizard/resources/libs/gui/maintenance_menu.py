
import xbmc

import os

from resources.libs.common import directory
from resources.libs.common import logging
from resources.libs.common import tools
from resources.libs.common.config import CONFIG


class MaintenanceMenu:

    def get_listing(self):
        directory.add_dir('Reinigung', {'mode': 'maint', 'name': 'clean'}, icon=CONFIG.ICONMAINT, themeit=CONFIG.THEME1)
        directory.add_dir('Addons', {'mode': 'maint', 'name': 'addon'}, icon=CONFIG.ICONMAINT, themeit=CONFIG.THEME1)
        directory.add_dir('LOG', {'mode': 'maint', 'name': 'logging'}, icon=CONFIG.ICONMAINT, themeit=CONFIG.THEME1)
        directory.add_dir('Instandhaltung', {'mode': 'maint', 'name': 'misc'}, icon=CONFIG.ICONMAINT, themeit=CONFIG.THEME1)
        directory.add_dir('Backup', {'mode': 'maint', 'name': 'backup'}, icon=CONFIG.ICONBACKUP, themeit=CONFIG.THEME1)
        directory.add_dir('System', {'mode': 'maint', 'name': 'tweaks'}, icon=CONFIG.ICONMAINT, themeit=CONFIG.THEME1)

    def clean_menu(self):
        from resources.libs import clear
        from resources.libs.common import tools

        on = '[COLORlime]AN[/COLOR]'
        off = '[COLORred]AUS[/COLOR]'

        autoclean = 'true' if CONFIG.AUTOCLEANUP == 'true' else 'false'
        cache = 'true' if CONFIG.AUTOCACHE == 'true' else 'false'
        packages = 'true' if CONFIG.AUTOPACKAGES == 'true' else 'false'
        thumbs = 'true' if CONFIG.AUTOTHUMBS == 'true' else 'false'
        includevid = 'true' if CONFIG.INCLUDEVIDEO == 'true' else 'false'
        includeall = 'true' if CONFIG.INCLUDEALL == 'true' else 'false'

        sizepack = tools.get_size(CONFIG.PACKAGES)
        sizethumb = tools.get_size(CONFIG.THUMBNAILS)
        archive = tools.get_size(CONFIG.ARCHIVE_CACHE)
        sizecache = (clear.get_cache_size()) - archive
        totalsize = sizepack + sizethumb + sizecache

        directory.add_file(
            'Komplette Reinigung: [COLORlime]{0}[/COLOR]'.format(tools.convert_size(totalsize)), {'mode': 'fullclean'},
            icon=CONFIG.ICONCLEAN, themeit=CONFIG.THEME1)
        directory.add_file('Cache reinigen: [COLORlime]{0}[/COLOR]'.format(tools.convert_size(sizecache)),
                           {'mode': 'clearcache'}, icon=CONFIG.ICONCLEAN, themeit=CONFIG.THEME1)
        if xbmc.getCondVisibility('System.HasAddon(script.module.urlresolver)') or xbmc.getCondVisibility(
                'System.HasAddon(script.module.resolveurl)'):
            directory.add_file('Resolver Cache reinigen', {'mode': 'clearfunctioncache'}, icon=CONFIG.ICONCLEAN,
                               themeit=CONFIG.THEME1)
        directory.add_file('Packages reinigen: [COLORlime]{0}[/COLOR]'.format(tools.convert_size(sizepack)),
                           {'mode': 'clearpackages'}, icon=CONFIG.ICONCLEAN, themeit=CONFIG.THEME1)
        directory.add_file(
            'Thumbnails reinigen: [COLORlime]{0}[/COLOR]'.format(tools.convert_size(sizethumb)),
            {'mode': 'clearthumb'}, icon=CONFIG.ICONCLEAN, themeit=CONFIG.THEME1)
        if os.path.exists(CONFIG.ARCHIVE_CACHE):
            directory.add_file('Archive_Cache reinigen: [COLORlime]{0}[/COLOR]'.format(
                tools.convert_size(archive)), {'mode': 'cleararchive'}, icon=CONFIG.ICONCLEAN, themeit=CONFIG.THEME1)
        directory.add_file('Alte Thumbnails reinigen', {'mode': 'oldThumbs'}, icon=CONFIG.ICONCLEAN, themeit=CONFIG.THEME1)
        directory.add_file('Crash LOGs reinigen', {'mode': 'clearcrash'}, icon=CONFIG.ICONCLEAN, themeit=CONFIG.THEME1)
        directory.add_file('Datenbanken reinigen', {'mode': 'purgedb'}, icon=CONFIG.ICONCLEAN, themeit=CONFIG.THEME1)
        directory.add_file('[COLORred]Frischer Start[/COLOR]', {'mode': 'freshstart'}, icon=CONFIG.ICONCLEAN, themeit=CONFIG.THEME1)

        directory.add_file('Automatische Reinigung beim Start: {0}'.format(autoclean.replace('true', on).replace('false', off)),
                           {'mode': 'togglesetting', 'name': 'autoclean'}, icon=CONFIG.ICONCLEAN, themeit=CONFIG.THEME1)
        if autoclean == 'true':
            directory.add_file(
                '> Automatische Reinigung Intervall: [COLORlime]{0}[/COLOR]'.format(
                    CONFIG.CLEANFREQ[CONFIG.AUTOFREQ]),
                {'mode': 'changefreq'}, icon=CONFIG.ICONCLEAN, themeit=CONFIG.THEME1)
            directory.add_file(
                '> Cache beim Start reinigen: {0}'.format(cache.replace('true', on).replace('false', off)),
                {'mode': 'togglesetting', 'name': 'clearcache'}, icon=CONFIG.ICONCLEAN, themeit=CONFIG.THEME1)
            directory.add_file(
                '> Packages beim Start reinigen: {0}'.format(packages.replace('true', on).replace('false', off)),
                {'mode': 'togglesetting', 'name': 'clearpackages'}, icon=CONFIG.ICONCLEAN, themeit=CONFIG.THEME1)
            directory.add_file(
                '> Alte Thumbnails beim Start reinigen: {0}'.format(thumbs.replace('true', on).replace('false', off)),
                {'mode': 'togglesetting', 'name': 'clearthumbs'}, icon=CONFIG.ICONCLEAN, themeit=CONFIG.THEME1)
        directory.add_file(
            'Video-Cache in Cache leeren einschließen: {0}'.format(includevid.replace('true', on).replace('false', off)),
            {'mode': 'togglecache', 'name': 'includevideo'}, icon=CONFIG.ICONCLEAN, themeit=CONFIG.THEME1)

        if includeall == 'true':
            includegaia = 'true'
            includeexodusredux = 'true'
            includethecrew = 'true'
            includeyoda = 'true'
            includevenom = 'true'
            includenumbers = 'true'
            includescrubs = 'true'
            includeseren = 'true'
        else:
            includeexodusredux = 'true' if CONFIG.INCLUDEEXODUSREDUX == 'true' else 'false'
            includegaia = 'true' if CONFIG.INCLUDEGAIA == 'true' else 'false'
            includethecrew = 'true' if CONFIG.INCLUDETHECREW == 'true' else 'false'
            includeyoda = 'true' if CONFIG.INCLUDEYODA == 'true' else 'false'
            includevenom = 'true' if CONFIG.INCLUDEVENOM == 'true' else 'false'
            includenumbers = 'true' if CONFIG.INCLUDENUMBERS == 'true' else 'false'
            includescrubs = 'true' if CONFIG.INCLUDESCRUBS == 'true' else 'false'
            includeseren = 'true' if CONFIG.INCLUDESEREN == 'true' else 'false'

        if includevid == 'true':
            directory.add_file(
                'Alle Video Addons (Cache) reinigen: {0}'.format(includeall.replace('true', on).replace('false', off)),
                {'mode': 'togglecache', 'name': 'includeall'}, icon=CONFIG.ICONCLEAN, themeit=CONFIG.THEME1)
            if xbmc.getCondVisibility('System.HasAddon(plugin.video.exodusredux)'):
                directory.add_file(
                    '> Exodus Redux Cache reinigen: {0}'.format(
                        includeexodusredux.replace('true', on).replace('false', off)),
                    {'mode': 'togglecache', 'name': 'includeexodusredux'}, icon=CONFIG.ICONCLEAN, themeit=CONFIG.THEME1)
            if xbmc.getCondVisibility('System.HasAddon(plugin.video.gaia)'):
                directory.add_file(
                    '> Gaia Cache reinigen: {0}'.format(includegaia.replace('true', on).replace('false', off)),
                    {'mode': 'togglecache', 'name': 'includegaia'}, icon=CONFIG.ICONCLEAN, themeit=CONFIG.THEME1)
            if xbmc.getCondVisibility('System.HasAddon(plugin.video.numbersbynumbers)'):
                directory.add_file(
                    '> NuMb3r5 Cache reinigen: {0}'.format(includenumbers.replace('true', on).replace('false', off)),
                    {'mode': 'togglecache', 'name': 'includenumbers'}, icon=CONFIG.ICONCLEAN, themeit=CONFIG.THEME1)
            if xbmc.getCondVisibility('System.HasAddon(plugin.video.scrubsv2)'):
                directory.add_file(
                    '> Scrubs v2 Cache reinigen: {0}'.format(includescrubs.replace('true', on).replace('false', off)),
                    {'mode': 'togglecache', 'name': 'includescrubs'}, icon=CONFIG.ICONCLEAN, themeit=CONFIG.THEME1)
            if xbmc.getCondVisibility('System.HasAddon(plugin.video.seren)'):
                directory.add_file(
                    '> Seren Cache reinigen: {0}'.format(includeseren.replace('true', on).replace('false', off)),
                    {'mode': 'togglecache', 'name': 'includeseren'}, icon=CONFIG.ICONCLEAN, themeit=CONFIG.THEME1)
            if xbmc.getCondVisibility('System.HasAddon(plugin.video.thecrew)'):
                directory.add_file(
                    '> THE CREW Cache reinigen: {0}'.format(includethecrew.replace('true', on).replace('false', off)),
                    {'mode': 'togglecache', 'name': 'includethecrew'}, icon=CONFIG.ICONCLEAN, themeit=CONFIG.THEME1)
            if xbmc.getCondVisibility('System.HasAddon(plugin.video.venom)'):
                directory.add_file(
                    '> Venom Cache reinigen: {0}'.format(includevenom.replace('true', on).replace('false', off)),
                    {'mode': 'togglecache', 'name': 'includevenom'}, icon=CONFIG.ICONCLEAN, themeit=CONFIG.THEME1)
            if xbmc.getCondVisibility('System.HasAddon(plugin.video.yoda)'):
                directory.add_file(
                    '> Yoda Cache reinigen: {0}'.format(includeyoda.replace('true', on).replace('false', off)),
                    {'mode': 'togglecache', 'name': 'includeyoda'}, icon=CONFIG.ICONCLEAN, themeit=CONFIG.THEME1)
            directory.add_file('> alle Video Addons (Cache reinigen) aktivieren', {'mode': 'togglecache', 'name': 'true'}, icon=CONFIG.ICONCLEAN,
                               themeit=CONFIG.THEME1)
            directory.add_file('> alle Video Addons (Cache reinigen) deaktivieren', {'mode': 'togglecache', 'name': 'false'}, icon=CONFIG.ICONCLEAN,
                               themeit=CONFIG.THEME1)

    def addon_menu(self):
        directory.add_file('Unbekannte Quellen de-/aktivieren', {'mode': 'unknownsources'}, icon=CONFIG.ICONADDON, themeit=CONFIG.THEME1)
        directory.add_file('Addon Updates de-/aktivieren', {'mode': 'toggleupdates'}, icon=CONFIG.ICONADDON, themeit=CONFIG.THEME1)
        directory.add_file('Quellen auf defekte URLs durchsuchen', {'mode': 'checksources'}, icon=CONFIG.ICONADDON, themeit=CONFIG.THEME1)
        directory.add_file('Nach defekten Repos suchen', {'mode': 'checkrepos'}, icon=CONFIG.ICONADDON, themeit=CONFIG.THEME1)
        directory.add_file('Addons entfernen', {'mode': 'removeaddons'}, icon=CONFIG.ICONADDON, themeit=CONFIG.THEME1)
        directory.add_dir('Addon Daten entfernen', {'mode': 'removeaddondata'}, icon=CONFIG.ICONADDON, themeit=CONFIG.THEME1)
        directory.add_dir('Addons de-/aktivieren', {'mode': 'enableaddons'}, icon=CONFIG.ICONADDON, themeit=CONFIG.THEME1)
        directory.add_file('Repos aktualisieren', {'mode': 'forceupdate'}, icon=CONFIG.ICONADDON, themeit=CONFIG.THEME1)
        directory.add_file('Addons aktualisieren', {'mode': 'forceupdate', 'action': 'auto'}, icon=CONFIG.ICONADDON, themeit=CONFIG.THEME1)

   
    def logging_menu(self):
        errors = int(logging.error_checking(count=True))
        errorsfound = str(errors) + ' Fehler gefunden' if errors > 0 else 'Keine'
        wizlogsize = ': [COLORred]Nicht gefunden[/COLOR]' if not os.path.exists(
            CONFIG.WIZLOG) else ": [COLORlime]{0}[/COLOR]".format(
            tools.convert_size(os.path.getsize(CONFIG.WIZLOG)))
            
        directory.add_file('Debug Logging de-/aktivieren', {'mode': 'enabledebug'}, icon=CONFIG.ICONLOG, themeit=CONFIG.THEME1)
        directory.add_file('LOG hochladen', {'mode': 'uploadlog'}, icon=CONFIG.ICONLOG, themeit=CONFIG.THEME1)
        directory.add_file('Fehler im LOG anzeigen: [COLORlime]{0}[/COLOR]'.format(errorsfound), {'mode': 'viewerrorlog'}, icon=CONFIG.ICONLOG, themeit=CONFIG.THEME1)
        if errors > 0:
            directory.add_file('Letzten Fehler im LOG anzeigen', {'mode': 'viewerrorlast'}, icon=CONFIG.ICONLOG, themeit=CONFIG.THEME1)
        directory.add_file('LOG anzeigen', {'mode': 'viewlog'}, icon=CONFIG.ICONLOG, themeit=CONFIG.THEME1)
        directory.add_file('Wizard LOG anzeigen', {'mode': 'viewwizlog'}, icon=CONFIG.ICONLOG, themeit=CONFIG.THEME1)
        directory.add_file('Wizard LOG bereinigen: [COLORlime]{0}[/COLOR]'.format(wizlogsize), {'mode': 'clearwizlog'}, icon=CONFIG.ICONLOG, themeit=CONFIG.THEME1)
   
        
    def misc_menu(self):
        directory.add_dir('Netzwerktools', {'mode': 'nettools'}, icon=CONFIG.ICONSPEED, themeit=CONFIG.THEME1)
        directory.add_file('Skin neu laden', {'mode': 'forceskin'}, icon=CONFIG.ICONMAINT, themeit=CONFIG.THEME1)
        directory.add_file('Profile neu laden', {'mode': 'forceprofile'}, icon=CONFIG.ICONMAINT, themeit=CONFIG.THEME1)
        directory.add_file('[COLORred]Kodi beenden erzwingen[/COLOR]', {'mode': 'forceclose'}, icon=CONFIG.ICONMAINT, themeit=CONFIG.THEME1)

    def backup_menu(self):
        directory.add_file('Backup Ordner bereinigen', {'mode': 'clearbackup'}, icon=CONFIG.ICONBACKUP, themeit=CONFIG.THEME1)
        directory.add_file('Backup Ordner: [COLORdeepskyblue]{1}[/COLOR]'.format(CONFIG.COLOR2, CONFIG.MYBUILDS), {'mode': 'settings', 'name': 'Maintenance'}, icon=CONFIG.ICONBACKUP, themeit=CONFIG.THEME1)
        directory.add_file('Build Backup erstellen', {'mode': 'backup', 'action': 'build'}, icon=CONFIG.ICONBACKUP, themeit=CONFIG.THEME1)
        directory.add_file('GuiFix Backup erstellen', {'mode': 'backup', 'action': 'gui'}, icon=CONFIG.ICONBACKUP, themeit=CONFIG.THEME1)
        directory.add_file('Theme Backup erstellen', {'mode': 'backup', 'action': 'theme'}, icon=CONFIG.ICONBACKUP, themeit=CONFIG.THEME1)
        directory.add_file('Addon Backup erstellen', {'mode': 'backup', 'action': 'addonpack'}, icon=CONFIG.ICONBACKUP, themeit=CONFIG.THEME1)
        directory.add_file('Addon Daten Backup erstellen', {'mode': 'backup', 'action': 'addondata'}, icon=CONFIG.ICONBACKUP, themeit=CONFIG.THEME1)
        directory.add_file('Lokales Build wiederherstellen', {'mode': 'restore', 'action': 'build'}, icon=CONFIG.ICONBACKUP, themeit=CONFIG.THEME1)
        directory.add_file('Lokalen GuiFix wiederherstellen', {'mode': 'restore', 'action': 'gui'}, icon=CONFIG.ICONBACKUP, themeit=CONFIG.THEME1)
        directory.add_file('Lokales Theme wiederherstellen', {'mode': 'restore', 'action': 'theme'}, icon=CONFIG.ICONBACKUP, themeit=CONFIG.THEME1)
        directory.add_file('Lokales Addon Backup wiederherstellen', {'mode': 'restore', 'action': 'addonpack'}, icon=CONFIG.ICONBACKUP, themeit=CONFIG.THEME1)
        directory.add_file('Lokales Addon Daten Backup wiederherstellen', {'mode': 'restore', 'action': 'addondata'}, icon=CONFIG.ICONBACKUP, themeit=CONFIG.THEME1)
        directory.add_file('Externes Build wiederherstellen', {'mode': 'restore', 'action': 'build', 'name': 'external'}, icon=CONFIG.ICONBACKUP, themeit=CONFIG.THEME1)
        directory.add_file('Externen GuiFix wiederherstellen', {'mode': 'restore', 'action': 'gui', 'name': 'external'}, icon=CONFIG.ICONBACKUP, themeit=CONFIG.THEME1)
        directory.add_file('Externes Theme wiederherstellen', {'mode': 'restore', 'action': 'theme', 'name': 'external'}, icon=CONFIG.ICONBACKUP, themeit=CONFIG.THEME1)
        directory.add_file('Externes Addon Backup wiederherstellen', {'mode': 'restore', 'action': 'addonpack', 'name': 'external'}, icon=CONFIG.ICONBACKUP, themeit=CONFIG.THEME1)
        directory.add_file('Externes Addon Daten Backup wiederherstellen', {'mode': 'restore', 'action': 'addondata', 'name': 'external'}, icon=CONFIG.ICONBACKUP, themeit=CONFIG.THEME1)

    def tweaks_menu(self):
        directory.add_file('Pfade in spezial:// konvertieren', {'mode': 'convertpath'}, icon=CONFIG.ICONSYSTEM, themeit=CONFIG.THEME1)
        directory.add_file('Skin neu laden', {'mode': 'forceskin'}, icon=CONFIG.ICONSYSTEM, themeit=CONFIG.THEME1)
        directory.add_file('Profile neu laden', {'mode': 'forceprofile'}, icon=CONFIG.ICONSYSTEM, themeit=CONFIG.THEME1)
        directory.add_file('[COLORred]Kodi beenden erzwingen[/COLOR]', {'mode': 'forceclose'}, icon=CONFIG.ICONSYSTEM, themeit=CONFIG.THEME1)

################################################################################
#  Copyright (C) 2019 drinfernoo / Modified & translated by SGK 2021           #
#                                                                              #
#  This Program is free software; you can redistribute it and/or modify        #
#  it under the terms of the GNU General Public License as published by        #
#  the Free Software Foundation; either version 2, or (at your option)         #
#  any later version.                                                          #
#                                                                              #
#  This Program is distributed in the hope that it will be useful,             #
#  but WITHOUT ANY WARRANTY; without even the implied warranty of              #
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the                #
#  GNU General Public License for more details.                                #
#                                                                              #
#  You should have received a copy of the GNU General Public License           #
#  along with XBMC; see the file COPYING.  If not, write to                    #
#  the Free Software Foundation, 675 Mass Ave, Cambridge, MA 02139, USA.       #
#  http://www.gnu.org/copyleft/gpl.html                                        #
################################################################################