# -*- coding: UTF-8 -*-

# 2022-01-09

import resolveurl as resolver
from scrapers.modules.tools import cParser  # re - alternative
from resources.lib.requestHandler import cRequestHandler
from scrapers.modules import cleantitle, dom_parser, source_utils
from resources.lib.control import getSetting


# movie4k-click
class source:
    def __init__(self):
        self.priority = 1
        self.language = ['de']
        self.domains = ['movie4k.wiki']
        self.base_link = 'https://movie4k.wiki' # https://www.movie4k.tech/
        #self.base_link = source_utils.check_302(self.base_link)
        self.search_link = 'https://www.movie4k.tech/index.php?do=search'
        self.checkHoster = False if getSetting('provider.movie4k-click.checkHoster') == 'false' else True
        self.sources = []

    def run(self, titles, year, season=0, episode=0, imdb='', hostDict=None):
        sources = []
        url = ''
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
                    pattern = 'article class.*?href="([^"]+).*?<h3>([^<]+).*?white">([^<]+)'
                    isMatch, aResult = cParser.parse(sHtmlContent, pattern)
                    if not isMatch:
                        continue

                    for sUrl, sName, sYear in aResult:
                        if season == 0:
                            if cleantitle.get(sName) in t and int(sYear) in years:
                                # url = sUrl
                                # break
                                links.append(sUrl)

                        else:
                            if cleantitle.get(sName.split('-')[0].strip()) in t and str(season) in sName.split('-')[1]:
                                links.append(sUrl)
                                break
                    if len(links) > 0: break
                except:
                    continue

            if len(links) == 0: return sources

            for url in links:
                sHtmlContent = cRequestHandler(url).request()
                isMatch, quality = cParser().parseSingleResult(sHtmlContent, 'Qualität:.*?span>([^<]+)')
                if season > 0:
                    pattern = '\s%s<.*?</ul>' % episode
                    isMatch, sHtmlContent = cParser.parseSingleResult(sHtmlContent, pattern)
                    if not isMatch: return sources

                isMatch, aResult = cParser().parse(sHtmlContent, 'link="([^"]+)">([^<]+)')

                if isMatch:
                    if self.checkHoster:
                        from resources.lib import workers
                        threads = []
                        for i in aResult:
                            # print(sUrl)
                            threads.append(workers.Thread(self.chk_link, i[0], i[1], quality, hostDict))
                        [i.start() for i in threads]
                        [i.join() for i in threads]
                        return self.sources

                    for sUrl, sName in aResult:
                        if 'railer' in sName: continue
                        if sUrl.startswith('/'): sUrl = 'https:' + sUrl
                        valid, hoster = source_utils.is_host_valid(sUrl, hostDict)
                        if not valid: continue
                        sources.append({'source': hoster, 'quality': quality, 'language': 'de', 'url': sUrl, 'direct': False})

            return sources
        except:
            return sources

    def chk_link(self, sUrl, sName, quality, hostDict):
        if 'railer' in sName: return
        if sUrl.startswith('/'): sUrl = 'https:' + sUrl
        valid, hoster = source_utils.is_host_valid(sUrl, hostDict)
        if not valid: return
        hmf = resolver.HostedMediaFile(url=sUrl, include_disabled=True, include_universal=False)
        if hmf.valid_url():
            url = hmf.resolve()
            if url: self.sources.append({'source': hoster, 'quality': quality, 'language': 'de', 'url': url, 'direct': True})

    def resolve(self, url):
        try:
            return url
        except:
            return
