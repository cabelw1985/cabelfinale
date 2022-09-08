# -*- coding: utf-8 -*-

# 2022-01-09

import json
import re
import time
import requests
import resolveurl as resolver

from scrapers.modules.tools import cParser  # re - alternative
from resources.lib.requestHandler import cRequestHandler
from resources.lib.control import urlparse, quote_plus, urljoin, parse_qs, getSetting, setSetting
from scrapers.modules import cleantitle, dom_parser, source_utils

# kinox
class source:
    def __init__(self):
        self.priority = 1
        self.language = ['de']
        self.domains, self.base_link = self.getdomain()
        #self.domains = ['KinoX.to', 'ww8.kinox.to', 'ww1.kinox.to', 'kinoS.TO', 'kinox.TV', 'kinox.ME', 'kinoz.TO', 'kinox.IO', 'kinox.SX', 'kinox.AM', 'kinox.NU', 'kinox.SG', 'kinox.GRATIS', 'kinox.MOBI', 'kinox.SH', 'kinox.LOL', 'kinox.WTF', 'kinox.FUN', 'kinox.FYI', 'kinox.CLOUD', 'kinox.AI', 'kinox.CLICK', 'kinox.TUBE', 'kinox.CLUB', 'kinox.DIGITAL', 'kinox.DIRECT', 'kinox.PUB', 'kinox.EXPRESS', 'kinox.PARTY', 'kinox.BZ']
        #self.domains = ['kinos.to', 'kinox.tv', 'kinox.to', 'kinox.nu', 'kinox.sh']
        #self.base_link = self._base_link
        self.search_link = self.base_link +'/Search.html?q=%s'
        self.get_links_epi = '/aGET/MirrorByEpisode/?Addr=%s&SeriesID=%s&Season=%s&Episode=%s'
        self.mirror_link = '/aGET/Mirror/%s&Hoster=%s&Mirror=%s'
        self.checkHoster = False if getSetting('provider.kinox.checkHoster') == 'false' else True
        self.sources = []

    def getdomain(self, check=False):
        if getSetting('kinox.base_link') and check == False: return [getSetting('kinox.domain')], getSetting('kinox.base_link')
        domains = ['KinoX.to', 'ww8.kinox.to', 'ww1.kinox.to', 'kinoS.TO', 'kinox.TV', 'kinox.ME', 'kinoz.TO', 'kinox.IO', 'kinox.SX', 'kinox.AM', 'kinox.NU', 'kinox.SG', 'kinox.GRATIS', 'kinox.MOBI', 'kinox.SH', 'kinox.LOL', 'kinox.WTF', 'kinox.FUN', 'kinox.FYI', 'kinox.CLOUD', 'kinox.AI', 'kinox.CLICK', 'kinox.TUBE', 'kinox.CLUB', 'kinox.DIGITAL', 'kinox.DIRECT', 'kinox.PUB', 'kinox.EXPRESS', 'kinox.PARTY', 'kinox.BZ']
        for domain in domains:
            try:
                url = 'http://%s' % domain
                resp = requests.get(url)
                url = resp.url
                if resp.status_code == 200:
                    r = dom_parser.parse_dom(resp.text, 'meta', attrs={'name': 'keywords'}, req='content')
                    if r and 'kinox.to' in r[0].attrs.get('content').lower():
                        setSetting('kinox.domain', urlparse(url).netloc)
                        setSetting('kinox.base_link', url[:-1])
                        if check:
                            self.domains = [urlparse(url).netloc]
                            self.base_link = url[:-1]
                            return self.domains, self.base_link
                        return  [urlparse(url).netloc], url[:-1]
            except:
                pass

    def run(self, titles, year, season=0, episode=0, imdb='', hostDict=None):
        sources = []
        url = ''
        t = [cleantitle.get(i) for i in set(titles) if i]
        for title in titles:
            try:
                query = self.search_link % (quote_plus(title))
                oRequest = cRequestHandler(query)
                sHtmlContent = oRequest.request()
                if not sHtmlContent:
                    self.getdomain(True)
                    query = self.search_link % (quote_plus(title))
                    sHtmlContent = cRequestHandler(query).request()

                r = dom_parser.parse_dom(sHtmlContent, 'table', attrs={'id': 'RsltTableStatic'})
                r = dom_parser.parse_dom(r, 'tr')
                r = [(dom_parser.parse_dom(i, 'a', req='href'), dom_parser.parse_dom(i, 'img', attrs={'alt': 'language'}, req='src'), dom_parser.parse_dom(i, 'span')) for i in r]
                r = [(i[0][0].attrs['href'], i[0][0].content, i[1][0].attrs['src'], i[2][0].content) for i in r if i[0] and i[1]]
                if season:
                    r = [(i[0], i[1], re.findall('.+?(\d+)\.', i[2]), i[3]) for i in r]
                else:
                    r = [(i[0], i[1], re.findall('.+?(\d+)\.', i[2]), i[3]) for i in r if i[3] == str(year)]
                r = [(i[0], i[1], i[2][0] if len(i[2]) > 0 else '0', i[3]) for i in r]
                r = sorted(r, key=lambda i: int(i[2]))  # german > german/subbed
                r = [i[0] for i in r if i[2] in ['1', '15'] and cleantitle.get(i[1]) in t]

                if len(r) == 0:
                    continue
                else:
                    url = urljoin(self.base_link,r[0])
                    break
            except:
                pass

        try:
            if not url:
                return sources
            oRequest = cRequestHandler(url)
            sHtmlContent = oRequest.request()
            if season and episode:
                r = dom_parser.parse_dom(sHtmlContent, 'select', attrs={'id': 'SeasonSelection'}, req='rel')[0]
                r = source_utils.replaceHTMLCodes(r.attrs['rel'])[1:]
                r = parse_qs(r)
                r = dict([(i, r[i][0]) if r[i] else (i, '') for i in r])
                r = urljoin(self.base_link, self.get_links_epi % (r['Addr'], r['SeriesID'], season, episode))
                oRequest = cRequestHandler(r)
                sHtmlContent = oRequest.request()

            r = dom_parser.parse_dom(sHtmlContent, 'ul', attrs={'id': 'HosterList'})[0]
            r = dom_parser.parse_dom(r, 'li', attrs={'id': re.compile('Hoster_\d+')}, req='rel')
            r = [(source_utils.replaceHTMLCodes(i.attrs['rel']), i.content) for i in r if i[0] and i[1]]
            r = [(i[0], re.findall('class="Named"[^>]*>([^<]+).*?(\d+)/(\d+)', i[1])) for i in r]
            r = [(i[0], i[1][0][0].lower().rsplit('.', 1)[0], i[1][0][2]) for i in r if len(i[1]) > 0]

            if self.checkHoster:
                from resources.lib import workers
                threads = []
                for link, hoster, mirrors in r:
                    valid, hoster = source_utils.is_host_valid(hoster, hostDict)
                    if not valid:
                        continue
                    threads.append(workers.Thread(self.chk_mirror, link, hoster, mirrors, hostDict, season, episode))
                [i.start() for i in threads]
                [i.join() for i in threads]
            else:
                for link, hoster, mirrors in r:
                    valid, hoster = source_utils.is_host_valid(hoster, hostDict)
                    if not valid: continue
                    u = parse_qs('&id=%s' % link)
                    u = dict([(x, u[x][0]) if u[x] else (x, '') for x in u])
                    for x in range(0, int(mirrors)):
                        tempLink = self.mirror_link % (u['id'], u['Hoster'], x + 1)
                        if season and episode: tempLink += "&Season=%s&Episode=%s" % (season, episode)
                        try:
                            self.sources.append({'source': hoster, 'quality': 'SD', 'language': 'de', 'url': tempLink, 'direct': False, 'debridonly': False})
                        except:
                            pass
            return self.sources
        except:
            return self.sources

    def chk_mirror(self, link, hoster, mirrors, hostDict, season, episode):
        u = parse_qs('&id=%s' % link)
        u = dict([(x, u[x][0]) if u[x] else (x, '') for x in u])
        for x in range(0, int(mirrors)):
            tempLink = self.mirror_link % (u['id'], u['Hoster'], x + 1)
            if season and episode: tempLink += "&Season=%s&Episode=%s" % (season, episode)
            url = urljoin(self.base_link, tempLink)
            oRequest = cRequestHandler(url)
            sHtmlContent = oRequest.request()
            if len(sHtmlContent) < 20:
                time.sleep(1)  # ka - Abfrage verzögern!  Workaround - 2x - so geht es
                oRequest = cRequestHandler(url)
                sHtmlContent = oRequest.request()
            r = json.loads(sHtmlContent)['Stream']
            r = [(dom_parser.parse_dom(r, 'a', req='href'), dom_parser.parse_dom(r, 'iframe', req='src'))]
            r = [i[0][0].attrs['href'] if i[0] else i[1][0].attrs['src'] for i in r if i[0] or i[1]][0]
            if not r.startswith('http'): r = urljoin('https:', r)
            hmf = resolver.HostedMediaFile(url=r, include_disabled=True, include_universal=False)
            if hmf.valid_url():
                url = hmf.resolve()
                if url: self.sources.append({'source': hoster, 'quality': 'SD', 'language': 'de', 'url': url, 'direct': True, 'debridonly': False})

    def resolve(self, url):
        if self.checkHoster: return url
        try:
            url = urljoin(self.base_link, url)
            oRequest = cRequestHandler(url)
            sHtmlContent = oRequest.request()
            if len(sHtmlContent) < 20:
                time.sleep(1)  # ka - Abfrage verzögern!  Workaround - 2x - so geht es
                oRequest = cRequestHandler(url)
                sHtmlContent = oRequest.request()
            r = json.loads(sHtmlContent)['Stream']
            r = [(dom_parser.parse_dom(r, 'a', req='href'), dom_parser.parse_dom(r, 'iframe', req='src'))]
            r = [i[0][0].attrs['href'] if i[0] else i[1][0].attrs['src'] for i in r if i[0] or i[1]][0]

            if not r.startswith('http'): r = urljoin('https:', r)
            url = self.check_302(r)
            return url
        except:
            return

    def check_302(self, url):
        try:
            while True:
                host = urlparse(url).netloc
                headers_dict = {'Host': host}
                r = requests.get(url, allow_redirects=False, headers=headers_dict, timeout=7)
                if 300 <= r.status_code <= 400: url = r.headers['Location']
                elif 400 <= r.status_code: url = ''
                else: break

            return url
        except:
            return



