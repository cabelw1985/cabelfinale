# -*- coding: utf-8 -*-
from resources.lib.handler.ParameterHandler import ParameterHandler
from resources.lib.handler.requestHandler import cRequestHandler
from resources.lib.tools import logger, cParser
from resources.lib.gui.guiElement import cGuiElement
from resources.lib.gui.gui import cGui

SITE_IDENTIFIER = 'filmpalast_to'
SITE_NAME = 'FilmPalast'
SITE_ICON = 'filmpalast.png'
URL_MAIN = 'https://filmpalast.to'
URL_MOVIES = URL_MAIN + '/movies/%s'
URL_SHOWS = URL_MAIN + '/serien/view'
URL_ENGLISH = URL_MAIN + '/search/genre/Englisch'
URL_SEARCH = URL_MAIN + '/search/title/%s'


def load():
    logger.info('Load %s' % SITE_NAME)
    params = ParameterHandler()
    params.setParam('sUrl', URL_MAIN)
    cGui().addFolder(cGuiElement('Neues', SITE_IDENTIFIER, 'showEntries'), params)
    cGui().addFolder(cGuiElement('Filme', SITE_IDENTIFIER, 'showMovieMenu'), params)
    cGui().addFolder(cGuiElement('Serien', SITE_IDENTIFIER, 'showSeriesMenu'), params)
    cGui().addFolder(cGuiElement('Suche', SITE_IDENTIFIER, 'showSearch'), params)
    cGui().setEndOfDirectory()


def showMovieMenu():
    params = ParameterHandler()
    params.setParam('sUrl', URL_MOVIES % 'new')
    cGui().addFolder(cGuiElement('Neuesten', SITE_IDENTIFIER, 'showEntries'), params)
    params.setParam('sUrl', URL_MOVIES % 'top')
    cGui().addFolder(cGuiElement('Hits', SITE_IDENTIFIER, 'showEntries'), params)
    params.setParam('sUrl', URL_MOVIES % 'votes')
    cGui().addFolder(cGuiElement('Votes', SITE_IDENTIFIER, 'showEntries'), params)
    params.setParam('sUrl', URL_MOVIES % 'imdb')
    cGui().addFolder(cGuiElement('IMDB-Bewertung', SITE_IDENTIFIER, 'showEntries'), params)
    params.setParam('sUrl', URL_ENGLISH)
    cGui().addFolder(cGuiElement('Englisch', SITE_IDENTIFIER, 'showEntries'), params)
    params.setParam('sUrl', URL_MOVIES % 'new')
    params.setParam('value', 'genre')
    cGui().addFolder(cGuiElement('Genre', SITE_IDENTIFIER, 'showValue'), params)
    params.setParam('value', 'movietitle')
    cGui().addFolder(cGuiElement('A-Z', SITE_IDENTIFIER, 'showValue'), params)
    cGui().setEndOfDirectory()


def showSeriesMenu():
    params = ParameterHandler()
    params.setParam('sUrl', URL_SHOWS)
    cGui().addFolder(cGuiElement('Serien', SITE_IDENTIFIER, 'showEntries'), params)
    params.setParam('value', 'movietitle')
    cGui().addFolder(cGuiElement('A-Z', SITE_IDENTIFIER, 'showValue'), params)
    cGui().setEndOfDirectory()


def showValue():
    params = ParameterHandler()
    value = params.getValue("value")
    sHtmlContent = cRequestHandler(params.getValue('sUrl')).request()
    pattern = '<section[^>]id="%s">(.*?)</section>' % value
    isMatch, sContainer = cParser.parseSingleResult(sHtmlContent, pattern)
    if isMatch:
        isMatch, aResult = cParser.parse(sContainer, 'href="([^"]+)">([^<]+)')
    if not isMatch:
        cGui().showInfo()
        return

    for sUrl, sName in aResult:
        params.setParam('sUrl', sUrl)
        cGui().addFolder(cGuiElement(sName, SITE_IDENTIFIER, 'showEntries'), params)
    cGui().setEndOfDirectory()


