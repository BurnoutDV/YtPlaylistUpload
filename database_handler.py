import sqlite3
from datetime import datetime

from a_video import OneVideo
from a_playlist import OnePlaylist


import logging
logger = logging.getLogger(__name__)

current_ytmate_schema_version = "0.1"

yt_twitch_stuff_schema = {}
yt_twitch_stuff_schema['OneVideo'] = """
CREATE TABLE IF NOT EXISTS OneVideo (
uid INTEGER PRIMARY KEY AUTOINCREMENT,
yid TEXT UNIQUE,
title TEXT,
description TEXT,
tags TEXT,
category INTEGER,
etag TEXT,
channel_id TEXT,
published TIMESTAMP,
twitch_link TEXT DEFAULT '',
yt_thumbnail_url TEXT 
);"""

yt_twitch_stuff_schema['OnePlaylist'] = """
CREATE TABLE IF NOT EXISTS OnePlaylist (
uid INTEGER PRIMARY KEY AUTOINCREMENT,
yid TEXT UNIQUE,
title TEXT,
description TEXT,
item_list TEXT,
etag TEXT,
entries INTEGER DEFAULT 0,
channel_id TEXT,
published TIMESTAMP,
twitch_link TEXT DEFAULT ''
);"""

yt_twitch_stuff_schema['playlist_video_link'] = """
CREATE TABLE playlist_video_link (
video_id INTEGER REFERENCES OneVideo(uid),
playlist_id INTEGER REFERENCES OnePlaylist(uid)
);"""
yt_twitch_stuff_schema['metadata'] = """
CREATE TABLE metadata (
uid INTEGER PRIMARY KEY AUTOINCREMENT,
version TEXT,
first_run TIMESTAMP,
last_run TIMESTAMP,
runs INTEGER
);
"""


class YoutubeMateDBHandler:
    def __init__(self, filepath=""):
        self.db_path = filepath
        self.con = None

    def initiate(self, filepath=""):
        # check if file exists
        # check if file is actually an sqlite file
        # check if file got the tables necessary
        # check what the meta information is, table version
        # update database to current status

        # ! Connection stuff
        if self.db_path == "" and filepath == "":
            logger.info("No file path set")
            return False
        elif self.db_path == "":
            self.db_path = filepath
        if self.con is not None:
            logger.info("Tried to initiate already initiated database")
            return False
        try:
            self.con = sqlite3.connect(filepath, uri=True)
        except sqlite3.OperationalError as err:
            logger.error(f"Error while opening database file: {err}")
        # !table check on existence and populate if not
        for key in yt_twitch_stuff_schema:
            record = self.con.execute(f"SELECT count(name) FROM sqlite_master WHERE type='table' AND name='{key}';")
            if record.fetchone()[0] == 0:
                self.con.execute(yt_twitch_stuff_schema[key])
        self.con.commit()
        # checking for all rows to be there and adding the missing ones is actually quite hard i noticed
        # i can check for exactness with .schema <name> but the rest isn't so easy
        # ! check meta information
        record = self.con.execute("SELECT version, first_run, last_run, runs FROM metadata").fetchone() # shall only be one
        jetzt = datetime.now()
        if record is None: # no entries yet
            sql = f"""
                    INSERT INTO metadata (version, first_run, last_run, runs)
                     VALUES ('{current_ytmate_schema_version}', '{jetzt}', '{jetzt}', 1);
                    """
            self.con.execute(sql)
        else:
            sql = f"""
                    UPDATE metadata SET
                        last_run = '{jetzt}',
                        runs = '{record[3]+1}';
                  """  # there should only be ONE line, but in doubt, we update 'em all to the same
            self.con.execute(sql)
        self.con.commit()

    def close(self):
        if self.con is not None:
            self.con.commit()
            self.con.close()

    def create_schema(self):
        if self.con is None:
            return False
        for key in yt_twitch_stuff_schema:
            self.con.execute(yt_twitch_stuff_schema[key])
        self.con.commit()
        # write new table
        pass

    def fetch_video(self, yt_id: str) -> OneVideo or None:
        # fetches video based on youtube video id
        sql = f"""SELECT yid, title, description, tags, category, etag, channel_id, published, twitch_link, yt_thumbnail_url 
                  FROM OneVideo WHERE yid = '{yt_id}';"""

        response = self.con.execute(sql).fetchone()
        if response is not None:
            temp_video = OneVideo()
            temp_video.yt_id = response[0]
            temp_video.title = response[1]
            temp_video.description = response[2]
            temp_video.tags = response[3].split(',')
            temp_video.category = response[4]
            temp_video.etag = response[5]
            temp_video.channel_id = response[6]
            temp_video.published = response[7]
            temp_video.twitch_link = response[8]
            temp_video.yt_thumbnail_url = response[9]
            return temp_video
        else:
            return None

    def fetch_playlist(self, yt_id: str) -> OnePlaylist:
        # fetch playlist based on youtube id with all videos
        pass

    def insert_video(self, a_video: OneVideo):
        # * TODO: Check if youtube_id is already there cause its an unique key
        sql = f"""INSERT INTO OneVideo
                (yid, title, description, tags, category, etag, channel_id, published, twitch_link, yt_thumbnail_url)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);"""
        try:
            self.con.executemany(sql, [a_video.export("tuple")])
            self.con.commit()
        except sqlite3.IntegrityError as e:
            logger.error(f"SQLite Integrity Exception: {e}")

    def insert_playlist(self, a_playlist: OnePlaylist):
        pass

    @property
    def db_path(self):
        return self._db_path

    @db_path.setter
    def db_path(self, file_path: str):
        self._db_path = file_path
