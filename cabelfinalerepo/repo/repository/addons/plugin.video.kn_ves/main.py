# Module: default
# Author: Roman V. M., modified by Birger Jesch
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html

from resources.lib.tools import *
import sys
import requests
import json
import os
from urllib.parse import urlencode, parse_qsl
import xbmc
import xbmcgui
import xbmcplugin
import YDStreamExtractor

server = getAddonSetting('server')
writeLog('Event Server: {}'.format(server), xbmc.LOGINFO)
if server[-1] != '/': server = '{}/'.format(ADDON.getSetting('server'))

yt_quality = getAddonSetting('quality', sType=NUM)
show_outdated = getAddonSetting('show_outdated', sType=BOOL)

API = 'api.php?playlist'

FANART = os.path.join(PATH, 'resources', 'media', 'wp3.jpg')
ICON = os.path.join(PATH, 'resources', 'media', 'icon.png')

SERVER_TIME_FORMAT = '%Y-%m-%d %H:%M'
PLUGIN_TIME_FORMAT = '{} {}'.format(xbmc.getRegion('dateshort'),
                                    xbmc.getRegion('time').replace('%H%H', '%H').replace('%I%I', '%I').replace(':%S', ''))

# playstates: = 'Timing unknown', 'Permalink', 'coming soon', 'outdated', 'on Air'

playstate = list([LS(30061), LS(30062), LS(30063), LS(30064), LS(30065)])
playstate_info = list([LS(30071), LS(30072), LS(30073), LS(30074), LS(30075)])

playlist = None

_url = sys.argv[0]
_handle = int(sys.argv[1])


def convDate(sDatetime, sFrom=SERVER_TIME_FORMAT, sTo=PLUGIN_TIME_FORMAT):
    so = str2datetime(sDatetime, sFrom)
    if so:
        return datetime2str(so, sTo)
    return sDatetime


def exists(item):
    if not item: return False
    try:
        req = requests.get(item, stream=True)
        req.raise_for_status()
        return True

    except requests.exceptions.ConnectTimeout as e:
        writeLog(str(e), xbmc.LOGERROR)
        # no response
        notify(LS(30000), LS(30040), xbmcgui.NOTIFICATION_ERROR)

    except requests.exceptions.ConnectionError as e:
        writeLog(str(e), xbmc.LOGERROR)
        # could not resolve host
        notify(LS(30000), LS(30045), xbmcgui.NOTIFICATION_ERROR)

    except requests.exceptions.HTTPError as e:

        if req.status_code == 403 or req.status_code == 404:
            # forbidden/not found
            writeLog(str(e), xbmc.LOGERROR)
    return False


def get_playlist():
    playlist = None
    try:
        req = requests.get('{}{}'.format(server, API))
        req.raise_for_status()
        js = json.loads(req.text)
        response = js.get('result', None)
        if response is None:

            # Invalid Response
            notify(LS(30000), LS(30044))
            writeLog('Got invalid or no response from Eventserver, exiting...', xbmc.LOGINFO)
            exit()

        else:
            if js.get('code', '') == '30030':

                # empty playlist
                writeLog('No content available', xbmc.LOGERROR)
                notify(LS(30000), LS(30049))
                exit()

            elif js.get('code', '') == '30031':
                playlist = js.get('item', list())
                writeLog('{} items received'.format(len(playlist)), xbmc.LOGINFO)
                return playlist

    except requests.exceptions.ConnectTimeout as e:
        writeLog(str(e), xbmc.LOGERROR)
        # no response
        notify(LS(30000), LS(30040), xbmcgui.NOTIFICATION_ERROR)

    except requests.exceptions.ConnectionError as e:
        writeLog(str(e), xbmc.LOGERROR)
        # could not resolve host
        notify(LS(30000), LS(30045), xbmcgui.NOTIFICATION_ERROR)

    except requests.exceptions.HTTPError as e:

        if req.status_code == 403:
            # forbidden
            notify(LS(30000), LS(30041), xbmcgui.NOTIFICATION_ERROR)

        elif req.status_code == 404:
            # not found
            notify(LS(30000), LS(30042), xbmcgui.NOTIFICATION_ERROR)

        writeLog(str(e), xbmc.LOGERROR)

    except ValueError as e:
        # communication error
        notify(LS(30000), LS(30043), xbmcgui.NOTIFICATION_ERROR)
        writeLog(str(e), xbmc.LOGERROR)

    except AttributeError as e:
        # communication error
        notify(LS(30000), LS(30043), xbmcgui.NOTIFICATION_ERROR)
        writeLog(str(e), xbmc.LOGERROR)

    exit()


def get_parameters(params):
    return ','.join(urlencode(params).split('&'))


def get_url(params):
    return '{0}?{1}'.format(_url, urlencode(params))


