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

import json
import unittest
from a_video import OneVideo
from database_handler import YoutubeMateDBHandler


class DbHandlerTest(unittest.TestCase):

    def test_insert(self):
        json_string = """{
                    "kind": "youtube#video",
                    "etag": "J3TC3IeuRR-HR_69iMs1wid7hrU",
                    "id": "gfxrandomIDxfg",
                    "snippet": {
                      "publishedAt": "2021-10-05T16:03:29Z",
                      "channelId": "UCU3N3MrZThrI9OMBarMPu3A",
                      "title": "this is the title",
                      "description": "test description",
                      "channelTitle": "BurnoutDV",
                      "tags": [
                        "lets_play",
                        "ingame",
                        "klettern"
                      ],
                      "categoryId": "20"
                    }
                  }"""
        test_video = OneVideo()
        some_dict = json.loads(json_string)
        test_video.generate_from_dict(some_dict)
        test_video.twitch_link = "twitch.tv"
        # i boldly assume that this is already tested and works accordingly
        test_db = YoutubeMateDBHandler(":memory:")
        test_db.initiate()
        test_db.insert_video(test_video)
        second_video = test_db.fetch_video(test_video.yt_id)
        self.assertEqual(test_video.export("tuple"), second_video.export("tuple"))
        test_db.close()


