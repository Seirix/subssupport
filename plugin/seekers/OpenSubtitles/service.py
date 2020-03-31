# -*- coding: utf-8 -*-

import os
from ..utilities import log, hashFile
from os_utilities import OSDBServer


def search_subtitles(file_original_path, title, tvshow, year, season, episode, set_temp, rar, lang1, lang2, lang3, stack):  # standard input
    hash_search = False

    if set_temp:
        hash_search = False
        file_size = "000000000"
        SubHash = "000000000000"
    else:
        try:
            file_size, SubHash = hashFile(file_original_path, rar)
            log(__name__, "xbmc module hash and size")
            hash_search = True
        except:
            file_size = ""
            SubHash = ""
            hash_search = False

    if file_size != "" and SubHash != "":
        log(__name__, "File Size [%s]" % file_size)
        log(__name__, "File Hash [%s]" % SubHash)

    log(__name__, "Search by hash and name %s" %
        (os.path.basename(file_original_path),))
    subtitles_list, msg = OSDBServer().searchsubtitles(title, tvshow, year, season,
                                                       episode, lang1, lang2, lang3, hash_search, SubHash, file_size)

    return subtitles_list, "", msg  # standard output


def download_subtitles(subtitles_list, pos, zip_subs, tmp_sub_dir, sub_folder, session_id):  # standard input
    destination = os.path.join(tmp_sub_dir, "%s.srt" %
                               subtitles_list[pos]["filename"])
    result = OSDBServer().downloadByLink(subtitles_list[pos]["link"], destination)
    if not result:
        result = OSDBServer().download(subtitles_list[pos]["ID"], destination, session_id)
    language = subtitles_list[pos]["language_name"]
    return False, language, destination  # standard output
