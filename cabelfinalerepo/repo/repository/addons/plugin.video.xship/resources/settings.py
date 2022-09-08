# -*- coding: utf-8 -*-
import sys
from  xbmcgui import NOTIFICATION_INFO, Dialog
dialog = Dialog()
from resources.lib import control
from scrapers import scrapers_source

name = control.addonInfo('name')

_params = dict(control.parse_qsl(sys.argv[1].replace('?', '')))
_action = _params.get('action')
mode = None
query = None

def run(params):
    action = params.get('subaction')

    if action == "Defaults":
        dialog.notification(name , 'Einstellungen wurden übernommen', NOTIFICATION_INFO, 500, sound=False)
        sourceList = scrapers_source.all_providers
        for i in sourceList:
            source_setting = 'provider.' + i
            value = control.getSettingDefault(source_setting)
            control.setSetting(source_setting, value)

    elif action == "toggleAll":
        dialog.notification(name , 'Einstellungen wurden übernommen', NOTIFICATION_INFO, 500, sound=False)
        sourceList = scrapers_source.all_providers
        for i in sourceList:
            source_setting = 'provider.' + i
            control.setSetting(source_setting, params['setting'])

    elif action == "defaultsGerman":
        sourceList = scrapers_source.german_providers
        for i in sourceList:
            source_setting = 'provider.' + i
            value = control.getSettingDefault(source_setting)
            control.setSetting(source_setting, value)

    elif action == "toggleGerman":
        sourceList = scrapers_source.german_providers
        for i in sourceList:
            source_setting = 'provider.' + i
            control.setSetting(source_setting, params['setting'])

    elif action == "defaultsEnglish":
        sourceList = scrapers_source.english_providers
        for i in sourceList:
            source_setting = 'provider.' + i
            value = control.getSettingDefault(source_setting)
            control.setSetting(source_setting, value)

    elif action == "toggleEnglish":
        sourceList = scrapers_source.english_providers
        for i in sourceList:
            source_setting = 'provider.' + i
            control.setSetting(source_setting, params['setting'])
