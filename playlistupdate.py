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

import errno

import googleapiclient
import httplib2
import json
from json.decoder import JSONDecodeError
import logging
from apiclient.discovery import build
import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors


class playlistUpdater:
    dev_key = None
    yt_service = None  # its a bit weird that i already call it yt service when i even leave it so there is an option for non yt-services
    yt_app_ver = None
    status = False
    youtube = None
    oauth_scopes = ["https://www.googleapis.com/auth/youtube.readonly", "https://www.googleapis.com/auth/youtube.force-ssl"]

    def __init__(self, api_key_file=None, dev_key=None, oauth_file=None,yt_api_service_name="youtube", yt_api_ver="v3"):
        if api_key_file is not None:
            if self.load_yt_conf(api_key_file):
                self.status = True
                self._connectAPI()
        elif oauth_file is not None:
            self._connectOAUTH2(oauth_file)
        elif dev_key is not None:
            self.dev_key = dev_key
            self.yt_service = yt_api_service_name
            self.yt_app_ver = yt_api_ver
            self.status = True
            self._connectAPI()


    @staticmethod
    def load_generic_json(filename):
        """
        Just loads a generic file, tries to json interpret it and gives back the content if everything succeeds.
        There is probably some boilerplate for that exact purpose
        :param filename:
        :return:
        """
        try:
            with open(filename, "r") as json_file:
                return json.load(json_file)
        except IOError as e:
            if e.errno == errno.ENOENT:
                logging.error(f"While loading json file {filename} no file could be found")
            elif e.errno == errno.EACCES:
                logging.error(f"While loading json file {filename} there was a lack of permission")
            else:
                logging.error(f"While loading json file {filename} some unknown error '{e}' turned up")
            return None
        except JSONDecodeError as e:
            logging.error(f"Json Decode Error {e}")
            return None

    def load_yt_conf(self, config_file_path) -> bool:
        try:
            with open(config_file_path, "r") as conf_file:
                data = json.load(conf_file)
                self.dev_key = data['API_KEY']
                self.yt_service = data['YOUTUBE_API_SERVICE_NAME']
                self.yt_app_ver = data['YOUTUBE_API_VERSION']
        except FileNotFoundError:
            logging.error("Config file not found")
            return False
        except ValueError as e:  # json
            logging.error("Config file could not be interpreted as json", e)
            return False
        except KeyError as e:
            logging.error(f"The Key {e} could not be found in the config file.")
            return False
        return True

    def _connectAPI(self):
        if self.status != True:
            return False
        try:
            self.youtube = build(self.yt_service, self.yt_app_ver, developerKey=self.dev_key)

        except httplib2.ServerNotFoundError:
            logging.error("Server connection could not be opened")
            return False
        logging.info("successfully connected to youtube with API Key")
        return True

    def _connectOAUTH2(self, secret_file):
        api_service_name = "youtube"
        api_version = "v3"

        # Get credentials and create an API client
        flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
            secret_file, self.oauth_scopes)
        credentials = flow.run_console()
        self.youtube = googleapiclient.discovery.build(api_service_name, api_version, credentials=credentials)

    def fetch_most_recent_videos(self, channel_id, max_results=10):
        # ! each call costs whopping 100 points, so max_results > 50 are expensive
        #  GET https://www.googleapis.com/youtube/v3/search?part=snippet&channelId={CHANNEL_ID}&maxResults=10&order=date&type=video&key={YOUR_API_KEY}
        if self.youtube is None:
            return False

        if max_results > 50:
            rounds = round((max_results/50)+0.5)
            logging.info(f"More than 50 results, {rounds} rounds", logel=3)
            requests = 50
        else:
            requests = max_results

        res = self.youtube.search().list(
            part='id',
            channelId=channel_id,
            maxResults=requests,
            order='date',
            type='video'
        ).execute()

        full_list = res.get('items')

        if max_results > 50:
            next_page_token = res.get('nextPageToken')
            for i in range(1, rounds):
                if i == rounds:
                    requests = max_results % 50
                res = self.youtube.search().list(
                    part='snippet',
                    channelId=channel_id,
                    maxResults=requests,
                    order='date',
                    type='video',
                    pageToken=next_page_token
                ).execute()
                next_page_token = res.get('nextPageToken')
                full_list += res.get('items', [])  # in case something goes wrong an empty list should be save, right?
        return full_list

    def fetch_video_tags(self, video_id):
        if self.youtube is None:
            return False
        res = self.youtube.videos().list(
            part='snippet',  # i would really like to request less but thats apparently not an option
            id=video_id
        ).execute()
        if res.get('items', None) is None and len(res['items']) >= 1:  # if we get more than 1 i am a bit puzzled why
            return None
        try:
            return res['items'][0]['snippet']['tags']  #quite the glass tower
        except KeyError:
            return False

    def fetch_all_playlist_videos(self, playlist_id, part="snippet"):
        res = self.youtube.playlistItems().list(
            part=part,
            playlistId=playlist_id,
            maxResults="50"
        ).execute()

        next_page_token = res.get('nextPageToken')
        while ('nextPageToken' in res):
            next_page = self.youtube.playlistItems().list(
                part=part,
                playlistId=playlist_id,
                maxResults="50",
                pageToken=next_page_token
            ).execute()
            res['items'] += next_page['items']

            if 'nextPageToken' not in next_page:
                res.pop('nextPageToken', None)
            else:
                next_page_token = next_page['nextPageToken']
        return res

    def fetch_all_channel_playlists(self, channel_id):
        if self.youtube is None:
            return False
        res = self.youtube.playlists().list(channelId=channel_id, part='contentDetails, snippet', maxResults='50').execute()
        next_page_token = res.get('nextPageToken')
        while 'nextPageToken' in res:
            next_page = self.youtube.playlists().list(
                channelId=channel_id,
                part='snippet',
                maxResults='50',
                pageToken=next_page_token).execute()
            res['items'] += next_page['items']

            if 'nextPageToken' not in next_page:
                res.pop('nextPageToken', None)
            else:
                next_page_token = next_page['nextPageToken']

        return res

    def check_existence_in_playlist(self, playlist_id, video_id):
        if self.youtube is None:
            return None
        try:
            videos = self.fetch_all_playlist_videos(playlist_id)
            for each in videos['items']:
                one_video_id = each['snippet']['resourceId']['videoId']
                if one_video_id == video_id:
                    return True
            return False
        except KeyError as e:
            logging.error(f"Surprising KeyError with key {e}")
        except googleapiclient.errors.HttpError as e:
            logging.error(f"Error with the google API: {e}")

    def insert_video_into_playlist(self, playlist_id, video_id):
        if self.youtube is None:
            return None
        try:
            playlistItem = self.youtube.playlistItems().insert(
                part="snippet",
                body={
                    'snippet': {
                    "playlistId": playlist_id,
                    "resourceId": {
                        'kind': "youtube#video",
                        'videoId': video_id
                        }
                    }
                }
            ).execute()
            return playlistItem
        except googleapiclient.errors.HttpError as e:
            logging.error(f"Error with the google API: {e}")
