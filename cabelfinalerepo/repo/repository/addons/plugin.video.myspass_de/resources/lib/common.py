# -*- coding: utf-8 -*-

import sys
import os
import re
import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon
import json
import xbmcvfs
import time
from datetime import datetime, timedelta
import io
import gzip
import difflib
PY2 = sys.version_info[0] == 2
if PY2:
	from urllib import urlencode, quote, unquote_plus  # Python 2.X
	from urllib2 import build_opener  # Python 2.X
	TRANS_PATH, LOG_MESSAGE, INPUT_APP = xbmc.translatePath, xbmc.LOGNOTICE, 'inputstreamaddon' # Stand: 05.12.20 / Python 2.X
else:
	from urllib.parse import urlencode, quote, unquote_plus  # Python 3.X
	from urllib.request import build_opener  # Python 3.X
	TRANS_PATH, LOG_MESSAGE, INPUT_APP = xbmcvfs.translatePath, xbmc.LOGINFO, 'inputstream' # Stand: 05.12.20  / Python 3.X


global debuging
HOST_AND_PATH                 = sys.argv[0]
ADDON_HANDLE                  = int(sys.argv[1])
dialog                                      = xbmcgui.Dialog()
addon                                     = xbmcaddon.Addon()
addon_id                                = addon.getAddonInfo('id')
addon_name                         = addon.getAddonInfo('name')
addon_version                      = addon.getAddonInfo('version')
addonPath                             = TRANS_PATH(addon.getAddonInfo('path')).encode('utf-8').decode('utf-8')
dataPath                                = TRANS_PATH(addon.getAddonInfo('profile')).encode('utf-8').decode('utf-8')
channelFavsFile                    = os.path.join(dataPath, 'favorites_MYSPASS.json')
WORKFILE                             = os.path.join(dataPath, 'episode_data.json')
defaultFanart                        = (os.path.join(addonPath, 'fanart.jpg') if PY2 else os.path.join(addonPath, 'resources', 'media', 'fanart.jpg'))
icon                                         = (os.path.join(addonPath, 'icon.png') if PY2 else os.path.join(addonPath, 'resources', 'media', 'icon.png'))
artpic                                      = os.path.join(addonPath, 'resources', 'media', '').encode('utf-8').decode('utf-8')
alppic                                      = os.path.join(addonPath, 'resources', 'media', 'alphabet', '').encode('utf-8').decode('utf-8')
useThumbAsFanart              = addon.getSetting('useThumbAsFanart') == 'true'
enableADJUSTMENT            = addon.getSetting('show_settings') == 'true'
DEB_LEVEL                            = (LOG_MESSAGE if addon.getSetting('enableDebug') == 'true' else xbmc.LOGDEBUG)
BASE_LONG                           = 'https://www.myspass.de/'
BASE_URL                              = 'https://www.myspass.de'

xbmcplugin.setContent(ADDON_HANDLE, 'tvshows')

def py2_enc(s, nom='utf-8', ign='ignore'):
	if PY2:
		if not isinstance(s, basestring):
			s = str(s)
		s = s.encode(nom, ign) if isinstance(s, unicode) else s
	return s

def py2_uni(s, nom='utf-8', ign='ignore'):
	if PY2 and isinstance(s, str):
		s = unicode(s, nom, ign)
	return s

def py3_dec(d, nom='utf-8', ign='ignore'):
	if not PY2 and isinstance(d, bytes):
		d = d.decode(nom, ign)
	return d

def translation(id):
	return py2_enc(addon.getLocalizedString(id))

def failing(content):
	log(content, xbmc.LOGERROR)

def debug_MS(content):
	log(content, DEB_LEVEL)

def log(msg, level=LOG_MESSAGE): # kompatibel mit Python-2 und Python-3
	msg = py2_enc(msg)
	return xbmc.log('[{0} v.{1}]{2}'.format(addon_id, addon_version, msg), level)

def get_userAgent():
	base = 'Mozilla/5.0 {0} AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.89 Safari/537.36'
	if xbmc.getCondVisibility('System.Platform.Android'):
		if 'arm' in os.uname()[4]: return base.format('(X11; CrOS armv7l 7647.78.0)') # ARM based Linux
		return base.format('(X11; Linux x86_64)') # x86 Linux
	elif xbmc.getCondVisibility('System.Platform.Windows'):
		return base.format('(Windows NT 10.0; WOW64)') # Windows
	elif xbmc.getCondVisibility('System.Platform.IOS'):
		return base.format('(iPhone; CPU iPhone OS 10_3 like Mac OS X)') # iOS iPhone/iPad
	elif xbmc.getCondVisibility('System.Platform.Darwin'):
		return base.format('(Macintosh; Intel Mac OS X 10_10_1)') # Mac OSX
	return base.format('(X11; Linux x86_64)') # x86 Linux

