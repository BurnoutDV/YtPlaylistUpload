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
import datetime

import pytz

from a_video import OneVideo


class OneVideoTest(unittest.TestCase):
    def test_generate_from_dict(self):
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
        some_dict = json.loads(json_string)
        herbert = OneVideo()
        herbert.generate_from_dict(some_dict)
        heinz = OneVideo(title="this is the title", description="test description", tags=["lets_play", "ingame", "klettern"])
        heinz.etag = "J3TC3IeuRR-HR_69iMs1wid7hrU"
        heinz.yt_id = "gfxrandomIDxfg"
        heinz.published = datetime.datetime(2021, 10, 5, 16, 3, 29, 0, pytz.UTC)
        heinz.channel_id = "UCU3N3MrZThrI9OMBarMPu3A"
        heinz.category = 20
        heinz.carbon_copy = True
        self.assertEqual(herbert.export("dict"), heinz.export("dict"))

    def test_export_to_flat(self):
        pass

    def test_export_to_tuple(self):
        testVideo = OneVideo()
        big_tuple = ("yt_id", "this is the title", "this is the description", "these,are,the,tags", 43, "thisisetag",
                     "xychannel_idsds", "2021-10-05T16:47:22", "twitch.tv/dsfsdf", "i.ytimg.com")
        testVideo.yt_id = big_tuple[0]
        testVideo.title = big_tuple[1]
        testVideo.description = big_tuple[2]
        testVideo.tags = big_tuple[3].split(',')
        testVideo.category = big_tuple[4]
        testVideo.etag = big_tuple[5]
        testVideo.channel_id = big_tuple[6]
        testVideo.published = big_tuple[7]
        testVideo.twitch_link = big_tuple[8]
        testVideo.yt_thumbnail_url = big_tuple[9]
        self.assertEqual(big_tuple, testVideo.export("tuple"))


if __name__ == '__main__':
    unittest.main()
