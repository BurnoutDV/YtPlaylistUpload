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

from datetime import datetime
import dateutil.parser
import json

import logging
logger = logging.getLogger(__name__)


class OneVideo:
    """
    Part of my tries to abstract the structure of youtube videos / playlists as separate python objects, i am not
    quite sure if this is the way but i have things in mind which might make this appealing. For whatever reason
    """

    def __init__(self, title="", description="", tags=[], category=0):
        self.title = title  # title of this video
        self.description = description  # desription of this video
        self.tags = tags  # tags of the video
        self._generate_tag_hash()
        self.yt_id = ""  # id of the youtube video, the part behind youtube.com/watch?v=
        self.category = ""  # youtube categories, 20 is gaming
        # bla
        self.tag_hash = ""  # hash of all tags combined as string "tag1, tag2, tag3"
        self.etag = ""  # i have no clue for what this is good for but it exists in the files
        self.channel_id = ""  # the idea of the channel this video is belonging to
        self.carbon_copy = False # if its loaded from a json/api call its considered genuine till something happens
        self.published = datetime.today()  # date of publishment

    def generate_from_dict(self, json_dict: dict):
        kind = json_dict.get("kind", None)
        if kind is None:
            logger.warning("couldnt generate video from json due bad data")
            return False
        # from playlistItem && #videoItem
        if json_dict.get("snippet") is None:
            return False
        snippet = json_dict['snippet']
        if kind == "youtube#playlistItem" or kind == "youtube#video":
            # ? .get defaults to None, this is on purpose
            self._description = snippet.get("description", None)
            self._title = snippet.get("title", None)
            # * Dates are special, the python 3.7 function only works for one kind of iso format without trailing Z
            # self.published = datetime.fromisoformat(snippet.get("publishedAt", None).replace("Z", "+00:00"))
            self.published = dateutil.parser.isoparse(snippet.get("publishedAt", None))
        if kind == "youtube#playlistItem":
            self.yt_id = json_dict.get("resourceID").get("videoId", None)
            self.channel_id = snippet.get("videoOwnerChannelId", None)
            self._category = -1
            self._tags = []
            self.tag_hash = None
        elif kind == "youtube#video":
            self._tags = snippet.get("tags", [])
            self._generate_tag_hash()
            self.yt_id = json_dict.get("id", None)
            self.channel_id = snippet.get("channelId", None)
            self._category = int(snippet.get("categoryId", 0))
        # ! well, this is awkward. Etags are for saving on resources, basically a hash, but if we create a video from
        # ! a playlist or a search there is a difference in etag cause those are different things naturally
        self.etag = json_dict.get("etag", "")
        self.carbon_copy = True
            return True

    def _generate_tag_hash(self):
        """
        Just generates a hash for the list of tags as you cannot simply call hash() on a list
        """
        tag_string = ""
        for tag in self._tags:
            tag_string = f"{tag}, "
        tag_string = tag_string[:-2]
        self.tag_hash = hash(tag_string)

    def to_yt_json(self, structure="json"):
        """
        Returns the same kind of json structure that you get from youtube (minus the data i just not have)
        :return:
        """
        my_dict = {
                   'kind': "youtube#video",
                   'etag': self.etag,
                   'id': self.yt_id,
                   'snippet': {
                       'publishedAt': self.published.isoformat(),
                       'channelId': self.channel_id,
                       'title': self._title,
                       'description': self._description,
                       'tags': self._tags,
                       'categoryId': self._category
                    }
                   }
        if structure == "json":
            return json.dumps(my_dict, indent=3)
        else:
            return my_dict

    # ! boring getter & setter, modify carbon status
    @property
    def tags(self):
        return self._tags

    @tags.setter
    def tags(self, tags: list):
        self.carbon_copy = False
        self._tags = tags
        self._generate_tag_hash()

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

    @property
    def category(self):
        return self._category

    @category.setter
    def category(self, category: int):
        self.carbon_copy = False
        self._category = category

    """
    technically i should add more getter/setters here, but on the other hand..those other attributes cannot be changed
    anyway, sure, you can set your own custom publishDate but it wont change anything
    """