def showEntries(entryUrl=False, sGui=False, sSearchText=False):
    oGui = sGui if sGui else cGui()
    params = ParameterHandler()
    if not entryUrl: entryUrl = params.getValue('sUrl')
    oRequest = cRequestHandler(entryUrl, ignoreErrors=(sGui is not False))
    sHtmlContent = oRequest.request()
    # will match movies from first page (filmpalast.to)
    pattern = '<article[^>]*>\s*<a href="([^"]+)" title="([^"]+)">\s*<img src=["\']([^"\']+)["\'][^>]*>(.*?)</article>'
    isMatch, aResult = cParser.parse(sHtmlContent, pattern)
    if not isMatch:
        # will match movies from specific pages (filmpalast.to/movies/new)
        # last match is just a dummy!
        pattern = '<a[^>]*href="([^"]*)"[^>]*title="([^"]*)"[^>]*>[^<]*<img[^>]*src=["\']([^"\']*)["\'][^>]*>\s*</a>(\s*)</article>'
        isMatch, aResult = cParser.parse(sHtmlContent, pattern)
    if not isMatch:
        # not needed anymore???
        pattern = '</div><a[^>]href="([^"]+)"[^>]title="([^"]+)">.*?src="([^"]+)(.*?)alt'
        isMatch, aResult = cParser.parse(sHtmlContent, pattern)
    if not isMatch:
        if not sGui: oGui.showInfo()
        return

    total = len(aResult)
    for sUrl, sName, sThumbnail, sDummy in aResult:
        isTvshow, aResult = cParser.parse(sName, 'S\d\dE\d\d')
        # seriesname should not be crippled here!
        if sSearchText and not cParser().search(sSearchText, sName):
            continue
        if sThumbnail.startswith('/'):
            sThumbnail = URL_MAIN + sThumbnail
        isYear, sYear = cParser.parseSingleResult(sDummy, 'Jahr:[^>]([\d]+)')
        isDuration, sDuration = cParser.parseSingleResult(sDummy, '[Laufzeit][Spielzeit]:[^>]([\d]+)')
        isRating, sRating = cParser.parseSingleResult(sDummy, 'Imdb:[^>]([^<]+)')
        oGuiElement = cGuiElement(sName, SITE_IDENTIFIER, 'showSeasons' if isTvshow else 'showHosters')
        oGuiElement.setMediaType('tvshow' if isTvshow else 'movie')
        oGuiElement.setThumbnail(sThumbnail)
        if isYear:
            oGuiElement.setYear(sYear)
        if isDuration:
            oGuiElement.addItemValue('duration', sDuration)
        if isRating:
            oGuiElement.addItemValue('rating', sRating.replace(',', '.'))
        if sUrl.startswith('//'):
            params.setParam('entryUrl', 'https:' + sUrl)
        else:
            params.setParam('entryUrl', sUrl)
        params.setParam('sName', sName)
        params.setParam('sThumbnail', sThumbnail)
        oGui.addFolder(oGuiElement, params, isTvshow, total)
    if not sGui and not sSearchText:
        pattern = '<a class="pageing[^"]*"\s*href=([^>]+)>[^\+]+\+</a>\s*</div>'
        isMatchNextPage, sNextUrl = cParser.parseSingleResult(sHtmlContent, pattern)
        if isMatchNextPage:
            sNextUrl = sNextUrl.replace("'", "").replace('"', '')
            if sNextUrl.startswith('/'):
                sNextUrl = URL_MAIN + sNextUrl
            params.setParam('sUrl', sNextUrl)
            oGui.addNextPage(SITE_IDENTIFIER, 'showEntries', params)
        oGui.setView('tvshows' if isTvshow else 'movies')
        oGui.setEndOfDirectory()


