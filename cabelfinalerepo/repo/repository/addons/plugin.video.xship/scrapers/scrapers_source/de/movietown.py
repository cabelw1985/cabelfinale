# -*- coding: utf-8 -*-

# 2021-03-04

import json
from resources.lib.control import quote_plus
from resources.lib.requestHandler import cRequestHandler
from scrapers.modules import cleantitle,  source_utils


class source:
    def __init__(self):
        self.priority = 1
        self.language = ['de']
        self.domains = ['movietown.org']
        self.base_link = 'https://movietown.org'
        self.search_link = self.base_link + '/secure/search/%s?type=%s'
        self.movieLink = self.base_link + '/secure/titles/%s'
        self.serieLink = self.movieLink + '?titleId=%s&seasonNumber=%s&episodeNumber=%s'

    def run(self, titles, year, season=0, episode=0, imdb='', hostDict=None):
        sources = []
        url = ''
        type = 'movies' if season == 0 else 'series'
        try:
            t = [cleantitle.get(i) for i in set(titles) if i]
            for title in titles:
                query = self.search_link % (quote_plus(title), type)
                oRequest = cRequestHandler(query)
                sHtmlContent = oRequest.request()
                content = json.loads(sHtmlContent)['results']
                if season == 0:
                    result = [i for i in content if cleantitle.get(i['name']) in t and i['year'] == year]
                    if not result: continue
                    id = str(result[0]['id'])
                    url = self.movieLink % id
                else:
                    result = [i for i in content if cleantitle.get(i['name']) in t]
                    if not result: continue
                    id = str(result[0]['id'])
                    url = self.serieLink % (id, id, season, episode)

            if not url: return sources
            sHtmlContent = cRequestHandler(url).request()
            content = json.loads(sHtmlContent)
            links = content['title']['videos']
            links = [i for i in links if i['category'] == 'full']

            for link in links:
                hoster = link['url']
                quality = link['quality']
                if link['quality'].lower() == 'regular': quality = 'SD'
                if link['quality'].lower()  == 'hd': quality = 'HD'

                valid, host = source_utils.is_host_valid(hoster, hostDict)
                if not valid: continue
                sources.append({'source': host, 'quality': quality, 'language': 'de', 'url': hoster, 'direct': False})

            return sources
        except:
            return sources

    def resolve(self, url):
        return url

