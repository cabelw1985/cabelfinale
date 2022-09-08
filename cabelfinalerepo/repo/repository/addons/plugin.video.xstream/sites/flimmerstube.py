# -*- coding: utf-8 -*-

# 2022-08-26 Heptamer - Regex Fix Zeile 117


from resources.lib.handler.ParameterHandler import ParameterHandler
from resources.lib.handler.requestHandler import cRequestHandler
from resources.lib.tools import logger, cParser
from resources.lib.gui.guiElement import cGuiElement
from resources.lib.gui.gui import cGui
from resources.lib.config import cConfig

SITE_IDENTIFIER = 'flimmerstube'
SITE_NAME = 'Flimmerstube'
SITE_ICON = 'flimmerstube.png'
SITE_SETTINGS = '<setting id="flimmerstube.user" type="text" label="30083" default="" /><setting id="flimmerstube.pass" type="text" option="hidden" label="30084" default="" />'
URL_MAIN = 'http://flimmerstube.com'
URL_MOVIE = URL_MAIN + '/video/vic/alle_filme'
URL_SEARCH = URL_MAIN + '/video/shv'
SITE_GLOBAL_SEARCH = False


def load():
    logger.info('Load %s' % SITE_NAME)
    params = ParameterHandler()
    username = cConfig().getSetting('flimmerstube.user')
    password = cConfig().getSetting('flimmerstube.pass')
    if username == '' and password == '':
        import xbmcgui
        xbmcgui.Dialog().ok('INFO', '[COLOR red]Für diese Seite ist ein kostenloses Benutzerkonto nötig, bitte registrieren Sie sich unter http://flimmerstube.com und tragen Sie ihre Kontodaten in den xStream-Einstellungen ein.[/COLOR]')
    else:
        oRequest = cRequestHandler('http://flimmerstube.com/index/sub/')
        oRequest.addHeaderEntry('X-Requested-With', 'XMLHttpRequest')
        oRequest.addHeaderEntry('Referer', URL_MAIN)
        oRequest.addParameters('user', username)
        oRequest.addParameters('password', password)
        oRequest.addParameters('rem', '1')
        oRequest.addParameters('a', '2')
        oRequest.addParameters('ajax', '2')
        oRequest.addParameters('_tp_', 'xml')
        oRequest.request()
        params.setParam('sUrl', URL_MOVIE)
        cGui().addFolder(cGuiElement('Deutsche Horrorfilme', SITE_IDENTIFIER, 'showEntries'), params)
        cGui().addFolder(cGuiElement('Genre', SITE_IDENTIFIER, 'showGenre'), params)
        cGui().addFolder(cGuiElement('Suche', SITE_IDENTIFIER, 'showSearch'))
        cGui().setEndOfDirectory()


def showGenre():
    params = ParameterHandler()
    entryUrl = params.getValue('sUrl')
    sHtmlContent = cRequestHandler(entryUrl).request()
    pattern = '<a[^>]class=[^>]catName[^>][^>]href="([^"]+)"[^>]>([^"]+)</a>'
    isMatch, aResult = cParser.parse(sHtmlContent, pattern)
    if not isMatch:
        cGui().showInfo()
        return

    for sUrl, sName in aResult:
        params.setParam('sUrl', URL_MAIN + sUrl)
        cGui().addFolder(cGuiElement(sName, SITE_IDENTIFIER, 'showEntries'), params)
    cGui().setEndOfDirectory()


def showEntries(entryUrl=False, sGui=False, sSearchText=False):
    oGui = sGui if sGui else cGui()
    params = ParameterHandler()
    if not entryUrl: entryUrl = params.getValue('sUrl')
    oRequest = cRequestHandler(entryUrl, ignoreErrors=(sGui is not False))
    if sSearchText:
        oRequest.addHeaderEntry('Referer', entryUrl)
        oRequest.addHeaderEntry('Upgrade-Insecure-Requests', '1')
        oRequest.addParameters('query', sSearchText)
        if '+' in sSearchText:
            oRequest.addParameters('c', '70')
        else:
            oRequest.addParameters('c', '')
    sHtmlContent = oRequest.request()
    pattern = 've-screen.*?title="([^"]+).*?url[^>]([^")]+).*?href="([^">]+)'
    isMatch, aResult = cParser.parse(sHtmlContent, pattern)

    if not isMatch:
        if not sGui: oGui.showInfo()
        return

    total = len(aResult)
    for sName, sThumbnail, sUrl in aResult:
        sName = sName.replace('(HD)', '')
        if sSearchText and not cParser().search(sSearchText, sName):
            continue
        if sThumbnail.startswith('/'):
            sThumbnail = URL_MAIN + sThumbnail
        oGuiElement = cGuiElement(sName, SITE_IDENTIFIER, 'showHosters')
        oGuiElement.setThumbnail(sThumbnail)
        oGuiElement.setMediaType('movie')
        params.setParam('entryUrl', URL_MAIN + sUrl)
        oGui.addFolder(oGuiElement, params, False, total)
    if not sGui:
        pattern = "spages[^>][^>]([^']+)[^>][^>];return[^>]false;[^>]><span>&raquo;.*?location.href = '([^']+)"
        aResult = cParser().parse(sHtmlContent, pattern)
        if aResult[0] and aResult[1][0]:
            for sNr, Url in aResult[1]:
                params.setParam('sUrl', URL_MAIN + Url + sNr)
                oGui.addNextPage(SITE_IDENTIFIER, 'showEntries', params)
        oGui.setView('movies')
        oGui.setEndOfDirectory()


def showHosters():
    hosters = []
    params = ParameterHandler()
    sUrl = params.getValue('entryUrl')
    sHtmlContent = cRequestHandler(sUrl).request()
    isMatch, sUrl = cParser().parse(sHtmlContent, 'class="link"[^>]href="([^"]+)')
    if isMatch:
        sHtmlContent2 = cRequestHandler(sUrl[0]).request()
        isMatch, aResult = cParser().parse(sHtmlContent2, 'p><iframe.*?src="([^"]+)')
    if isMatch:
        for sUrl in aResult:
            if sUrl.startswith('//'):
                sUrl = 'https:' + sUrl
            hoster = {'link': sUrl, 'name': cParser.urlparse(sUrl)}
            hosters.append(hoster)
    if hosters:
        hosters.append('getHosterUrl')
    return hosters


def getHosterUrl(sUrl=False):
    if 'youtube' in sUrl:
        import xbmc
        if not xbmc.getCondVisibility('System.HasAddon(%s)' % 'plugin.video.youtube'):
            xbmc.executebuiltin('InstallAddon(%s)' % 'plugin.video.youtube')
    return [{'streamUrl': sUrl, 'resolved': False}]


def showSearch():
    sSearchText = cGui().showKeyBoard()
    if not sSearchText: return
    showEntries(URL_SEARCH, False, sSearchText)
    cGui().setEndOfDirectory()


def _search(oGui, sSearchText):
    pass
