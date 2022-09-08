# -*- coding: UTF-8 -*-

#2021-07-19

import requests
import re, random, base64, ast
from resources.lib.utils import test_stream
from resources.lib.control import quote_plus, unquote_plus, urlparse, py2_encode, quote
from resources.lib.requestHandler import cRequestHandler
from scrapers.modules import dom_parser, source_utils, cleantitle, jsunpacker

# kinoger
class source:
    def __init__(self):
        self.priority = 1
        self.language = ['de']
        self.domains = ['kinoger.com']
        self.base_link = 'https://kinoger.com/'
        self.search = self.base_link + 'index.php?do=search&subaction=search&search_start=1&full_search=0&result_from=1&titleonly=3&story=%s'
        #self.search = self.base_link + '?do=search&subaction=search&titleonly=3&story=%s&x=5&y=11&submit=submit'
        # http://kinoger.to/index.php?do=search&subaction=search&search_start=1&full_search=0&result_from=1&titleonly=3&story=Captain%20Marvel


    def run(self, titles, year, season=0, episode=0, imdb='', hostDict=None):
        sources = []
        url = ''
        try:
            t = [cleantitle.get(i) for i in titles  if i]
            years = [str(year), str(year + 1)] if season == 0 else ['']
            for title in titles:
                try:
                    sUrl = self.search % quote_plus(title)
                    oRequest = cRequestHandler(sUrl)
                    oRequest.removeBreakLines(False)
                    oRequest.removeNewLines(False)
                    sHtmlContent = oRequest.request()

                    search_results = dom_parser.parse_dom(sHtmlContent, 'div', attrs={'class': 'title'})
                    search_results = dom_parser.parse_dom(search_results, 'a')
                    search_results = [(i.attrs['href'], i.content) for i in search_results]
                    search_results = [(i[0], re.findall('(.*?)\((\d+)', i[1])[0]) for i in search_results]

                    if season > 0:
                        for x in range(0, len(search_results)):
                            title = cleantitle.get(search_results[x][1][0])
                            if 'staffel' in title and any(k in title for k in t):
                                url = search_results[x][0]
                    else:
                        for x in range(0, len(search_results)):
                            title = cleantitle.get(search_results[x][1][0])
                            if any(k in title for k in t) and search_results[x][1][1] in years:
                                url = search_results[x][0]
                                break
                    if url != '': break
                except:
                    pass

            if url == '': return

            sHtmlContent = cRequestHandler(url).request()
            quali = re.findall('title="Stream.(.+?)"', sHtmlContent)
            links = re.findall('.show.+?,(\[\[.+?\]\])', sHtmlContent)
            if len(links) == 0: return sources

            if season > 0 and episode > 0:
                season = season - 1
                episode = episode - 1

            for i in range(0, len(links)):
                if 'playerx' in links[i]: continue #ka temp off
                if 'kinoger' in links[i]: continue #ka temp off
                direct = True
                pw = ast.literal_eval(links[i])
                url = (pw[season][episode]).strip()
                valid, host = source_utils.is_host_valid(url, hostDict)
                if valid: direct = False
                quality = quali[i]
                if quality == '': quality = 'SD'
                if quality == 'HD': quality = '720p'
                if quality == 'HD+': quality = '1080p'
                if 'sst' in url:
                    oRequest = cRequestHandler(url)
                    oRequest.addHeaderEntry('Referer', url)
                    sHtmlContent = oRequest.request()
                    #if sHtmlContent == '': continue
                    pattern = 'file:"(.*?)"'
                    sContainer = re.search(pattern, sHtmlContent)
                    pattern = '(\d+p).(http[^",]+)'
                    try:
                        for i in sContainer.group(0).split(","):
                            r = re.search(pattern, i)
                            url = r.group(2)
                            quality = r.group(1)
                            sources.append({'source': host, 'quality': quality, 'language': 'de',
                                            'url': url, 'direct': direct})
                    except:
                        continue

                sources.append({'source': host, 'quality': quality, 'language': 'de',
                                'url': url, 'direct': direct})

            return sources
        except:
            return sources


    def Quali(self, url):
        if 'start' in url: return '1080p'
        elif 'protonvideo' in url: return '1080p'
        elif 'kinoger' in url: return '720p'
        elif 'sst' in url: return '720p'
        else: return '720p'


    def resolve(self, url):
        try:
            user_agent = 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:76.0) Gecko/20100101 Firefox/76.0'
            headers = {'User-Agent': user_agent}

            if 'sst' in url:
                return url

            elif 'protonvideo' in url:
                ## Test Beispiele
                # url = 'https://protonvideo.to/iframe/c54f49e9f04c95b1e861b4f6fa6d04ee/'    # Variante 1
                # url = u'https://protonvideo.to/iframe/71b9f7e458e108b43eb2132ca8051652/'   # Variante 2
                referer = url
                oRequest = cRequestHandler('https://api.svh-api.ch/api/v4/player', ignoreErrors=True, jspost=True)
                oRequest.addParameters('idi', url.split('/')[4])
                oRequest.addParameters('token', self.aes(url.split('/')[4]))
                sHtmlContent = oRequest.request()
                if sHtmlContent == '': return

                # Variante 1
                pattern = '(\d+p)\]([^{"|\s|,}]+)'
                sContainer = re.findall(pattern, sHtmlContent)
                if len(sContainer) > 0:
                    for quality in ('1080p', '720p', '480p', '360p'):
                        for i in sContainer:
                            if quality in i[0]:
                                url = i[1]
                                if test_stream(url): # Test - es gibt viele url die nicht funzen
                                    return url
                else:
                    # Variante 2
                    pattern = 'file(?:":"|:")([^"]+)'
                    sContainer = re.findall(pattern, sHtmlContent)
                    url = sContainer[0]
                    if url.startswith("http"):
                        url = url
                    elif url.startswith("//"):
                        url = 'https:' + url
                    else:
                        url = 'https://' + url
                    if url: return url  + '|User-Agent=' + user_agent + '&Referer=' + referer

                return

            elif 'kinoger' in url:
                if '/e/' in url:    # u'https://kinoger.pw/e/2h2g1qjegjza.html'
                    apiurl = url.replace('/e/', '/play/')
                    oRequest = cRequestHandler(apiurl)
                    oRequest.addHeaderEntry('Referer', url)
                    sHtmlContent = oRequest.request()
                    if sHtmlContent == '': return
                    sHtmlContent = jsunpacker.unpack(sHtmlContent)
                    pattern = 'sources\s*:\s*\[{file:\s*"([^"]+)'
                    apiurl2 = re.search(pattern, sHtmlContent).group(1)
                    oRequest = cRequestHandler(apiurl2, ignoreErrors=True)
                    oRequest.addHeaderEntry('Referer', 'https://kinoger.pw/')
                    oRequest.addHeaderEntry('Origin', 'https://kinoger.pw')
                    sHtmlContent = oRequest.request()
                    pattern = 'RESOLUTION=\d+x(\d+).*?(http[^"]+)#'
                    data_links = re.findall(pattern, sHtmlContent)
                    best_quality = max(re.findall('RESOLUTION=\d+x(\d+)', sHtmlContent))
                    for i in data_links:
                        if i[0] == best_quality:
                            return i[1].replace('\\', '')

                else:   # u'https://kinoger.re/v/elz45t-z8ymj7p8'
                    mediaId = url.split("/")[-1:][0]
                    apiurl = 'https://kinoger.re/api/source/' + mediaId
                    oRequest = cRequestHandler(apiurl)
                    oRequest.addHeaderEntry('Referer', self.base_link[:-1])
                    oRequest.addParameters('r', self.base_link[:-1])
                    oRequest.addParameters('d', 'kinoger.re')
                    sHtmlContent = oRequest.request()
                    best_quality = max(re.findall('label.+?(\d+)', sHtmlContent))
                    data_links = re.findall('{"file":"(.+?)",.+?(\d+)p.+?}', sHtmlContent)
                    for i in data_links:
                        if i[1] == best_quality: url = i[0].replace('\\', '')

            elif 'start' in url: #'start.u-stream'
                a = ''
                import json
                t = url.split('/')
                ID = t[5]
                ID2 = t[4]
                token = self.encodeUrl(ID2 + ':' + ID)
                url2 = 'http://start.u-stream.in/ustGet.php?id=' + ID + '&token=' + token
                oRequest = cRequestHandler(url2)
                oRequest.addHeaderEntry('Referer', url)
                content = oRequest.request()
                t = json.loads(content)
                urls = []
                if 'url' in t and t['url']:
                    for u in t['url']:
                        a = self.decodeStr(u)
                        urls.append(a)

                    if len(urls) > 1:
                        for i in ('1080', '720', '480'):
                            for k in urls:
                                if i in k:
                                    url = self.check_302(k, headers)
                                    if url: return url

                    elif len(urls) == 1: return urls[0]
                    else: return a
                return
 
            return url
        except:
            return

    def decodeStr(self, text):
        ergebnis = ''
        k = text[-1]
        t0, t1 = self.keys(k)
        text = text[:-1]

        for i in range(len(text)):
            for ii in range(len(t0)):
                if text[i] in t0[ii]:
                    ergebnis = ergebnis + t1[ii]
                elif text[i] in t1[ii]:
                    ergebnis = ergebnis + t0[ii]
        return unquote_plus(base64.b64decode(ergebnis[::-1] + '==').decode())


    def encodeUrl(self, e):
        r = 0,
        n = ''
        t = 1
        a = (random.randint(2, 9))
        t0, t1 = self.keys(str(a))
        t = a + 5

        for r in range(len(e)):
            n += self.toString(ord(e[r]), t)
            n += '!'
        n = base64.b64encode(n[:-1].encode()).decode().replace('=', '')
        e = ''
        for i in range(len(n)):
            for ii in range(len(t0)):
                if n[i] in t0[ii]:
                    e = e + t1[ii]
                elif n[i] in t1[ii]:
                    e = e + t0[ii]
        return self.encodeStr(e + str(a))


    def encodeStr(self, text):
        ergebnis = ''
        k = str(random.randint(2, 7))
        t0, t1 = self.keys(k)
        text = quote_plus(text)
        text = base64.b64encode(text.encode())
        text = text.decode().replace('=', '')[::-1]

        for i in range(len(text)):
            for ii in range(len(t0)):
                if text[i] in t0[ii]:
                    ergebnis = ergebnis + t1[ii]
                elif text[i] in t1[ii]:
                    ergebnis = ergebnis + t0[ii]
        return ergebnis + k


    def toString(self, number, base):
        string = "0123456789abcdefghijklmnopqrstuvwxyz"
        if number < base:
            return string[number]
        else:
            return self.toString(number // base, base) + string[number % base]

    def keys(self, s):
        if s == '1':
            return ('54A80Ibc3VBdefWGTSFg1X7hEYNijZU', 'kQl2mCnDoMpOq9rHsPt6uLvawRxJyKz')
        if s == '2':
            return ('4YMHUe5OFZ7L2PEJ8fgKAh1RGiIj0kV', 'aTlNmCn3oBpDqSr9sbtWu6vcwdxXyQz')
        elif s == '3':
            return ('AN4YZVHTJEOeLS2fGaFghiKWjQMbIkl', 'Xmc1d3nCo7p5qBrUsDt9u8vRw6x0yPz')
        elif s == '4':
            return ('V6YD2ZNWaTefXgObhS3UcRAP4dIiJjK', 'k7l5mLnCoEpMqGrBsFtQuHv1w0x9y8z')
        elif s == '5':
            return ('OGAFaN985MDHTbYW7ceQfdIgZhJiXj3', 'kSl6mRn2oCpKqErPsUt1u0v4wLxByVz')
        elif s == '6':
            return ('cZXK8O3BS5NRedFPfLAg2U6hIiDj7VT', 'k9lQmJnWoGp1q0rCsatHuYvbw4xMyEz')
        elif s == '7':
            return ('UZQXTPHcVS7deEfWDgRMLh9iIa1Y0j2', 'klb3m8nOoBpNqKr5s6tJuAvCwGxFy4z')
        elif s == '8':
            return ('AZI4WCcKOdNJGF3YEa2eHfgb8hMiLjD', 'kUlPmBnSoVp5q7r6s9t1uTv0wQxRyXz')
        elif s == '9':
            return ('OWZYcP3adUNSbeCfJVghTQDRIiKjBkG', 'X5lMmFnAoLp1q7r6s0tHu2vEw9x4y8z')
        else:
            return ('', '')


    def check_302(self, url, headers):
        try:
            user_agent = 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:76.0) Gecko/20100101 Firefox/76.0'
            host = urlparse(url).netloc
            headers.update({'User-Agent': user_agent, 'Host': host, 'Range': 'bytes=0-',
                            'Connection': 'keep-alive',
                            'Accept': 'video/webm,video/ogg,video/*;q=0.9,application/ogg;q=0.7,audio/*;q=0.6,*/*;q=0.5'})
            r = requests.get(url, allow_redirects=False, headers=headers, timeout=7)
            if 300 <= r.status_code < 400: return r.headers['Location']
            if 400 <= r.status_code: return
            return url
        except:
            return

    def aes(self, txt):
        import base64
        from resources.lib import pyaes
        from binascii import unhexlify
        key = unhexlify('0123456789abcdef0123456789abcdef')
        iv = unhexlify('abcdef9876543210abcdef9876543210')
        aes = pyaes.Encrypter(pyaes.AESModeOfOperationCBC(key, iv))
        return base64.b64encode(aes.feed(txt) + aes.feed()).decode()

