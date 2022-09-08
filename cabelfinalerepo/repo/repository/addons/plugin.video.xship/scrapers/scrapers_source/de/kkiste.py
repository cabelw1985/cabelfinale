# -*- coding: UTF-8 -*-

# 2022-01-09

import resolveurl as resolver
from scrapers.modules.tools import cParser  # re - alternative
from resources.lib.requestHandler import cRequestHandler
from scrapers.modules import cleantitle, dom_parser, source_utils
from resources.lib.control import getSetting

# kkiste
class source:
    def __init__(self):
        self.priority = 1
        self.language = ['de']
        self.domains = ['kkiste.rest']
        self.base_link = 'https://kkiste.rest'
        #self.base_link = source_utils.check_302(self.base_link)
        self.search_link = self.base_link + '/index.php?do=search'
        self.checkHoster = False if getSetting('provider.kkiste.checkHoster') == 'false' else True
        self.sources = []

    def run(self, titles, year, season=0, episode=0, imdb='', hostDict=None):
        sources = []
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

                    pattern = 'h2>.*?href="([^"]+)">([^<]+).*?label-1">([^<]+).*?(\d{4})<'
                    isMatch, aResult = cParser.parse(r, pattern)
                    if not isMatch:
                        continue

                    for sUrl, sName, sQuality, sYear in aResult:
                        if season == 0:
                            if cleantitle.get(sName) in t and int(sYear) in years:
                                  links.append({'url': sUrl,'name': sName, 'quality': sQuality, 'year': sYear})
                        else:
                            if cleantitle.get(sName.split('-')[0].strip()) in t and str(season) in sName.split('-')[1]:
                                links.append({'url': sUrl, 'name': sName.split('-')[0].strip(), 'quality': sQuality, 'year': sYear})

                    if len(links) > 0: break
                except:
                    continue

            if len(links) == 0: return sources
            for link in links:
                sHtmlContent = cRequestHandler(link['url']).request()
                self.quality = link['quality']
                if season > 0:
                    pattern = '\s%s<.*?</ul>' % episode
                    isMatch, sHtmlContent = cParser.parseSingleResult(sHtmlContent, pattern)
                    if not isMatch: return sources
                isMatch, aResult = cParser().parse(sHtmlContent, 'link="([^"]+)">')
                if not isMatch: return sources
                if self.checkHoster:
                    from resources.lib import workers
                    threads = []
                    for sUrl in aResult:
                        #print(sUrl)
                        threads.append(workers.Thread(self.chk_link, sUrl, hostDict, season, episode))
                    [i.start() for i in threads]
                    [i.join() for i in threads]
                else:
                    for sUrl in aResult:
                        if sUrl.startswith('/'): sUrl = 'https:' + sUrl
                        valid, hoster = source_utils.is_host_valid(sUrl, hostDict)
                        if not valid or 'youtube' in hoster: continue
                        self.sources.append({'source': hoster, 'quality': link['quality'], 'language': 'de', 'url': sUrl, 'direct': False})

            return self.sources
        except:
            return self.sources

    def chk_link(self, sUrl, hostDict, season, episode):
        if sUrl.startswith('/'): sUrl = 'https:' + sUrl
        valid, hoster = source_utils.is_host_valid(sUrl, hostDict)
        if not valid or 'youtube' in hoster: return
        hmf = resolver.HostedMediaFile(url=sUrl, include_disabled=True, include_universal=False)
        if hmf.valid_url():
            url = hmf.resolve()
            if url: self.sources.append({'source': hoster, 'quality': self.quality, 'language': 'de', 'url': url, 'direct': True})


    def resolve(self, url):
        try:
            return url
        except:
            return