def getUrl(url, header=None, data=None, agent=get_userAgent()):
	opener = build_opener()
	opener.addheaders = [('User-Agent', agent), ('Accept-Encoding', 'gzip, identity')]
	try:
		if header: opener.addheaders = header
		response = opener.open(url, data, timeout=30)
		if response.info().get('Content-Encoding') == 'gzip':
			content = py3_dec(gzip.GzipFile(fileobj=io.BytesIO(response.read())).read())
		else:
			content = py3_dec(response.read())
	except Exception as e:
		failure = str(e)
		failing("(common.getUrl) ERROR - ERROR - ERROR : ########## {0} === {1} ##########".format(url, failure))
		dialog.notification(translation(30521).format('URL'), "ERROR = [COLOR red]{0}[/COLOR]".format(failure), icon, 15000)
		return sys.exit(0)
	return content

def get_Seconds(info):
	try:
		info = re.sub('[a-z]', '', info)
		secs = sum(x * int(t) for x, t in zip([1, 60, 3600], reversed(info.split(':'))))
		return "{0:.0f}".format(secs)
	except: return '0'

def getSorting():
	method = [xbmcplugin.SORT_METHOD_UNSORTED, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE, xbmcplugin.SORT_METHOD_DURATION, xbmcplugin.SORT_METHOD_EPISODE, xbmcplugin.SORT_METHOD_DATE]
	return method

def cleanPlaylist():
	playlist = xbmc.PlayList(1)
	playlist.clear()
	return playlist

def cleaning(text):
	text = py2_enc(text)
	for n in (('&lt;', '<'), ('&gt;', '>'), ('&amp;', '&'), ('&Amp;', '&'), ('&apos;', "'"), ("&quot;", "\""), ("&Quot;", "\""), ('&szlig;', 'ß'), ('&mdash;', '-'), ('&ndash;', '-'), ('&nbsp;', ' '), ('&hellip;', '...'), ('\xc2\xb7', '-'),
				("&#x27;", "'"), ('&#34;', '"'), ('&#39;', '\''), ('&#039;', '\''), ('&#x00c4', 'Ä'), ('&#x00e4', 'ä'), ('&#x00d6', 'Ö'), ('&#x00f6', 'ö'), ('&#x00dc', 'Ü'), ('&#x00fc', 'ü'), ('&#x00df', 'ß'), ('&#xD;', ''),
				('&#xC4;', 'Ä'), ('&#xE4;', 'ä'), ('&#xD6;', 'Ö'), ('&#xF6;', 'ö'), ('&#xDC;', 'Ü'), ('&#xFC;', 'ü'), ('&#xDF;', 'ß'), ('&#x201E;', '„'), ('&#xB4;', '´'), ('&#x2013;', '-'), ('&#xA0;', ' '),
				('&Auml;', 'Ä'), ('&Euml;', 'Ë'), ('&Iuml;', 'Ï'), ('&Ouml;', 'Ö'), ('&Uuml;', 'Ü'), ('&auml;', 'ä'), ('&euml;', 'ë'), ('&iuml;', 'ï'), ('&ouml;', 'ö'), ('&uuml;', 'ü'), ('&#376;', 'Ÿ'), ('&yuml;', 'ÿ'),
				('&agrave;', 'à'), ('&Agrave;', 'À'), ('&aacute;', 'á'), ('&Aacute;', 'Á'), ('&acirc;', 'â'), ('&Acirc;', 'Â'), ('&egrave;', 'è'), ('&Egrave;', 'È'), ('&eacute;', 'é'), ('&Eacute;', 'É'), ('&ecirc;', 'ê'), ('&Ecirc;', 'Ê'),
				('&igrave;', 'ì'), ('&Igrave;', 'Ì'), ('&iacute;', 'í'), ('&Iacute;', 'Í'), ('&icirc;', 'î'), ('&Icirc;', 'Î'), ('&ograve;', 'ò'), ('&Ograve;', 'Ò'), ('&oacute;', 'ó'), ('&Oacute;', 'Ó'), ('&ocirc;', 'ô'), ('&Ocirc;', 'Ô'),
				('&ugrave;', 'ù'), ('&Ugrave;', 'Ù'), ('&uacute;', 'ú'), ('&Uacute;', 'Ú'), ('&ucirc;', 'û'), ('&Ucirc;', 'Û'), ('&yacute;', 'ý'), ('&Yacute;', 'Ý'),
				('u00c4', 'Ä'), ('u00e4', 'ä'), ('u00d6', 'Ö'), ('u00f6', 'ö'), ('u00dc', 'Ü'), ('u00fc', 'ü'), ('u00df', 'ß'), ('u00e0', 'à'), ('u00e1', 'á'), ('u00e9', 'é'), # Line = php-Codes clear
				('u00b4', '´'), ('u0060', '`'), ('u201c', '“'), ('u201d', '”'), ('u201e', '„'), ('u201f', '‟'), ('u2013', '-'), ("u2018", "‘"), ("u2019", "’"), # Line = php-Codes clear
				('Ã¤', 'ä'), ('Ã„', 'Ä'), ('Ã¶', 'ö'), ('Ã–', 'Ö'), ('Ã¼', 'ü'), ('Ãœ', 'Ü'), ('ÃŸ', 'ß'), ('â€ž', '„'), ('â€œ', '“'), ('â€™', '’'), ('â€“', '–'), ('Ã¡', 'á'), ('Ã©', 'é'), ('Ã¨', 'è')): # Line = xml-writing-Umlaut clear
				text = text.replace(*n)
	return text.strip()

