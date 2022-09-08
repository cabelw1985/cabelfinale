# -*- coding: utf-8 -*-

import sys
import re
import xbmc
import xbmcgui
import xbmcplugin
import json
import xbmcvfs
PY2 = sys.version_info[0] == 2
if PY2:
	from urllib import urlencode, quote  # Python 2.X
else: 
	from urllib.parse import urlencode, quote  # Python 3.X

from .common import *


if not xbmcvfs.exists(dataPath):
	xbmcvfs.mkdirs(dataPath)

def mainMenu():
	addDir(translation(30601), artpic+'favourites.png', {'mode': 'listShowsFavs'})
	addDir(translation(30602), icon, {'mode': 'listEpisodes', 'url': BASE_LONG})
	addDir(translation(30603), icon, {'mode': 'listSelections', 'url': 'CHANNELS'})
	addDir(translation(30604), icon, {'mode': 'listSelections', 'url': 'TV SHOWS'})
	addDir(translation(30605), icon, {'mode': 'listSelections', 'url': 'WEB SHOWS'})
	addDir(translation(30606), icon, {'mode': 'listSelections', 'url': 'STAND UP'})
	addDir(translation(30607), icon, {'mode': 'listSelections', 'url': 'SERIEN'})
	addDir(translation(30608), icon, {'mode': 'listAlphabet'})
	addDir(translation(30609), icon, {'mode': 'listShows', 'url': 'standard'})
	if enableADJUSTMENT:
		addDir(translation(30610), artpic+'settings.png', {'mode': 'aConfigs'}, folder=False)
	xbmcplugin.endOfDirectory(ADDON_HANDLE)

def listAlphabet():
	debug_MS("(navigator.listAlphabet) ------------------------------------------------ START = listAlphabet -----------------------------------------------")
	for letter in ['0-9', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'R', 'S', 'T', 'U', 'W', 'Z', '??']:
		addDir(letter, alppic+letter.replace('??', 'QM')+'.jpg', {'mode': 'listShows', 'url': letter.replace('0-9', '1').replace('??', 'QM')})
	xbmcplugin.endOfDirectory(ADDON_HANDLE)

def listShows(TYPE):
	xbmcplugin.addSortMethod(ADDON_HANDLE, xbmcplugin.SORT_METHOD_LABEL)
	debug_MS("(navigator.listShows) -------------------------------------------------- START = listShows --------------------------------------------------")
	debug_MS("(navigator.listShows) ### URL or LETTER : {0} ###".format(TYPE))
	content = getUrl(BASE_URL+'/sendungen-a-bis-z/')
	if TYPE == 'QM':
		result = re.compile(r'<h3 class="category__headline">(.*?)</div>          </div>\s*</div>', re.S).findall(content)[-1]
	elif len(TYPE) < 4:
		result = re.findall(r'<div class="category clearfix" id="{0}">(.*?)(?:<div class="category clearfix"|<footer class=)'.format(TYPE), content, re.S)[0]
	else:
		result = re.findall('<div id="content" class="container">(.*?)<footer class=', content, re.S)[0]
	spl = result.split('<div class="category__item">')
	for i in range(1, len(spl), 1):
		entry = spl[i]
		title = re.compile(' alt=["\']([^"]+?)["\']/>', re.S).findall(entry)[0]
		title = cleaning(title)
		link = re.compile('<a href=["\']([^"]+?)["\']', re.S).findall(entry)[0]
		link = BASE_URL+link if link[:4] != 'http' else link
		photo = re.compile(r'(?:img["\'] src=|data-src=)["\']([^"]+?)["\']', re.S).findall(entry)[0].replace('-300x169.', '.')
		photo = BASE_URL+quote(photo) if photo[:4] != 'http' else quote(photo)
		debug_MS("(navigator.listShows) ##### TITLE = {0} || LINK = {1} || IMAGE = {2} #####".format(str(title), link, photo))
		addType = 1
		if xbmcvfs.exists(channelFavsFile):
			with open(channelFavsFile, 'r') as fp:
				watch = json.load(fp)
				for item in watch.get('items', []):
					if item.get('url') == link: addType = 2
		addDir(title, photo, {'mode': 'listSeasons', 'url': link, 'extras': photo, 'origSERIE': title}, addType=addType)
	xbmcplugin.endOfDirectory(ADDON_HANDLE)

