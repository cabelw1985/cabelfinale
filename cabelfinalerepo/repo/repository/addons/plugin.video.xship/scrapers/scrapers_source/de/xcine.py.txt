# -*- coding: UTF-8 -*-

#2022-01-09

import re, json
from resources.lib.requestHandler import cRequestHandler
from scrapers.modules import cleantitle, dom_parser
from scrapers.modules.tools import cParser
from resources.lib.control import urljoin, quote_plus

class source:
    def __init__(self):
        self.priority = 1
        self.language = ['de']
        self.domains = ['xcine.me']
        self.base_link = 'https://xcine.me/'
        self.search_link = '/search'    #?key=%s'
        self.search_api = self.base_link + '/search'
        self.get_link = 'movie/load-stream/%s/%s?'


    def run(self, titles, year, season=0, episode=0, imdb='', hostDict=None):
        sources = []
        links = []
        t = [cleantitle.get(i) for i in set(titles) if i]
        for title in titles:
            try:
                title = cleantitle.query(title)
                entryUrl = urljoin(self.base_link, self.search_link)    #'https://xcine.me/search'
                oRequest = cRequestHandler(entryUrl)
                oRequest.addHeaderEntry('Referer', self.base_link + '/')
                oRequest.addHeaderEntry('Host', self.domains[0])
                oRequest.addParameters('key',title)
                oRequest.addParameters('getInfo', 1)
                content = oRequest.request()
                if content == '[]': continue
                aJson = json.loads(content)['film']
                years = (year, 0) # xShip
                for item in aJson:
                    if not item['year'] in years: continue # xShip
                    title = cleantitle.get(item['name'])
                    if any(i in title for i in t):
                        if season == 0:
                            url = item['link'] + '/deutsch'
                            links.append({'sUrl': url, 'sName': item['name'], 'sThumbnail': item['poster'], 'sYear': item['year']})
                            break
                        else:
                            if not ("staffel0" + str(season) in title or "staffel" + str(season) in title): continue
                            url = item['link'] + '/folge-' + str(episode)
                            links.append({'sUrl': url, 'sName': item['name'], 'sThumbnail': item['poster'], 'sYear': item['year']})
                            break
                if len(links) > 0: break
            except:
                 pass

        try:
            #u'https://hdfilme.cc/the-poison-rose-dunkle-vergangenheit-14882-stream/deutsch'
            #u'https://xcine.me/serien-vikings-staffel-01-1942-stream/folge-1'
            url = links[0]['sUrl']
            if not url: return sources
            query = urljoin(self.base_link, url)
            oRequest = cRequestHandler(query)
            #oRequest.addHeaderEntry('Host', self.domains[0])
            oRequest.addHeaderEntry('Upgrade-Insecure-Requests', '1')
            sHtmlContent = oRequest.request()
            pattern = 'data-movie-id="(\d+).*?data-episode-id="(\d+)"'
            isMatch, aResult = cParser().parse(sHtmlContent, pattern)
            if isMatch:
                movie_id = aResult[0][0]
                episode_id = aResult[0][1]
            else: return sources

            #'movie/load-stream/14882/130355?'
            link = self.get_link % (movie_id,episode_id )
            link = urljoin(self.base_link, link)
            oRequest = cRequestHandler(link)
            oRequest.addHeaderEntry('Referer', urljoin(self.base_link, url))
            oRequest.addHeaderEntry('Host', self.domains[0])
            oRequest.addHeaderEntry('X-Requested-With', 'XMLHttpRequest')
            moviesource = oRequest.request()
            if not moviesource: return sources

            #'https://load.hdfilme.ws/playlist/203829575d4e8d6602a69a746d7dacf4/203829575d4e8d6602a69a746d7dacf4.m3u8'
            isMatch, hUrl = cParser().parse(moviesource, 'urlVideo = "([^"]+)')
            if not isMatch: return sources
            m3u8_url =  hUrl[0]
            m3u8_base_url = m3u8_url.rpartition('/')[0]
            oRequest = cRequestHandler(m3u8_url)
            #oRequest.addHeaderEntry('Referer', urljoin(self.base_link, url))
            #oRequest.addHeaderEntry('Origin', self.domains[0])
            sHtmlContent = oRequest.request()
            pattern = 'RESOLUTION=([0-9,x]+)([^#]+)'
            isMatch, aResult = cParser().parse(sHtmlContent, pattern)
            if isMatch:
                for _quality, url in aResult:
                    if not 'http' in url: url = m3u8_base_url+'/'+ url

                    if "1080" in _quality or "1920" in _quality:
                        quality = "1080p"
                    elif "720" in _quality or "1280" in _quality:
                        quality = "720p"
                    else:
                        quality = 'SD'
                    sources.append({'source': 'XCINE.ME', 'quality': quality, 'language': 'de',
                                        'url': url, 'direct': True, 'debridonly': False, 'local': True})

            return sources
        except:
            return sources


    def resolve(self, url):
        try:
            user_agent = 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:76.0) Gecko/20100101 Firefox/76.0'
            return url + '|User-Agent=' + user_agent
        except:
            return