def similar(a, b, max_similarity=0.85):
	if difflib.SequenceMatcher(None, a, b).ratio() >= max_similarity:
		debug_MS("(common.similar) ##### fullURL = {0} || URL-2 = {1} || SIMILAR % = {2} #####".format(a, b, str(difflib.SequenceMatcher(None, a, b).ratio())))
		return True
	return False

def getVideodata(VideoID):
	# https://www.myspass.de/includes/apps/video/getvideometadataxml.php?id=886
	show, name, plot, stream = ("" for _ in range(4))
	seasonNR, episodeNR, duration = ('0' for _ in range(3))
	image, startDATES = (None for _ in range(2))
	url = BASE_URL+'/includes/apps/video/getvideometadataxml.php?id='+VideoID
	debug_MS("(common.getVideodata) ### URL : {0} ###".format(str(url)))
	content = getUrl(url)
	debug_MS("++++++++++++++++++++++++")
	debug_MS("(common.getVideodata) CONTENT = {0}".format(str(content)))
	debug_MS("++++++++++++++++++++++++")
	TVS = re.compile('<format><!\\[CDATA\\[(.+?)\\]\\]></format>', re.S).findall(content)
	if TVS: show = cleaning(TVS[0])
	TTL = re.compile('<title><!\\[CDATA\\[(.+?)\\]\\]></title>', re.S).findall(content)
	if TTL: name = cleaning(TTL[0])
	SEAS = re.compile('<season><!\\[CDATA\\[(.+?)\\]\\]></season>', re.S).findall(content)
	if SEAS: seasonNR = SEAS[0]
	EPIS = re.compile('<episode><!\\[CDATA\\[(.+?)\\]\\]></episode>', re.S).findall(content)
	if EPIS: episodeNR = EPIS[0]
	DESC = re.compile('<description><!\\[CDATA\\[(.+?)\\]\\]></description>', re.S).findall(content)
	if DESC: plot = cleaning(DESC[0])
	DUR = re.compile('<duration><!\\[CDATA\\[(.+?)\\]\\]></duration>', re.S).findall(content)
	if DUR: duration = get_Seconds(DUR[0])
	IMG = re.compile('<imagePreview><!\\[CDATA\\[(.+?)\\]\\]></imagePreview>', re.S).findall(content)
	if IMG: image = IMG[0]
	BCDT = re.compile('<broadcast_date><!\\[CDATA\\[(.+?)\\]\\]></broadcast_date>', re.S).findall(content)
	if BCDT:
		try:
			airedtime = datetime(*(time.strptime(BCDT[0], '%Y{0}%m{0}%d'.format('-'))[0:6])) # 2019-06-13
			startDATES = airedtime.strftime('%d{0}%m{0}%Y').format('.')
		except: pass
	VID = re.compile('<url_flv><!\\[CDATA\\[(.+?)\\]\\]></url_flv>', re.S).findall(content)
	if VID:
		stream = VID[0]
		grps = re.search(r'/myspass2009/\d+/(\d+)/(\d+)/(\d+)/', stream)
		for group in grps.groups() if grps else []:
			videoINT = int(VideoID)
			groupINT = int(group)
			if groupINT > videoINT:
				try: stream = stream.replace(group, unicode(groupINT // videoINT))
				except NameError: stream = stream.replace(group, str(groupINT // videoINT))
	return (show, name, seasonNR, episodeNR, plot, duration, image, startDATES, stream)

def parameters_string_to_dict(parameters):
	paramDict = {}
	if parameters:
		paramPairs = parameters[1:].split('&')
		for paramsPair in paramPairs:
			paramSplits = paramsPair.split('=')
			if (len(paramSplits)) == 2:
				paramDict[paramSplits[0]] = paramSplits[1]
	return paramDict

params = parameters_string_to_dict(sys.argv[2])
name = unquote_plus(params.get('name', ''))
url = unquote_plus(params.get('url', ''))
pict = unquote_plus(params.get('pict', ''))
mode = unquote_plus(params.get('mode', 'root'))
action = unquote_plus(params.get('action', ''))
origSERIE = unquote_plus(params.get('origSERIE', ''))
extras = unquote_plus(params.get('extras', 'standard'))
IDENTiTY = unquote_plus(params.get('IDENTiTY', ''))
