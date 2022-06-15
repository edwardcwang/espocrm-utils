#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  ingest_email.py
#  Ingest e-mail metadata from
#  https://github.com/edwardcwang/gmail-button-addon/

from espocrm_utils import *
from typing import *
from http.server import BaseHTTPRequestHandler, HTTPServer
import logging

REGISTER_EMAIL = int(os.environ.get("ESPOCRM_REGISTER_EMAIL", "1")) > 0

def handle_data(data: str) -> bool:
    try:
        e = IngestedEmail.from_str(data)
        logging.info("handle_data: logging " + str(e))
        if REGISTER_EMAIL:
            reg_result = register_email(e)
            if not reg_result:
                logging.info("handle_data: failed to register")
            return reg_result
        else:
            return True
    except Exception as e:
        logging.info("handle_data: got exception " + str(e))
        return False

class S(BaseHTTPRequestHandler):
    def _set_response(self, code=200):
        self.send_response(code)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
    def do_GET(self):
        logging.info("GET request,\nPath: %s\nHeaders:\n%s\n", str(self.path), str(self.headers))
        self._set_response()
        self.wfile.write("".encode('utf-8'))
    def do_POST(self):
        content_length = int(self.headers['Content-Length']) # <--- Gets the size of data

        # The data itself
        post_data = self.rfile.read(content_length).decode('utf-8')

        logging.info("POST request,\nPath: %s\nHeaders:\n%s\n\nBody:\n%s\n",str(self.path), str(self.headers), post_data)

        successful = handle_data(post_data)
        resp = "Success" if successful else ""

        logging.info("Handled request")

        self._set_response(200 if successful else 400)
        self.wfile.write(resp.encode('utf-8'))

def run(server_class=HTTPServer, handler_class=S, port=8080) -> None:
    logging.basicConfig(level=logging.INFO)
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    logging.info('Starting httpd...\n')
    print(httpd)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()
    logging.info('Stopping httpd...\n')

def main(args: List[str]) -> int:

    port = 25000

    if len(args) > 1:
        port = int(args[1])

    run(port=port)

    return 0

if __name__ == '__main__':
    sys.exit(main(sys.argv))
