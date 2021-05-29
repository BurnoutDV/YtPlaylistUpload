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
import ssl
from urllib.parse import urlparse, parse_qs
from http.server import BaseHTTPRequestHandler, HTTPServer

import logging
from io import BytesIO

logger = logging.getLogger(__name__)


class BasicRequester(BaseHTTPRequestHandler):
    """
    This is a small python based webserver that is meant to be run in a thread
    or threading. It runs as long till it gets the right parameters for an OAuth
    authentication token process, does the necessary steps and then reports back
    with the received tokens. Usually the process goes as follows:
    1. USER clicks the link with a response address
    2. USER accepts the terms for the scope and gets forwarded to this server with a token
    3. that token gets reported back, the server terminated itself and you can proceed with
       the token
    """
    def do_GET(self):
        if '?code=' in self.path:
            params = parse_qs(urlparse(self.path).query)
            code = params.get('code', 'unknown')
            message = f"Code is {code}"
        else: # default message
            message = self.path
        self.protocol_version = "HTTP/1.1"
        self.send_response(200)
        self.send_header("Content-Length", len(message))
        self.send_header("Content-Type", "text/html")
        self.end_headers()

        self.wfile.write(bytes(message, "utf8"))

    def do_POST(self):
        self.send_response(200)
        self.end_headers()
        response = BytesIO()
        response.write(b'This should not answer to POST requests')
        self.wfile.write(response.getvalue())


class PocketWebserver:
    # ? openssl req -x509 -newkey rsa:4096 -sha256 -days 3650 -nodes -keyout private.key -out full_chain.pem -subj "/CN=localhost" -addext "subjectAltName=DNS:localhost,DNS:localhost,IP:127.0.0.1"
    def __init__(self, port=8080, ssl=False, keyfile="./private.key", certfile="./full_chain.pem"):
        self.port = port
        self.ssl = ssl
        self.keyfile = keyfile
        self.certfile = certfile

    def run(self):
        httpd = HTTPServer(('', self.port), BasicRequester)
        if ssl:
            httpd.socket = ssl.wrap_socket(httpd.socket,
                                           keyfile=self.keyfile,
                                           certfile=self.certfile,
                                           server_side=True)
        httpd.serve_forever()


michael = PocketWebserver(8443, False)
michael.run()