def showSeasons():
    params = ParameterHandler()
    sUrl = params.getValue('entryUrl')
    sThumbnail = params.getValue("sThumbnail")
    sName = params.getValue('sName')
    sHtmlContent = cRequestHandler(sUrl).request()
    pattern = '<a[^>]*class="staffTab"[^>]*data-sid="(\d+)"[^>]*>'
    isMatch, aResult = cParser.parse(sHtmlContent, pattern)
    if not isMatch:
        cGui().showInfo()
        return

    isDesc, sDesc = cParser.parseSingleResult(sHtmlContent, '"description">([^<]+)')
    total = len(aResult)
    for sSeason in aResult:
        oGuiElement = cGuiElement('Staffel ' + str(sSeason), SITE_IDENTIFIER, 'showEpisodes')
        oGuiElement.setTVShowTitle(sName)
        oGuiElement.setSeason(sSeason)
        oGuiElement.setMediaType('season')
        oGuiElement.setThumbnail(sThumbnail)
        if isDesc:
            oGuiElement.setDescription(sDesc)
        cGui().addFolder(oGuiElement, params, True, total)
    cGui().setView('seasons')
    cGui().setEndOfDirectory()


def showEpisodes():
    params = ParameterHandler()
    sUrl = params.getValue('entryUrl')
    sThumbnail = params.getValue("sThumbnail")
    sSeason = params.getValue('season')
    sShowName = params.getValue('TVShowTitle')
    sHtmlContent = cRequestHandler(sUrl).request()
    pattern = '<div[^>]*class="staffelWrapperLoop[^"]*"[^>]*data-sid="%s">(.*?)</ul></div>' % sSeason
    isMatch, sContainer = cParser.parseSingleResult(sHtmlContent, pattern)
    if not isMatch:
        cGui().showInfo()
        return

    pattern = 'href="([^"]+)'
    isMatch, aResult = cParser.parse(sContainer, pattern)
    isDesc, sDesc = cParser.parseSingleResult(sHtmlContent, '"description">([^<]+)')
    total = len(aResult)
    for sUrl in aResult:
        isMatch, sName = cParser.parseSingleResult(sUrl, 'e(\d+)')
        oGuiElement = cGuiElement('Folge ' + str(sName), SITE_IDENTIFIER, 'showHosters')
        oGuiElement.setThumbnail(sThumbnail)
        oGuiElement.setTVShowTitle(sShowName)
        oGuiElement.setSeason(sSeason)
        oGuiElement.setEpisode(sName)
        oGuiElement.setMediaType('episode')
        if sUrl.startswith('//'):
            params.setParam('entryUrl', 'https:' + sUrl)
        else:
            params.setParam('entryUrl', sUrl)
        if isDesc:
            oGuiElement.setDescription(sDesc)
        cGui().addFolder(oGuiElement, params, False, total)
    cGui().setView('episodes')
    cGui().setEndOfDirectory()


def showHosters():
    sUrl = ParameterHandler().getValue('entryUrl')
    sHtmlContent = cRequestHandler(sUrl).request()
    pattern = 'hostName">([^<]+).*?(http[^"]+)'
    isMatch, aResult = cParser().parse(sHtmlContent, pattern)
    hosters = []
    if isMatch:
        for sName, sUrl in aResult:
            hoster = {'link': sUrl, 'name': sName}
            hosters.append(hoster)
    if hosters:
        hosters.append('getHosterUrl')
    return hosters


def getHosterUrl(sUrl=False):
    if 'vivo.php' in sUrl:
        oRequest = cRequestHandler(sUrl, caching=False)
        oRequest.addHeaderEntry('Referer', URL_MAIN)
        oRequest.request()
        return [{'streamUrl': oRequest.getRealUrl(), 'resolved': False}]
    else:
        return [{'streamUrl': sUrl, 'resolved': False}]


def showSearch():
    sSearchText = cGui().showKeyBoard()
    if not sSearchText: return
    _search(False, sSearchText)
    cGui().setEndOfDirectory()


def _search(oGui, sSearchText):
    showEntries(URL_SEARCH % cParser().quotePlus(sSearchText), oGui, sSearchText)
