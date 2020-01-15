# -*- coding: UTF-8 -*-

################################   Premium.Titulky.com #################################


import os

import time,calendar
import urllib2,urllib,re,cookielib
from ..utilities import languageTranslate, log, getFileSize

from ..seeker import SubtitlesDownloadError, SubtitlesErrors

def search_subtitles(file_original_path, title, tvshow, year, season, episode, set_temp, rar, lang1, lang2, lang3, stack ): #standard input
    client = PremiumTitulkyClient()
    login(client)
    # need to filter titles like <Localized movie name> (<Movie name>)
    br_index = title.find('(')
    if br_index > -1:
        title = title[:br_index]
    title = title.strip()
    session_id = "0"    
    subtitles_list = client.search_subtitles( file_original_path, title, tvshow, year, season, episode, set_temp, rar,'Czech','Slovak','EN' )
    return subtitles_list, session_id, ""  #standard output
    
def login(client):     
    username = settings_provider.getSetting("Titulkyuser")
    password = settings_provider.getSetting("Titulkypass")
    if password == '' or username == '':
        log(__name__,'Credentials to Premium.Titulky.com not provided. Check your username/password at the addon configuration')
        raise SubtitlesDownloadError(SubtitlesErrors.NO_CREDENTIALS_ERROR,
                                          "Credentials to Premium.Titulky.com not provided. Check your username/password at the addon configuration")
        return True,subtitles_list[pos]['language_name'], ""
    else:
        if client.login(username,password) == False:
            log(__name__,'Login to Premium.Titulky.com failed. Check your username/password at the addon configuration')
            raise SubtitlesDownloadError(SubtitlesErrors.INVALID_CREDENTIALS_ERROR,
                                          "Login to Premium.Titulky.com failed. Check your username/password at the addon configuration")
            return True,subtitles_list[pos]['language_name'], ""
        log(__name__,'Login successfull')
    return True

def download_subtitles (subtitles_list, pos, zip_subs, tmp_sub_dir, sub_folder, session_id): #standard input
    client = PremiumTitulkyClient()
    login(client)
    subtitle_id = subtitles_list[pos]['ID']       
    
    log(__name__,'Downloading subtitle zip')
    data = client.get_file(subtitle_id)
    log(__name__,'Saving to file %s' % zip_subs)
    zip_file = open(zip_subs,'wb')
    zip_file.write(data)
    zip_file.close()
    return True,subtitles_list[pos]['language_name'], "zip" #standard output

def lang_titulky2xbmclang(lang):
    if lang == 'CZ': return 'Czech'
    if lang == 'SK': return 'Slovak'
    return 'English'

def lang_xbmclang2titulky(lang):
    if lang == 'Czech': return 'CZ'
    if lang == 'Slovak': return 'SK'
    return 'EN'

def get_episode_season(episode,season):
    return 'S%sE%s' % (get2DigitStr(int(season)),get2DigitStr(int(episode)))

def get2DigitStr(number):
    if number>9:
        return str(number)
    else:
        return '0'+str(number)

def lang2_opensubtitles(lang):
    lang = lang_titulky2xbmclang(lang)
    return languageTranslate(lang,0,2)

