#!/usr/bin/env python3
# coding: utf-8

# Copyright 2021 by BurnoutDV, <burnoutdv@gmail.com>
#
# This file is part of some open source application.
#
# Some open source application is free software: you can redistribute
# it and/or modify it under the terms of the GNU General Public
# License as published by the Free Software Foundation, either
# version 3 of the License, or (at your option) any later version.
#
# Some open source application is distributed in the hope that it will
# be useful, but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Foobar.  If not, see <http://www.gnu.org/licenses/>.
#
# @license GPL-3.0-only <https://www.gnu.org/licenses/gpl-3.0.en.html>

import json, logging
import sys

import googleapiclient

from playlistupdate import playlistUpdater

channel = "UCU3N3MrZThrI9OMBarMPu3A"
# Default Settings for logging, might be overwritten by config file
log_file = "ytupdater.log"
log_level = logging.INFO
log_format = '%(asctime)s \t %(levelname)s:%(message)s'


def check_for_updates(yt_config_file, playlist_config_file):
    """
    Checks the given youtube Channel for New Videos, look ups their tags and then checks if any tags are in a
    list of playlists that need autoadd, if yes, check if the video is already present, if yes, add them to the playlist
    :return: true if everything went fine
    """
    playlist_dict = playlistUpdater.load_generic_json(playlist_config_file)
    # playlist dict is a dictionary of Tags and Playlist ID -- { 'SORT_TAG': "PLAxxxxxxxxxxxxxxxxxxxx"}
    if playlist_dict is None:
        return False
    if not isinstance(playlist_dict, dict):
        print("Playlist dict has the wrong structure")
        return False
    for key, value in playlist_dict.items():
        if not isinstance(key, str) or not isinstance(value, str):
            print("Playlist dict content is not all strings")
            return False
    polaris = playlistUpdater(api_key_file=yt_config_file, log_level=4)
    if polaris is None:
        return False
    new_videos = polaris.fetch_most_recent_videos(channel, max_results=5)
    if new_videos is None:
        return False
    list_of_tags = {}  # instead of saving the tags i could do all my things directly here
    for each in new_videos:
        tags = polaris.fetch_video_tags(each['id']['videoId'])
        if tags is not None:
            list_of_tags[each['id']['videoId']] = tags
    for video, tags in list_of_tags.items():
        for tag in tags:
            if tag in playlist_dict:
                if polaris.check_existence_in_playlist(playlist_dict[tag], video) is False:
                    polaris.add_video_to_playlist(playlist_dict[tag], video)
                break  # for efficiency it would be wise if the sort tag is the first on youtube


if __name__ == "__main__":
    try:
        config = playlistUpdater.load_generic_json("config.json")
        if config:
            log_file = config.get('log_file', log_file)
            log_format = config.get('log_format', log_format)
            log_level = config.get('log_level', log_level)
            channel = config.get('channel_id', None)
    except IOError:
        print("Couldn't open config file, falling back to default", file=sys.stderr)
    finally:
        logging.basicConfig(filename=log_file, format=log_format, level=log_level)

        # polaris = playlistUpdater(oauth_file="client_secrets.json")
    polaris = playlistUpdater(api_key_file="yt-data.json")
    # print(polaris.fetch_all_playlist_videos("UCU3N3MrZThrI9OMBarMPu3A"))
    # check_for_updates("yt-data.json", "sorting_playlists.json")

    if channel is None:
        logging.info("No Channel ID set, trying to pry from user input")
        print("No channel id set in config file / no config file at all, channel id needed to proceed")
        channel = input()

    try:
        with open("testfile.json", "w") as test_file:
            json.dump(polaris.fetch_all_playlist_videos("PLAFz5ZZJ21wPLXztTV3rwsOdXHCFoI9O3", "snippet, contentDetails"), test_file, indent=2)
            # json.dump(polaris.fetch_all_channel_playlists(channel), test_file, indent=2)
            # print(f"Status of Video in Playlist", polaris.check_existence_in_playlist("PLAFz5ZZJ21wNyeB0GVnG1IQokpa-HBGRA","M2ooDDajhaohz"))
            #json.dump(polaris.insert_video_into_playlist("PLAFz5ZZJ21wNyeB0GVnG1IQokpa-HBGRA", "1rUWjfwaERc"), test_file, indent=2)
    except googleapiclient.errors.HttpError as e:
        logging.error(f"Problem with the request: {e}")