def listSelections(TYPE):
	xbmcplugin.addSortMethod(ADDON_HANDLE, xbmcplugin.SORT_METHOD_LABEL)
	debug_MS("(navigator.listSelections) -------------------------------------------------- START = listSelections --------------------------------------------------")
	debug_MS("(navigator.listSelections) ### TYPE : {0} ###".format(TYPE))
	content = getUrl(BASE_URL+'/ganze-folgen/')
	result = re.findall(r'<h3 class="headline has-arrow">{0}</h3>(.*?)(?:<h3 class="headline has-arrow">|<footer class=)'.format(TYPE), content, re.S)[0]
	spl = result.split('<div class="bacs-item bacs-item--hover')
	for i in range(1, len(spl), 1):
		entry = spl[i]
		title = re.compile(r'(?:<meta itemprop=["\']name["\'] content=| alt=)["\']([^"]+?)["\'](?:/>|>)', re.S).findall(entry)[0]
		title = cleaning(title)
		link = re.compile('<a href=["\']([^"]+?)["\']', re.S).findall(entry)[0]
		link = BASE_URL+link if link[:4] != 'http' else link
		photo = re.compile(r'(?:<meta itemprop=["\']image["\'] content=|data-src=)["\']([^"]+?)["\']', re.S).findall(entry)[0].replace('-300x169.', '.')
		photo = BASE_URL+quote(photo) if photo[:4] != 'http' else quote(photo)
		debug_MS("(navigator.listSelections) ##### TITLE = {0} || LINK = {1} || IMAGE = {2} #####".format(str(title), link, photo))
		if not 'trailer' in link.lower():
			if TYPE == 'CHANNELS':
				addDir(title, photo, {'mode': 'listEpisodes', 'url': link, 'extras': 'compilation', 'origSERIE': title})
			else:
				addType = 1
				if xbmcvfs.exists(channelFavsFile):
					with open(channelFavsFile, 'r') as fp:
						watch = json.load(fp)
						for item in watch.get('items', []):
							if item.get('url') == link: addType = 2
				addDir(title, photo, {'mode': 'listSeasons', 'url': link, 'extras': photo, 'origSERIE': title}, addType=addType)
	xbmcplugin.endOfDirectory(ADDON_HANDLE)

def listSeasons(url, IMG, SERIE):
	debug_MS("(navigator.listSeasons) -------------------------------------------------- START = listSeasons --------------------------------------------------")
	debug_MS("(navigator.listSeasons) ### URL : {0} ###".format(url))
	COMBI_SEASON = []
	FOUND = 0
	html = getUrl(url)
	season_SELECTOR = re.search('<select title="Staffel auswählen" class=(.*?)</select>', html, re.S)
	if season_SELECTOR:
		all_SEASONS = re.findall('<option data-remote-args="(.*?)".+?data-remote-target=.+?>(.*?)</option>', season_SELECTOR.group(1), re.S)
		for url2, title in all_SEASONS:
			FOUND += 1
			new_URL = BASE_URL+'/frontend/php/ajax.php?query=bob&videosOnly=true'+url2
			title = cleaning(title)
			number = re.compile('([0-9]+)', re.S).findall(title)
			if number:
				title = translation(30620).format(str(number[0])) if 'staffel' in title.lower() else translation(30621) if str(number[0]) == '1' else title.split(' -')[0]
			debug_MS("(navigator.listSeasons) ##### TITLE = {0} || newURL = {1} #####".format(str(title), new_URL))
			COMBI_SEASON.append([title, IMG, new_URL, SERIE])
	if COMBI_SEASON and FOUND == 1:
		debug_MS("(navigator.listSeasons) ----- Only one Season FOUND - goto = listEpisodes -----")
		listEpisodes(new_URL, SERIE)
	elif COMBI_SEASON and FOUND > 1:
		for title, IMG, new_URL, SERIE in COMBI_SEASON:
			addDir(title, IMG, {'mode': 'listEpisodes', 'url': new_URL, 'origSERIE': SERIE})
	else:
		debug_MS("(navigator.listSeasons) ##### Keine SEASON-List - Kein Eintrag gefunden #####")
		return dialog.notification(translation(30523), translation(30524).format(SERIE), icon, 8000)
	xbmcplugin.endOfDirectory(ADDON_HANDLE)