def list_videos():
    """
    Create the list of playable videos in the Kodi interface.
    """
    # Set plugin category. It is displayed in some skins as the name
    # of the current section.
    current = int(time.time())
    xbmcplugin.setPluginCategory(_handle, LS(30060))

    # Set plugin content. It allows Kodi to select appropriate views
    # for this type of content.
    xbmcplugin.setContent(_handle, 'videos')

    for video in playlist:

        if video['plot'] != '':
            video['plot'] += '[CR][CR]{} {}'.format(LS(30068), video['user'])
        elif video['user'] != '':
            video['plot'] = '{} {}'.format(LS(30068), video['user'])
        else:
            pass

        if not video.get('permalink', False) and (video['ts_from'] == '' or video['ts_to'] == ''): continue

        list_item = xbmcgui.ListItem(label=video['event'])

        if not exists(video['fanart']): video['fanart'] = FANART
        if not exists(video['icon']): video['icon'] = ICON
        list_item.setArt({'thumb': video['icon'], 'icon': video['icon'],
                          'fanart': video['fanart']})

        status = 0
        color = '[COLOR=FFFFFFFF]'
        add_info = playstate_info[status]

        stream = True
        if video['stream'] == '':
            color = '[COLOR=FFFF0000]'
            stream = False

        if video.get('permalink', False):
            status = 1
            add_info = playstate_info[status]
        elif current < int(video['ts_from']):
            status = 2
            if stream: color = '[COLOR=FFBBBB00]'
            add_info = playstate_info[status].format(convDate(video['from']))
        elif int(video['ts_from']) < current < int(video['ts_to']):
            status = 4
            if stream: color = '[COLOR=FF00BB00]'
            add_info = playstate_info[status].format(convDate(video['to']))
        elif current > int(video['ts_to'] and int(video['ts_to']) > 0):
            status = 3
            color = '[COLOR=FF4040FF]'
            add_info = playstate_info[status].format(convDate(video['to']))
        elif stream:
            color = '[COLOR=FFFFFF00]'

        list_item.setInfo('video', {'title': '{}{}:[/COLOR] {}'.format(color, add_info, video['event']),
                                    'tagline': add_info,
                                    'date': video['from'],
                                    'genre': video['genre'],
                                    'plot': video['plot'],
                                    'mediatype': 'video'})

        list_item.setLabel2(add_info)
        list_item.setProperty('IsPlayable', 'true')
        is_folder = False
        url = get_url({'action': 'play', 'video': video['stream'].encode('ascii', 'ignore'),
                       'isyoutube': video['isyoutube'], 'isplayable': status})

        if status == 3 and not show_outdated: continue

        xbmcplugin.addDirectoryItem(_handle, url, list_item, is_folder)

    xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_DATE)
    xbmcplugin.endOfDirectory(_handle, succeeded=True, updateListing=True, cacheToDisc=False)


def play_video(path, isyoutube, isplayable):
    """
    Play a video by the provided path.

    :param path: Fully-qualified video URL
    :type path: str
    :type isyoutube: bool
    :type isplayable: Number 0-4
    """
    if isplayable in ('0', '2', '3'):
        # unplayable item (unknown, coming soon, outdated)
        if isplayable == '2':
            if not dialogYesNo(LS(30000), LS(30067)):
                return
        elif isplayable == '3':
            if not dialogYesNo(LS(30000), LS(30066)):
                return
        else:
            return

    if strToBool(isyoutube):
        writeLog('Youtube video, invoke plugin.youtube.dl', xbmc.LOGINFO)
        writeLog('try to use quality factor {}'.format(yt_quality))

        if YDStreamExtractor.mightHaveVideo(path, resolve_redirects=True):
            try:
                vid = YDStreamExtractor.getVideoInfo(path, quality=yt_quality, resolve_redirects=True)
                if vid is not None:
                    if vid.hasMultipleStreams():
                        s_list = list()
                        for stream in vid.streams():
                            s_list.append(stream['title'])
                        writeLog('multiple streams detected: {}'.format(', '.join(s_list)), xbmc.LOGINFO)
                    path = vid.streamURL()
                else:
                    notify(LS(30000), LS(30047), xbmcgui.NOTIFICATION_WARNING)
                    writeLog('Could not extract video stream', xbmc.LOGERROR)
            except Exception as e:
                notify(LS(30000), LS(30047), xbmcgui.NOTIFICATION_WARNING)
                writeLog('youtube_dl has thrown an exception', xbmc.LOGERROR)
                writeLog(str(e), xbmc.LOGERROR)

        else:
            writeLog('Could not extract video stream', xbmc.LOGERROR)
            notify(LS(30000), LS(), xbmcgui.NOTIFICATION_WARNING)

    play_item = xbmcgui.ListItem(path=path)
    xbmcplugin.setResolvedUrl(_handle, True, listitem=play_item)


def router(paramstring):
    """
    Router function that calls other functions
    depending on the provided paramstring

    :param paramstring: URL encoded plugin paramstring
    :type paramstring: str
    """

    writeLog('Provided parameters: {}'.format(paramstring))
    params = dict(parse_qsl(paramstring))
    if params:

        if params['action'] == 'listing':
            list_videos()

        elif params['action'] == 'play':
            try:
                play_video(params['video'], params['isyoutube'], params['isplayable'])
            except KeyError:
                writeLog('not all parameters passed', level=xbmc.LOGERROR)

        else:
            raise ValueError('Invalid paramstring: {}!'.format(paramstring))
    else:

        # Bootstrap
        list_videos()


if __name__ == '__main__':

    playlist = get_playlist()
    router(sys.argv[2][1:])
