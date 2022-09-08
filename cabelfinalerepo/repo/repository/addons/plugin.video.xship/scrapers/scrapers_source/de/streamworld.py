# -*- coding: UTF-8 -*-

# 2022-01-07

import re
from scrapers.modules.tools import cParser  # re - alternative
from resources.lib.requestHandler import cRequestHandler
from scrapers.modules import cleantitle, dom_parser, source_utils

# streamworld
class source:
    def __init__(self):
        self.priority = 1
        self.language = ['de']
        self.domains = ['streamworld.in']
        self.base_link = 'https://streamworld.in'
        self.search_link = self.base_link + '/index.php?do=search'
        self.sources = []

    def run(self, titles, year, season=0, episode=0, imdb='', hostDict=None):
        sources = []
        if season > 0: return sources
        url = None
        try:
            t = [cleantitle.get(i) for i in set(titles) if i]
            years = (year, year+1, year-1, 0)
            links = []
            for sSearchText in titles:
                try:
                    oRequest = cRequestHandler(self.search_link)
                    oRequest.addParameters('do', 'search')
                    oRequest.addParameters('subaction', 'search')
                    oRequest.addParameters('search_start', '0')
                    oRequest.addParameters('full_search', '0')
                    oRequest.addParameters('result_from', '1')
                    oRequest.addParameters('story', sSearchText)
                    oRequest.addParameters('titleonly', '3')
                    sHtmlContent = oRequest.request()
                    r = dom_parser.parse_dom(sHtmlContent, 'div', attrs={'id': 'dle-content'})[0].content
                    pattern = 'sres-wrap clearfix.*?href="([^"]+).*?alt="(.*?)\s+\((\d+)'
                    isMatch, aResult = cParser.parse(r, pattern)
                    if not isMatch:
                        continue

                    for sUrl, sName, sYear in aResult:
                        if cleantitle.get(sName) in t and int(sYear) in years:
                            links.append({'url': sUrl, 'name': sName, 'year': sYear})

                    if len(links) > 0: break
                except:
                    continue

            if len(links) == 0: return sources
            for link in links:
                sHtmlContent = cRequestHandler(link['url']).request()
                isMatch, aResult = cParser().parse(sHtmlContent, 'data-src="([^"]+)')
                if isMatch:
                    for sUrl in aResult:
                        if sUrl.startswith('/'): sUrl = 'https:' + sUrl
                        valid, hoster = source_utils.is_host_valid(sUrl, hostDict)
                        if not valid or 'youtube' in hoster: continue
                        sources.append({'source': hoster, 'quality': '720p', 'language': 'de', 'url': sUrl, 'direct': False})
            return sources
        except:
            return sources

    def resolve(self, url):
        try:
            return url
        except:
            return
