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
    Twitch Helix Rate Limit: 800 Points per Minute
    """

    def __init__(self, client_id, token):
        self.client_id = client_id
        self.token = token
        self.secret = None
        self.default_channel = 0
        self.headerv5 = {
            "Accept": "application/vnd.twitchtv.v5+json",
            "Authorization": f"OAuth {self.token}",
            "Client-ID": self.client_id
            }
        self.header_helix = {
            "Authorization": f"Bearer {self.token}",
            "Client-ID": self.client_id
        }
        self.scopes = []

    def search_by_channelname(self, channel, live = False):
        """
        Simply checks if some random user is only or not, which is not the point, i just want
        the api response and this is the simplest thing on the reference page
        :return:
        """
        url = f"{twitch_endpoint_api}search/channels"
        payload = {"query": channel,
                   "live_only": live}
        r = requests.get(url, headers=self.header_helix, params=payload)
        TwitchHandler.write_request(r.text)

    def get_channel_id(self, name: str):
        """
        Retrieves the id of a channel by its (unique) name
        :param name:
        :return:
        """
        url = f"{twitch_endpoint_api}users"
        payload = {"login": name}
        logging.info(f"Requesting user info for '{name}' via {url}")
        r = requests.get(url, headers=self.header_helix, params=payload)
        if r.status_code != 200:
            TwitchHandler.handle_response_error(r.text)
        TwitchHandler.write_request(r.text)

    def api_status_v5(self, verbose = False):
        url = f"{twitch_endpoint_v5}"
        r = requests.get(url, headers=self.headerv5)
        if r.status_code != 200:
            self.handle_response_error(r.text)
            raise TypeError(f"Error - {r.status_code}")
        response = json.loads(r.text)
        self.scopes = response['token']['authorization']['scopes']
        if 'token' in response:
            if not verbose:
                if response['token']['valid']:
                    return response['token']['authorization']['scopes']
                else:
                    raise Exception("Status - token not valid")
            else:  # Verbose
                try:
                    die_time = datetime.now() + timedelta(seconds=response['token']['expires_in'])
                    report = {
                        "valid": response['token']['valid'],
                        "scopes": response['token']['authorization']['scopes'],
                        "created_at": response['token']['authorization']['created_at'],
                        "updatet_at": response['token']['authorization']['updated_at'],
                        "client_id": response['token']['client_id'],
                        "expires_in": die_time.isoformat()
                    }
                    return report
                except KeyError as e:
                    logging.warning(f"KeyError in Status: {e}")
                    raise TypeError("Status - return structure is missing keys")
        else:
            TwitchHandler.write_request(r.text)
            raise TypeError("Status - return structure unknown")

    def api_status_validate(self):
        url = f"https://id.twitch.tv/oauth2/validate"
        validate_header = {"Authorization": f"OAuth {self.token}"}
        r = requests.get(url, headers = validate_header)
        if r.status_code != 200:
            self.handle_response_error(r.text)
            raise TypeError(f"Error - {r.status_code}")
        response = json.loads(r.text)
        # logger.info(json.dumps(response))
        if response['expires_in'] < 60*60*24: # 1 day in seconds
            logger.warning(f"Token about to expire ({response['expires_in']} seconds left)")
        self.scopes = response['scopes']
        return response['scopes']

    def upload_video(self, file, title):
        """
        Uploads a specified file to Twitch. As their own (v5) API Documentation this has to be max 1080P@60fps
        must use h264, aac and be in a MP4, MOV, AVI or FLV Container. The maximum of 10 Mbps Bitrate seems
        to not be very well enforced, at least my test did not ran into that. As i write this the v5 API is
        already deprecated BUT there is no equivalent in the new one also it uses another endpoint anyway.
        _https://uploads.twitch.tv/upload/<video ID>/_
        Requires Channel Editor Scope //  channel_editor|channel:manage:videos
        :param file:
        :param title:
        :return:
        """
        if not self.check_scope("channel_editor"):
            return False
        url = f"{twitch_endpoint_v5}videos"
        payload = {
                   "channel_id": "27045770",
                   "title": title,
                   }
        logger.info(f"Creating new POST request to {url}")
        r = requests.post(url, payload, headers=self.headerv5)
        if r.status_code != 200:
            TwitchHandler.handle_response_error(r.text)
            return False
        TwitchHandler.write_request(r.text)

    def create_collection(self, title, channel_id=0):
        if not self.check_scope("collections_edit"):
            return False
        if channel_id == 0:  # * magic number, i hope no one ever has that id for any reason
            if self.default_channel != 0:
                channel_id = self.default_channel
            else:
                raise TypeError("Need some channel id (fitting to the token)")
        if not self.check_scope("collections_edit"):
            return False
        url = f"{twitch_endpoint_v5}channels/{channel_id}/collections"
        payload = {"title": title}
        r = requests.post(url, payload, headers=self.headerv5)
        if r.status_code != 200:
            TwitchHandler.handle_response_error(r.text)
            return False
        TwitchHandler.write_request(r.text)

    def check_scope(self, required_scope):
        """
        Checks if the given token is able to perform a request, if nothing was done that actually
        checks the current token we cannot know the scope and we just default to true. This is a
        safety net with questionable purpose i must say. But i created it, and now i feel a bit proud
        :param required_scope: scope in which the action is to be done
        :return: boolean value whether we are in scope or not. True if not scope given
        """
        if len(self.scopes) == 0:
            return True
        if required_scope in self.scopes:
            return True
        return False

    def obtain_server_token(self, scope) -> (str, datetime):
        """
        Small routine to obtain an access token for the given scope.
        """
        if self.secret is None:
            raise Exception("No client secret, cannot fulfill request")
        auth_endpoint = "https://id.twitch.tv/oauth2/token"
        print(f"Requesting token for client_id: {self.client_id}")
        payload = {
            "client_id": self.client_id,
            "client_secret": self.secret,
            "grant_type": "client_credentials",
            "scope": scope,
        }
        r = requests.post(auth_endpoint, data=payload)
        if r.status_code != 200:
            msg = TwitchHandler.handle_response_error(r.text)
            raise TypeError(f"Error - {r.status_code} - {msg}")
        quick_dict = json.loads(r.text)
        die_time = datetime.now() + timedelta(seconds=quick_dict['expires_in'])
        """{'access_token': '1la4be0yk6l4e33gft4stn9dto0u6s', 
            'expires_in': 5392455, 
            'scope': ['channel_editor'], 
            'token_type': 'bearer'}
        """
        return quick_dict['access_token'], die_time

    def obtain_client_token(self, scope, response_url):
        """"
        GET https://id.twitch.tv/oauth2/authorize
    ?client_id=<your client ID>
    &redirect_uri=<your registered redirect URI>
    &response_type=<type>
    &scope=<space-separated list of scopes>
    """
        auth_endpoint = "https://id.twitch.tv/oauth2/authorize"
        payload = {
            "client_id": self.client_id,
            "redirect_uri": response_url,
            "response_type": "token",
            "scope": scope,
        }
        r = requests.post(auth_endpoint, payload)

    def obtain_client_token2(self, code, response_url):
        """
        POST https://id.twitch.tv/oauth2/token
        ?client_id=uo6dggojyb8d6soh92zknwmi5ej1q2
        &client_secret=nyo51xcdrerl8z9m56w9w6wg
        &code=394a8bc98028f39660e53025de824134fb46313
        &grant_type=authorization_code
        &redirect_uri=http://localhost
        :param code:
        :param scope:
        :return:
        """
        if self.secret is None:
            raise Exception("No client secret, cannot fulfill request")
        url = "https://id.twitch.tv/oauth2/token"
        payload = {
            "client_id": self.client_id,
            "client_secret": self.secret,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": response_url
        }
        r = requests.post(url, payload)
        if r.status_code != 200:
            TwitchHandler.handle_response_error(r.text)
            return False
        TwitchHandler.write_request(r.text)

    def refresh_token(self):
        if self.secret is not None:
            raise NotImplementedError("i have not done this yet, sorry")
        else:
            raise Exception("No client secret, cannot fulfill request")

    @staticmethod
    def handle_response_error(response):
        if TwitchHandler.is_jsonable(response):
            e_m = json.loads(response)
            if 'status' in e_m and 'error' in e_m and 'message' in e_m:
                logger.error(f"[{e_m['status']}]{e_m['error']} - {e_m['message']}")
                return e_m['message']
            else:
                logger.error(json.dumps(e_m))
                return json.dumps(e_m)
        else:
            logger.error(f"No Json: {response[:128]}")
            return response[:128]

    @staticmethod
    def write_request(request_text: str, file_path="request_input.json"):
        with open(file_path, "w") as requester:
            here = json.loads(request_text)
            here['_time'] = datetime.now().isoformat()
            json.dump(here, requester, indent=4)

    @staticmethod
    def is_jsonable(x):
        """
        Checks if the thing can be json
        Copied & Stolen: https://stackoverflow.com/a/53112659
        :param x: an object
        :return: True/False if the thing can be json
        """
        try:
            json.dumps(x)
            return True
        except (TypeError, OverflowError):
            return False

    @property
    def secret(self):
        return self._secret

    @secret.setter
    def secret(self, secret: str):
        self._secret = secret