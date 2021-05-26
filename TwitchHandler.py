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

import requests
import json
from datetime import datetime, timedelta

import logging
logger = logging.getLogger(__name__)


twitch_endpoint_v5 = "https://api.twitch.tv/kraken/"
twitch_video_upload = "https://uploads.twitch.tv/upload/"
twitch_endpoint_api = "https://api.twitch.tv/helix/"


class TwitchHandler:
    """
    Twitch (v6) Rate Limit: 800 Points per Minute
    """

    def __init__(self, client_id, token):
        self.client_id = client_id
        self.token = token
        self.secret = None

    def api_check(self, channel):
        """
        Simply checks if some random user is only or not, which is not the point, i just want
        the api response and this is the simplest thing on the reference page
        :return:
        """
        url = f"{twitch_endpoint_api}search/channels"
        header = {"Client-Id": self.client_id,
                  "Authorization": f"Bearer {self.token}"}
        payload = {"query": channel,
                   "live_only": False}
        r = requests.get(url, headers=header, params=payload)
        with open("request_input.json", "w") as requester:
            here = json.loads(r.text)
            json.dump(here, requester, indent=4)

    def upload_video(self, file, title):
        """
        Uploads a specified file to Twitch. As their own (v5) API Documentation this has to be max 1080P@60fps
        must use h264, aac and be in a MP4, MOV, AVI or FLV Container. The maximum of 10 Mbps Bitrate seems
        to not be very well enforced, at least my test did not ran into that. As i write this the v5 API is
        already deprecated BUT there is no equivalent in the new one also it uses another endpoint anyway.
        _https://uploads.twitch.tv/upload/<video ID>/
        Requires Channel Editor Scope //  channel_editor|channel:manage:videos
        :param file:
        :param title:
        :return:
        """

    @property
    def secret(self):
        return self._secret

    @secret.setter
    def secret(self, secret: str):
        self._secret = secret

    def obtain_token(self, scope) -> (str, datetime):
        """
        Small routine to obtain an access token for the given scope.
        """
        if self.secret is not None:
            auth_endpoint = "https://id.twitch.tv/oauth2/token"
            print(f"Requesting token for client_id: {self.client_id}")
            payload = {
                "client_id": self.client_id,
                "client_secret": self.secret,
                "grant_type": "client_credentials",
                "scope": scope,
            }
            r = requests.post(auth_endpoint, data=payload)
            quick_dict = json.loads(r.text)
            die_time = datetime.now() + timedelta(seconds=quick_dict['expires_in'])
            return quick_dict['access_token'], die_time
        else:
            raise Exception("No client secret, cannot fulfill request")
