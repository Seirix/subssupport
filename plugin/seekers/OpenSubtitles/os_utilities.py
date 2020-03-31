# -*- coding: utf-8 -*-

import xmlrpclib
import json
import urllib2,urllib,re
import requests
from ..utilities import languageTranslate, log

__scriptname__ = 'XBMC Subtitles'
__version__ = '4.0.0'

BASE_URL_XMLRPC = u"http://api.opensubtitles.org/xml-rpc"
BASE_URL = u"https://rest.opensubtitles.org/search"

class OSDBServer:
    def xmlRPCLogin(self):
        self.server = xmlrpclib.Server(BASE_URL_XMLRPC, verbose=0)
        login = self.server.LogIn("", "", "en", "%s_v%s" % (__scriptname__.replace(" ", "_"), __version__))
        self.osdb_token = login[ "token" ]

    def mergesubtitles(self):
        self.subtitles_list = []
        if(len(self.subtitles_hash_list) > 0):
            for item in self.subtitles_hash_list:
                if item["format"].find("srt") == 0 or item["format"].find("sub") == 0:
                    self.subtitles_list.append(item)

        if(len(self.subtitles_list) > 0):
            self.subtitles_list.sort(
                key=lambda x: [not x['sync'], x['lang_index']])

    def searchsubtitles(self, title, tvshow, year, season, episode, lang1, lang2, lang3, hash_search, _hash="000000000", size="000000000"):
        msg = ""
        lang_index = 3
        search_parameters = {}
        self.subtitles_hash_list = []
        self.langs_ids = [languageTranslate(lang1, 0, 2), languageTranslate(
            lang2, 0, 2), languageTranslate(lang3, 0, 2)]
        language = [languageTranslate(lang1, 0, 3)]
        if lang1 != lang2:
            language.append(languageTranslate(lang2, 0, 3))
        if lang3 != lang1 and lang3 != lang2:
            language.append(languageTranslate(lang3, 0, 3))

        try:
            for lang in language:
                search_parameters.update({'sublanguageid': lang})

                if hash_search:
                    search_parameters.update({'moviehash': _hash})
                    search_parameters.update({'moviebytesize': str(size)})
                else:
                    if not (tvshow == None or tvshow == ''):
                        search_parameters.update({'query': tvshow})
                    else:
                        search_parameters.update({'query': title})

                    if not (season == None or season == ''):
                        search_parameters.update({'season': season})
                    if not (episode == None or episode == ''):
                        search_parameters.update({'episode': episode})

                search_parameters_url = ['-'.join([key, urllib.quote_plus(str(val), '-')]) for key, val in search_parameters.iteritems()]
                search_parameters_url =  '/'.join(search_parameters_url).lower()

                url = BASE_URL + '/' + search_parameters_url

                result = self.sendRequest(url)

                if result:
                    search = result.json()
                    for item in search:
                        log(__name__,'New subtitle found '+ item["SubFileName"])
                        if not (year == None or year == '') and (item["MovieYear"] != year):
                            continue
                        if item["ISO639"]:
                            lang_index = 0
                            for user_lang_id in self.langs_ids:
                                if user_lang_id == item["ISO639"]:
                                    break
                                lang_index += 1
                            flag_image = "flags/%s.gif" % item["ISO639"]
                        else:
                            flag_image = "-.gif"

                        if str(item["MatchedBy"]) == "moviehash":
                            sync = True
                        else:
                            sync = False
                        self.subtitles_hash_list.append({
                            'lang_index': lang_index,
                            'filename': item["SubFileName"],
                            'link': item["ZipDownloadLink"],
                            'language_name': item["LanguageName"],
                            'language_flag': flag_image,
                            'language_id': item["SubLanguageID"],
                            'ID': item["IDSubtitleFile"],
                            'rating': str(int(item["SubRating"][0])),
                            'format': item["SubFormat"],
                            'sync': sync,
                            'hearing_imp': int(item["SubHearingImpaired"]) != 0,
                            'fps': item.get('MovieFPS')
                        })

        except Exception as e:
            msg = "Error Searching For Subs: %s" % str(e)

        self.mergesubtitles()
        return self.subtitles_list, msg

    def downloadByLink(self, link, dest):
        try:
            from StringIO import StringIO
            import zipfile
            log(__name__,'Downloading by link %s' % (link))
            res = urllib2.urlopen(link)
            subtitleZipFile = zipfile.ZipFile(StringIO(res.read()))
            subExtensions = ('.srt')
            for oneFile in subtitleZipFile.namelist():
                if oneFile.endswith(subExtensions):
                    data = subtitleZipFile.open(oneFile).read()
                    local_file = open(dest, 'wb')
                    local_file.write(data)
                    local_file.close()
                    return True
            return False
        except Exception as e:
            log(__name__,'Error downloading by link %s' % (e.message))
            return False

    def download(self, ID, dest, token):
        try:
            import zlib, base64
            self.xmlRPCLogin()
            down_id = [ID, ]
            log(__name__,'Downloading %s' % (dest))
            result = self.server.DownloadSubtitles(self.osdb_token, down_id)
            if result["data"]:
                local_file = open(dest, "w" + "b")
                d = zlib.decompressobj(16 + zlib.MAX_WBITS)
                data = d.decompress(base64.b64decode(result["data"][0]["data"]))
                local_file.write(data)
                local_file.close()
                return True
            return False
        except Exception as e:
            log(__name__,'Error downloading %s' % (e.message))
            return False

    def sendRequest(self, url):
        log(__name__,'Opening %s' % (url))
        headers = requests.utils.default_headers()
        headers.update({'User-Agent': "%s_v%s" % (__scriptname__.replace(" ", "_"), __version__)})
        response = requests.get(url, headers=headers)
        log(__name__,'Done')
        return response
