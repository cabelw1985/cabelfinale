# -*- coding: utf-8 -*-

#2022-01-14

import re
from resources.lib.control import  getSetting, urljoin, setSetting
from resources.lib.requestHandler import cRequestHandler
from scrapers.modules import cleantitle, dom_parser, source_utils
import datetime
date = datetime.date.today()
currentyear = int(date.strftime("%Y"))

class source:
    def __init__(self):
        self.priority = 2
        self.language = ['de']
        self.domains = ['serien.sx']
        self.base_link = 'http://190.115.18.20'
        #self.domains, self.base_link = self.getdomain()
        self.search_link = '/serien'
        self.login = getSetting('serienstream.user')
        self.password = getSetting('serienstream.pass')
        self.sources = []

    def getdomain(self, check=False):
        if getSetting('serienstream.base_link') and check == False: return [getSetting('serienstream.domain')], getSetting('serienstream.base_link')
        url ='https://serien.domains/'
        r = cRequestHandler(url).request()
        links = dom_parser.parse_dom(r, "ol", attrs={"class": "links"})
        links = dom_parser.parse_dom(links, "a")
        links = [(i.attrs["href"], i.content) for i in links]
        for i in links:
            link = source_utils.check_302(i[0])
            if link == i[0]:
                base_link = i[0]
                domains = i[1]
                setSetting('serienstream.domain', domains)
                setSetting('serienstream.base_link', base_link)
                if check:
                    self.domains = [domains]
                    self.base_link = base_link
                    return self.domains, self.base_link
                return [domains], base_link
        return ['serienstream.to'], 'https://serienstream.to'


    def run(self, titles, year, season=0, episode=0, imdb='', hostDict=None):
        sources = []
        if season == 0: return sources
        try:
            t = [cleantitle.get(i) for i in titles if i]
            url = urljoin(self.base_link, self.search_link)
            #url = urljoin('https://sus.to', self.search_link) # for test only
            sHtmlContent = cRequestHandler(url).request()
            if not self.base_link in str(dom_parser.parse_dom(sHtmlContent, "meta", attrs={"property": "og:url"})):
                self.getdomain(True) #new self.base_link
                url = urljoin(self.base_link, self.search_link)
                sHtmlContent = cRequestHandler(url).request()

            links = dom_parser.parse_dom(sHtmlContent, "div", attrs={"class": "genre"})
            links = dom_parser.parse_dom(links, "a")
            links = [(i.attrs["href"], i.content) for i in links]
            #links = [i for i in links if cleantitle.get(i[1]) in t or any([a in cleantitle.get(i[1]) for a in t])]
            url = ''
            aLinks = []
            for i in links:
                try:
                    if cleantitle.get(i[1]) in t:
                        #print (i[1])
                        url = i[0]
                        break
                except:
                    pass

            if url == '':
                for i in links:
                    for a in t:
                        try:
                            if any([a in cleantitle.get(i[1])]):
                                aLinks.append({'source': i[0]})
                                break
                        except:
                            pass

            if url == '':
                if len(aLinks) > 0:
                    for i in aLinks:
                        url = i['source']
                        self.run2(url, year, season=season, episode=episode, hostDict=hostDict)
                else:
                    return sources
            else:
                self.run2(url, year, season=season, episode=episode, hostDict=hostDict)
        except:
            return sources
        return self.sources

    def run2(self, url, year, season=0, episode=0, hostDict=None):
        try:
            url = url[:-1] if url.endswith('/') else url
            if "staffel" in url:
                url = re.findall("(.*?)staffel", url)[0]
            url += '/staffel-%d/episode-%d' % (int(season), int(episode))
            url = urljoin(self.base_link, url)
            sHtmlContent = cRequestHandler(url).request()
            startDate = dom_parser.parse_dom(sHtmlContent, 'span', attrs={'itemprop': 'startDate'})
            startDate = int(dom_parser.parse_dom(startDate[0].content, 'a')[0].content)
            endDate = dom_parser.parse_dom(sHtmlContent, 'span', attrs={'itemprop': 'endDate'})
            endDate = dom_parser.parse_dom(endDate[0].content, 'a')[0].content
            endDate = currentyear if endDate == 'Heute' else int(endDate)
            if not startDate <= year <= endDate: return
            r = dom_parser.parse_dom(sHtmlContent, 'div', attrs={'class': 'hosterSiteVideo'})
            #r = dom_parser.parse_dom(r, 'li', attrs={'data-lang-key': re.compile('[1|2|3]')})
            r = dom_parser.parse_dom(r, 'li', attrs={'data-lang-key': re.compile('[1]')}) #- only german

            r = [(i.attrs['data-link-target'], dom_parser.parse_dom(i, 'h4'),
                  'subbed' if i.attrs['data-lang-key'] == '3' else '' if i.attrs['data-lang-key'] == '1' else 'English/OV' if i.attrs['data-lang-key'] == '2' else '') for i
                 in r]

            r = [(i[0], re.sub('\s(.*)', '', i[1][0].content), 'HD' if 'hd' in i[1][0][1].lower() else 'SD', i[2]) for i in r]

            for link, host, quality, info in r:
                quality = 'HD' # temp
                valid, host = source_utils.is_host_valid(host, hostDict)
                if not valid: continue

                self.sources.append(
                    {'source': host, 'quality': quality, 'language': 'de', 'url': link, 'info': info, 'direct': False, 'priority': self.priority})

            return
        except:
            return

    def resolve(self, url):
        try:
            URL_LOGIN = urljoin(self.base_link, '/login')
            Handler = cRequestHandler(URL_LOGIN, caching=False)
            Handler.addHeaderEntry('Upgrade-Insecure-Requests', '1')
            Handler.addHeaderEntry('Referer', self.base_link)
            Handler.addParameters('email', self.login)
            Handler.addParameters('password', self.password)
            Handler.request()
            Request = cRequestHandler(self.base_link + url, caching=False)
            Request.addHeaderEntry('Referer', self.base_link)
            Request.addHeaderEntry('Upgrade-Insecure-Requests', '1')
            Request.request()
            url = Request.getRealUrl()

            if self.base_link in url:
                import xbmcgui, xbmcaddon
                AddonName = xbmcaddon.Addon().getAddonInfo('name')
                xbmcgui.Dialog().ok(AddonName, "- Geschützter Link - \nIn den Einstellungen die Kontodaten (Login) für Serienstream eintragen")
                return
            else:
                return url

        except:
            return