def listEpisodes(url, SERIE):
	debug_MS("(navigator.listEpisodes) -------------------------------------------------- START = listEpisodes --------------------------------------------------")
	debug_MS("(navigator.listEpisodes) ### URL : {0} ### SERIE : {1} ###".format(url, SERIE))
	COMBI_EPISODE = []
	position = 0
	startURL = url
	content = getUrl(url).replace('\\', '')
	if startURL == BASE_LONG:
		result = re.findall(r'<div id="content" class="container">(.*?)</article>  </section>', content, re.S)[0]
		spl = result.split('<div class="homeTeaser-overlay Desktop_HomeTeaser')
	elif 'channels/' in startURL:
		result = re.findall('<ul id="playlist_ul">(.*?)</ul>', content, re.S)[0]
		spl = result.split('_video_li">')
	else:
		spl = content.split('bacs-item--hover bacs-item--lg has-infos-shown bacs-item--monthly')
	for i in range(1, len(spl), 1):
		entry = spl[i]
		debug_MS("(navigator.listEpisodes) no.01 ##### ENTRY = {0} #####".format(str(entry)))
		newSHOW, newTITLE, vidURL, Note_1, Note_2, DESC = ("" for _ in range(6))
		vidURL_2, vidURL_3, photo, bcDATE, bcDATE_2, bcDATE_3, year, begins = (None for _ in range(8))
		SEAS, EPIS, duration, duration_2, duration_3 = ('0' for _ in range(5))
		position += 1
		if startURL == BASE_LONG:
			title = re.compile('<h2 class=["\']title ellipsis["\']>([^<]+?)</h2>', re.S).findall(entry)[0]
		elif 'channels/' in startURL:
			title = re.compile('aria-hidden=["\']true["\']></i>([^<]+?)</a></li>', re.S).findall(entry)[0]
		else:
			title_1 = re.compile('class="title" title="(.*?)">', re.S).findall(entry)
			title_2 = re.compile(' alt="(.*?)"/>', re.S).findall(entry)
			title = title_1[0] if title_1 else title_2[0]
		title = cleaning(title)
		if not 'channels/' in startURL and ('Teil 2' in title or 'Teil 3' in title): continue
		link = re.compile('<a href=["\']([^"]+?)["\']', re.S).findall(entry)[0]
		link = BASE_URL+link if link[:4] != 'http' else link
		try: episID = re.compile(r'https?://(?:www\.)?myspass\.de/([^/]+/)*(?P<id>\d+)', re.S).findall(link)[0][1]
		except: continue
		newSHOW, newTITLE, SEAS, EPIS, DESC, duration, photo, bcDATE, vidURL = getVideodata(episID)
		if vidURL == "": continue
		if 'channels/' in startURL and 'channel erneut von vorne' in title.lower():
			position -= 1
			continue 
		if not 'channels/' in startURL and ('Teil 1' in title or 'Teil 1' in newTITLE):
			try:
				if 'www.myspass.de' in link and '-Teil-' in link: shortURL = link.split('www.myspass.de')[1].split('-Teil-')[0]
				else: shortURL = link
				plus_CONTENT = content[content.find('<table class="listView--table">')+1:]
				plus_CONTENT = plus_CONTENT[:plus_CONTENT.find('</table>')]
				match = re.findall('<tr data-month(.+?)</tr>', plus_CONTENT, re.S)
				for chtml in match:
					debug_MS("(navigator.listEpisodes) no.02 ##### more Videos CHTML = {0} #####".format(str(chtml)))
					url2 = re.compile('<a href=["\']([^"]+?)["\']', re.S).findall(chtml)[0]
					fullURL = BASE_URL+url2 if url2[:4] != 'http' else url2
					identical = similar(url2, shortURL)
					if identical is True and 'Teil-2' in fullURL:
						newIDD_2 = re.compile(r'https?://(?:www\.)?myspass\.de/([^/]+/)*(?P<id>\d+)', re.S).findall(fullURL)[0][1]
						newSHOW_2, newTITLE_2, SEAS_2, EPIS_2, DESC_2, duration_2, photo_2, bcDATE_2, vidURL_2 = getVideodata(newIDD_2)
						vidURL_2 = '@@'+vidURL_2
					if identical is True and 'Teil-3' in fullURL:
						newIDD_3 = re.compile(r'https?://(?:www\.)?myspass\.de/([^/]+/)*(?P<id>\d+)', re.S).findall(fullURL)[0][1]
						newSHOW_3, newTITLE_3, SEAS_3, EPIS_3, DESC_3, duration_3, photo_3, bcDATE_3, vidURL_3 = getVideodata(newIDD_3)
						vidURL_3 = '@@'+vidURL_3
			except: pass
		if vidURL_2: vidURL = vidURL+vidURL_2
		if vidURL_3: vidURL = vidURL+vidURL_3
		duration = int(duration)+int(duration_2)+int(duration_3)
		image = icon
		if photo:
			image = quote(photo) if photo.startswith('http') else 'https:'+quote(photo) if photo.startswith('//') else BASE_URL+quote(photo)
		SERIE = newSHOW if startURL == BASE_LONG else SERIE
		Note_1 = translation(30622).format(SERIE)
		title = SERIE+' - '+newTITLE if startURL == BASE_LONG else title.split('- Teil')[0].split(' Teil')[0]
		newTITLE = newTITLE.split(' - Teil')[0].split(' Teil')[0] if 'Teil' in newTITLE else newTITLE
		if EPIS != '0' and EPIS.isdigit():
			SEAS, EPIS = SEAS.zfill(2), EPIS.zfill(2)
			name = translation(30623).format(SEAS, EPIS, title)
			if bcDATE and not '1970' in bcDATE:
				year, begins = str(bcDATE)[-4:], bcDATE
				Note_2 = translation(30624).format(newTITLE, SEAS, EPIS, str(bcDATE))
			else: Note_2 = translation(30625).format(newTITLE, SEAS, EPIS)
		else:
			name = title+'  (Special)' if 'spezial' in str(EPIS).lower() else title
			if bcDATE and not '1970' in bcDATE:
				year, begins = str(bcDATE)[-4:], bcDATE
				Note_2 = translation(30626).format(newTITLE, str(bcDATE))
			else: Note_2 = '[CR]'
		if 'channels/' in startURL:
			name = translation(30627).format(str(position).zfill(2), newTITLE)
		plot = Note_1+Note_2+DESC.replace('\n', '[CR]')
		COMBI_EPISODE.append([episID, vidURL, image, name, SERIE, SEAS, EPIS, plot, duration, year, begins])
	if COMBI_EPISODE:
		SEND = {}
		SEND['videos'] = []
		for episID, vidURL, image, name, SERIE, SEAS, EPIS, plot, duration, year, begins in COMBI_EPISODE:
			for method in getSorting():
				xbmcplugin.addSortMethod(ADDON_HANDLE, method)
			cineType = 'episode' if EPIS != '0' and str(EPIS).isdigit() else 'movie'
			playType = 'multi' if '@@' in vidURL else 'single'
			liz = xbmcgui.ListItem(name, path='{0}?IDENTiTY={1}&mode=playCODE'.format(HOST_AND_PATH, episID))
			info = {}
			info['Season'] = SEAS
			info['Episode'] = EPIS
			info['Tvshowtitle'] = SERIE
			info['Title'] = name
			info['Tagline'] = None
			info['Plot'] = plot
			info['Duration'] = duration
			if begins: info['Date'] = begins
			info['Year'] = year
			info['Genre'] = 'Unterhaltung'
			info['Studio'] = 'myspass.de'
			info['Mpaa'] = None
			info['Mediatype'] = cineType
			liz.setInfo(type='Video', infoLabels=info)
			liz.setArt({'icon': icon, 'thumb': image, 'poster': image, 'fanart': defaultFanart})
			if image and useThumbAsFanart and image != icon and not artpic in image:
				liz.setArt({'fanart': image})
			if playType == 'single':
				liz.setProperty('IsPlayable', 'true')
				liz.setContentLookup(False)
			liz.addContextMenuItems([(translation(30654), 'RunPlugin({0}?{1})'.format(HOST_AND_PATH, 'mode=AddToQueue'))])
			xbmcplugin.addDirectoryItem(handle=ADDON_HANDLE, url='{0}?IDENTiTY={1}&mode=playCODE'.format(HOST_AND_PATH, episID), listitem=liz)
			SEND['videos'].append({'url': vidURL, 'tvshow': SERIE, 'filter': episID, 'name': name, 'pict': image, 'cycle': duration})
		with open(WORKFILE, 'w') as ground:
			json.dump(SEND, ground, indent=4, sort_keys=True)
	else:
		debug_MS("(navigator.listEpisodes) ##### Keine EPISODE-List - Kein Eintrag gefunden #####")
		return dialog.notification(translation(30523), translation(30524).format(SERIE), icon, 8000)
	xbmcplugin.endOfDirectory(ADDON_HANDLE)

