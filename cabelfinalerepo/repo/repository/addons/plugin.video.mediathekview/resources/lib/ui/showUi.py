# -*- coding: utf-8 -*-
"""
The show model UI module

Copyright 2017-2018, Leo Moll and Dominik Schlösser
SPDX-License-Identifier: MIT
"""

# pylint: disable=import-error
import time
import resources.lib.appContext as appContext
import os
import xbmcgui
import xbmcplugin

import resources.lib.mvutils as mvutils
from resources.lib.model.show import Show


class ShowUi(object):
    """
    The show model view class

    Args:
        plugin(MediathekView): the plugin object
    """

    def __init__(self, plugin):
        self.logger = appContext.MVLOGGER.get_new_logger('ShowUI')
        self.plugin = plugin
        self.handle = plugin.addon_handle
        self.startTime = 0

    def generate(self, databaseRs):
        #
        # 0 - showid
        # 1 - channelId
        # 2 - showname
        # 3 - channel
        #
        self.startTime = time.time()
        #
        xbmcplugin.addSortMethod(self.handle, xbmcplugin.SORT_METHOD_TITLE)
        xbmcplugin.setContent(self.handle, '')
        #
        showModel = Show()
        listOfElements = []
        for element in databaseRs:
            #
            showModel.init(element[0], element[1], element[2], element[3])
            #
            if element[1].find(',') == -1:
                nameLabel = element[2];
                icon = os.path.join(
                    self.plugin.path,
                    'resources',
                    'icons',
                    'sender',
                    element[1].lower() + '-i.png'
                )
                fanart = os.path.join(
                    self.plugin.path,
                    'resources',
                    'icons',
                    'sender',
                    element[1].lower() + '-f.png'
                )
            else:
                nameLabel = element[2] + ' [' + element[3] + ']';
                icon = os.path.join(
                    self.plugin.path,
                    'resources',
                    'icons',
                    'default2-m.png'
                )
                fanart = os.path.join(
                    self.plugin.path,
                    'resources',
                    'icons',
                    'default2-f.png'
                )
            #
            if self.plugin.get_kodi_version() > 17:
                list_item = xbmcgui.ListItem(label=nameLabel, offscreen=True)
            else:
                list_item = xbmcgui.ListItem(label=nameLabel)
            #

            list_item.setArt({
                'thumb': icon,
                'icon': icon,
                'fanart': fanart
            })

            info_labels = {
                'title': nameLabel,
                'sorttitle': nameLabel.lower()
            }
            list_item.setInfo(type='video', infoLabels=info_labels)
            #
            targetUrl = mvutils.build_url({
                'mode': 'films',
                'channel' : element[1].replace(',', '|'),
                'show': element[0]
            })
            #
            contextmenu = []
            contextmenu.append((
            self.plugin.language(30922),
            'RunPlugin({})'.format(
                self.plugin.build_url({
                    'mode': "downloadmv",
                    'channel' : element[1].replace(',', '|'),
                    'show': element[0]
                })
            )
            ))
            # Download TV episode
            contextmenu.append((
                self.plugin.language(30924),
                'RunPlugin({})'.format(
                    self.plugin.build_url({
                        'mode': "downloadep",
                        'channel' : element[1].replace(',', '|'),
                        'show': element[0]
                    })
                )
            ))
            #
            list_item.addContextMenuItems(contextmenu)
            #
            listOfElements.append((targetUrl, list_item, True))
        #
        xbmcplugin.addDirectoryItems(
            handle=self.handle,
            items=listOfElements,
            totalItems=len(listOfElements)
        )
        #
        xbmcplugin.endOfDirectory(self.handle, cacheToDisc=False)
        self.plugin.setViewId(self.plugin.resolveViewId('SHOWS'))
        #
        self.logger.debug('generated: {} sec', time.time() - self.startTime)
