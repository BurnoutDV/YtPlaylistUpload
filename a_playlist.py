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

from a_video import OneVideo
from datetime import datetime
import dateutil.parser

import logging
logger = logging.getLogger(__name__)


class OnePlaylist:
    """
    For some reasons i want an object that represents a single playlist, the problem is that i am quite sure someone
    else already build a wrapper for this and everything i do is redundant but what do i know in the first place right?
    """
    def __init__(self, title="", description=""):
        self.id = None
        self.published = datetime.now().isoformat()
        self.channel_id = None
        self.title = title
        self.description = description
        self.items = {}  # this should actually be a list but the position is important..so its a sorted list
        self.etag = "" # cashing function to save in api points
        self.entries = 0

    def add_video(self, video: OneVideo):
        if video.yt_id != "":  # you are actually not meant to set this to anything on new videos
        # restores order
            idx = 0
            new_sorted_list = {}
            for key in self.items:
                new_sorted_list[idx] = self.items[key]
                idx += 1
            new_sorted_list[idx] = video
            self.items = new_sorted_list
            self.entries = len(self.items)

    def remove_video(self, video: OneVideo):
        if video.yt_id != "":
            idx = 0
            new_sorted_list = {}
            for key in self.items:
                #  recreates the list without that one
                if self.items[key].yt_id != video.yt_id:
                    new_sorted_list[idx] = self.items[key]
                    idx += 1
            self.items = new_sorted_list
            self.entries = len(self.items)

    def remove_video_by_id(self, yt_id):
        idx = 0
        new_sorted_list = {}
        for key in self.items:
            #  recreates the list without that one
            if self.items[key].yt_id != yt_id:
                new_sorted_list[idx] = self.items[key]
                idx += 1
        self.items = new_sorted_list
        self.entries = len(self.items)

    def generate_from_json(self, youtube_response: dict):
        kind = youtube_response.get("kind")
        if not kind: # in case some stuff that cannot be interpreted got returned
            return False
        if youtube_response.get("snippet") is None:
            return False
        snippet = youtube_response['snippet']
        if kind == "youtube#playlist":
            self._description = snippet.get("description", None)
            self._title = snippet.get("title", None)
            self.published = dateutil.parser.isoparse(snippet.get("publishedAt", None))
            self.etag = youtube_response.get("etag", "")
            self.carbon_copy = True  # ? Technically i could just set etag to nothing if something is changed
            if snippet.get("contentDetails") is not None:
                self.entries = snippet.get("contentDetails").get("itemCount")
        elif kind == "youtube#playlistItemListResponse":
            for one_video in youtube_response['items']:
                temp_video = OneVideo()
                temp_video.generate_from_dict(one_video)
                self.add_video(temp_video)
        else:
            logger.warning("Could not interpret given dictionary into a playlist item")
            return False
        #  playlist item response

    @property
    def title(self):
        return self._title

    @title.setter
    def title(self, title):
        self.carbon_copy = False
        self._title = title

    @property
    def description(self):
        return self._description

    @description.setter
    def description(self, description: str):
        self.carbon_copy = False
        self._description = description