def playCODE(IDD):
	debug_MS("(navigator.playCODE) -------------------------------------------------- START = playCODE --------------------------------------------------")
	debug_MS("(navigator.playCODE) ### IDD = {0} ###".format(IDD))
	finalURL = False
	position = 0
	with open(WORKFILE, 'r') as wok:
		ARRIVE = json.load(wok)
		for elem in ARRIVE['videos']:
			if elem['filter'] == IDD:
				finalURL = elem['url']
				seriesname = py2_enc(elem['tvshow'])
				title = py2_enc(elem['name'])
				title = title.split('[/COLOR]')[1].strip() if '[/COLOR]' in title else title
				photo = elem['pict']
				duration = elem['cycle']
	if finalURL:
		if '@@' in finalURL:
			PLT = cleanPlaylist()
			parts = finalURL.split('@@')
			for each in parts:
				position += 1
				NRS_title = translation(30628).format(title, str(position), str(len(parts)))
				LSM = xbmcgui.ListItem(path=each, label=NRS_title)
				LSM.setContentLookup(False)
				log("(navigator.playCODE) no. {0}_playlist : {1}".format(str(position), str(each)))
				PLT.add(each, LSM)
			xbmc.Player().play(PLT)
		else:
			log("(navigator.playCODE) StreamURL : {0} ".format(str(url)))
			LSM = xbmcgui.ListItem(path=finalURL)
			xbmcplugin.setResolvedUrl(ADDON_HANDLE, True, LSM)
	else:
		failing("(navigator.playCODE) AbspielLink-00 : *MYSPASS* Der angeforderte -VideoLink- wurde NICHT gefunden !!!")
		return dialog.notification(translation(30521).format('Video'), translation(30525), icon, 8000)