class PremiumTitulkyClient(object):

    def __init__(self):
        self.cookies = {}
        self.server_url = 'https://beta.titulky.com'
        self.LWPCookieJar = cookielib.LWPCookieJar()
        self.opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(self.LWPCookieJar))
        self.opener.addheaders = [('User-agent', 'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.2.3) Gecko/20100401 Firefox/3.6.3 ( .NET CLR 3.5.30729)')]
        urllib2.install_opener(self.opener)

    def login(self,username,password):
            log(__name__,'Logging in to Titulky.com')
            login_postdata = urllib.urlencode({'LoginName': username, 'LoginPassword': password, 'PermanentLog': '1'} )            
            response = self.opener.open(self.server_url + '/', login_postdata)
            
            log(__name__,'Got response')
            if response.read().find('BadLogin')>-1:
                return False

            log(__name__,'Storing Cookies')
            self.cookies = {}
            for cookie in self.LWPCookieJar:
                if cookie.name == 'SESSTITULKY':
                    self.cookies[cookie.name] = cookie.value                                       

            return True

    def search_subtitles(self, file_original_path, title, tvshow, year, season, episode, set_temp, rar, lang1, lang2, lang3 ):
        url = self.server_url+'/?'+urllib.urlencode({'Fulltext':title, 'action': 'search'})
        if not (tvshow == None or tvshow == ''):
            url = self.server_url+'/?'+urllib.urlencode({'Fulltext':tvshow, 'Serial':'S', 'Sezona':season, 'Epizoda': episode, 'action': 'search'})
        req = urllib2.Request(url)
        req = self.add_cookies_into_header(req)
        try:
            size = getFileSize(file_original_path)
            file_size='%.2f' % (float(size)/(1024*1024))
        except:
            file_size='-1'
        log(__name__,'Opening %s' % (url))
        response = urllib2.urlopen(req)
        content = response.read()
        response.close()
        log(__name__,'Done')
        subtitles_list = []

        log(__name__,'Searching for subtitles')
        max_group = 10
        group_index = 0
        for group_row in re.finditer('<tr class=\"pbl(.+?)</tr>', content, re.IGNORECASE | re.DOTALL):
            group_link_found = re.search('<a href=\"(?P<data>\.\/\?action=detail&id=(?P<id>\d+))\"',group_row.group(1),re.IGNORECASE | re.DOTALL )
            if group_link_found:
                try:
                    log(__name__,'New detail subtitle found')
                    reltive_url = self.format_relative_link(group_link_found.group('data'))
                    url = self.server_url+reltive_url
                    req = urllib2.Request(url)
                    req = self.add_cookies_into_header(req)
                    response = urllib2.urlopen(req)
                    group_content = response.read()
                    response.close()
                    item = self.parse_detail_main(group_content, group_link_found.group('id'))
                    if self.check_subtitle_lang(item, lang1, lang2, lang3):                                                 
                        subtitles_list.append(item)
                except Exception, e:
                    log(__name__,'Exception when parsing detail subtitle, all I got is  %s' % str(item))
                    
                for row in re.finditer('<tr class=\"pbl(.+?)</tr>', group_content, re.IGNORECASE | re.DOTALL):                    
                    log(__name__,'New alternative subtitle found')
                    try:
                        item = self.parse_detail_table_row(row)
                        if self.check_subtitle_lang(item, lang1, lang2, lang3):                                                 
                            subtitles_list.append(item)   
                    except Exception, e:
                        log(__name__,'Exception when parsing detail table row subtitle, all I got is  %s' % str(item))
                        continue
            group_index = group_index + 1
            if group_index > max_group:
                log(__name__,'Max group subtitle exceed')
                break
        return subtitles_list

    def parse_detail_table_row(self, table_row):
        item = {}
                
        item['ID'] = re.search('((.+?)</td>){5}[^>]+><input.*?name=\"TID\[\]\" value=\"(?P<data>[^\"]+)\"', table_row.group(1), re.IGNORECASE | re.DOTALL ).group('data')
        item['title'] = re.search('((.+?)</td>){1}[^>]+>.+?<a href=\"\./\?action=detail&id=\d+[^>]+\">(?P<data>[^<]+)', table_row.group(1), re.IGNORECASE | re.DOTALL ).group('data').strip()
        item['title'] = self.clean_html(item['title'])                
        tvshow_found = re.search('S\d\dE\d\d', item['title'], re.IGNORECASE | re.DOTALL )
        item['tvshow'] = tvshow_found.group() if tvshow_found else ""                                               
        item['year'] = ""
        item['downloads'] = ""
        item['lang'] = re.search('((.+?)</td>){1}[^>]+><img[^>]src=\"img/flag-(?P<data>\w{2})-small\.gif\"', table_row.group(1), re.IGNORECASE | re.DOTALL ).group('data')
        item['numberOfDiscs'] = "1"
        item['size'] = ''    
        item['language_flag'] = "flags/%s.gif" % (lang2_opensubtitles(item['lang']))   
        sync_found = re.search('((.+?)</td>){4}[^>]+><span[^>]+class=\"release_list\">(?P<data>[^<]+)', table_row.group(1) ,re.IGNORECASE | re.DOTALL )                                 
        item['filename'] = sync_found.group('data').strip()+".zip" if sync_found else item['title']+".zip"
        item['sync'] = True if sync_found else False
        item['mediaType'] = 'mediaType'
        item['rating'] = item['ID']
        item['language_name'] = lang_titulky2xbmclang(item['lang'])

        return item

    def clean_html(self, html):
        cleanr = re.compile('<.*?>|&([a-z0-9]+|#[0-9]{1,6}|#x[0-9a-f]{1,6});')
        raw_text = re.sub(cleanr, '', html)
        return raw_text 

    def parse_detail_main(self, content, id):
        item = {}
                
        item['ID'] = id
        item['title'] = re.search('<h1[^>]+>(?P<data>[^<]+)', content, re.IGNORECASE | re.DOTALL ).group('data').strip()                    
        tvshow_found = re.search('S\d\dE\d\d', item['title'], re.IGNORECASE | re.DOTALL )
        item['tvshow'] = tvshow_found.group() if tvshow_found else ""                                               
        item['year'] = re.search('<div class=\"rok\"[^>]?>(?P<data>[^<]+)', content, re.IGNORECASE | re.DOTALL ).group('data').strip()
        item['downloads'] = re.search('<div class=\"stazeno\"[^<]+[^>]+>(?P<data>[^<]+)', content, re.IGNORECASE | re.DOTALL ).group('data').strip()
        item['lang'] = re.search('<h2[^<]+<img[^>]?src=\"img/flag-(?P<data>\w{2})-big\.gif\">', content, re.IGNORECASE | re.DOTALL ).group('data')
        item['numberOfDiscs'] = "1"
        item['size'] = re.search('<div class=\"cd\dvelikost\"[^>]+?>(?P<data>[^<]+)', content, re.IGNORECASE | re.DOTALL ).group('data')     
        item['language_flag'] = "flags/%s.gif" % (lang2_opensubtitles(item['lang']))   
        sync_found = re.search('<div class=\"releas\"[^<]+[^>]+>(?P<data>[^<]+)', content, re.IGNORECASE | re.DOTALL )                                 
        item['filename'] = sync_found.group('data').strip()+".zip" if sync_found else item['title']+".zip"
        item['sync'] = True if sync_found else False
        item['mediaType'] = 'mediaType'
        item['rating'] = item['ID']
        item['language_name'] = lang_titulky2xbmclang(item['lang'])

        return item

    def check_subtitle_lang(self, item, lang1, lang2, lang3):
        lang = lang_titulky2xbmclang(item['lang'])
        if lang in [lang1,lang2,lang3]:
            return True
        else:
            log(__name__,'language does not match, ignoring %s' % str(item))
            return False
    
    def format_relative_link(self,link):
        return link.lstrip('.')     

    def get_file(self,subtitle_id):
        url = self.server_url+'/download.php?id='+subtitle_id
        log(__name__,'Downloading file %s' % (url))
        req = urllib2.Request(url)
        req = self.add_cookies_into_header(req)
        response = urllib2.urlopen(req)
        if response.headers.get('Set-Cookie'):
            phpsessid = re.search('PHPSESSID=(\S+);', response.headers.get('Set-Cookie'), re.IGNORECASE | re.DOTALL)
            if phpsessid:
                log(__name__, "Storing PHPSessionID")
                self.cookies['PHPSESSID'] = phpsessid.group(1)
        content = response.read()
        log(__name__,'Done')
        response.close()
        return content

    def add_cookies_into_header(self,request):
        cookies_string=""
        try:            
            cookies_string += "SESSTITULKY=" + self.cookies['SESSTITULKY']
        except KeyError:
            pass
        if 'PHPSESSID' in self.cookies:
            cookies_string += "; PHPSESSID=" + self.cookies['PHPSESSID']
        request.add_header('Cookie',cookies_string)
        return request