def listShowsFavs():
	debug_MS("(navigator.listShowsFavs) ------------------------------------------------ START = listShowsFavs -----------------------------------------------")
	xbmcplugin.addSortMethod(ADDON_HANDLE, xbmcplugin.SORT_METHOD_LABEL)
	if xbmcvfs.exists(channelFavsFile):
		with open(channelFavsFile, 'r') as fp:
			watch = json.load(fp)
			for item in watch.get('items', []):
				name = cleaning(item.get('name'))
				logo = icon if item.get('pict', 'None') == 'None' else item.get('pict')
				debug_MS("(navigator.listShowsFavs) ### NAME : {0} || URL : {1} || IMAGE : {2} ###".format(name, item.get('url'), logo))
				addDir(name, logo, {'mode': 'listSeasons', 'url': item.get('url'), 'extras': logo, 'origSERIE': name}, FAVclear=True)
	xbmcplugin.endOfDirectory(ADDON_HANDLE)

def favs(*args):
	TOPS = {}
	TOPS['items'] = []
	if xbmcvfs.exists(channelFavsFile):
		with open(channelFavsFile, 'r') as output:
			TOPS = json.load(output)
	if action == 'ADD':
		TOPS['items'].append({'name': name, 'pict': pict, 'url': url})
		with open(channelFavsFile, 'w') as input:
			json.dump(TOPS, input, indent=4, sort_keys=True)
		xbmc.sleep(500)
		dialog.notification(translation(30526), translation(30527).format(name), icon, 8000)
	elif action == 'DEL':
		TOPS['items'] = [obj for obj in TOPS['items'] if obj.get('url') != url]
		with open(channelFavsFile, 'w') as input:
			json.dump(TOPS, input, indent=4, sort_keys=True)
		xbmc.executebuiltin('Container.Refresh')
		xbmc.sleep(1000)
		dialog.notification(translation(30526), translation(30528).format(name), icon, 8000)

def AddToQueue():
	return xbmc.executebuiltin('Action(Queue)')

def addDir(name, image, params={}, plot=None, addType=0, FAVclear=False, folder=True):
	u = '{0}?{1}'.format(HOST_AND_PATH, urlencode(params))
	liz = xbmcgui.ListItem(name)
	liz.setInfo(type='Video', infoLabels={'Title': name, 'Plot': plot})
	liz.setArt({'icon': icon, 'thumb': image, 'poster': image, 'fanart': defaultFanart})
	if image and useThumbAsFanart and image != icon and not artpic in image and params.get('extras') != 'compilation':
		liz.setArt({'fanart': image})
	entries = []
	if addType == 1 and FAVclear is False:
		entries.append([translation(30651), 'RunPlugin({0}?{1})'.format(HOST_AND_PATH, urlencode({'mode': 'favs', 'action': 'ADD', 'name': params.get('origSERIE'), 'pict': 'None' if image == icon else image, 'url': params.get('url')}))])
	if FAVclear is True:
		entries.append([translation(30652), 'RunPlugin({0}?{1})'.format(HOST_AND_PATH, urlencode({'mode': 'favs', 'action': 'DEL', 'name': name, 'pict': image, 'url': params.get('url')}))])
	liz.addContextMenuItems(entries, replaceItems=False)
	return xbmcplugin.addDirectoryItem(handle=ADDON_HANDLE, url=u, listitem=liz, isFolder=folder)
