#!/usr/bin/env python
#
#  This code was original copied from:  https://github.com/runapp/flexproxy
#  It was modified as follows:
#
#     - remove the concept of an addition upstream proxy (up_host, up_port);  We arent upstreaming
#
#
import logging
import os
import sys
import socket
import asyncio

from WAFLogic import WAFLogic

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import tornado.httpserver
import tornado.ioloop
import tornado.iostream
import tornado.web
import tornado.httpclient
import tornado.httputil
from tornado.options import define, options

define('port', default=8875, help='Port the proxy server runs on')
define('bind', default='127.0.0.1', help='Address the proxy server binds to')
define('protected_uri', default=None, type=str, help='Protected application uri')


logger = logging.getLogger('tornado_proxy')

__all__ = ['ProxyHandler', 'run_proxy']

def fetch_request(request_url, **kwargs):        
    full_url = "{}{}".format(options.protected_uri, request_url)
    logger.info("full_url: {}".format(full_url))
    req = tornado.httpclient.HTTPRequest(full_url, **kwargs)
    client = tornado.httpclient.AsyncHTTPClient(defaults=dict(request_timeout=180))
    return client.fetch(req, raise_error=False)

async def pipe(f: tornado.iostream.IOStream, t: tornado.iostream.IOStream):
    try:
        while True:
            logger.info("aaa")
            a = await f.read_bytes(16384, partial=True)
            await t.write(a)
    except tornado.iostream.StreamClosedError as e:
        pass

class ProxyHandler(tornado.web.RequestHandler):
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.waf = WAFLogic()
        
    def compute_etag(self):
        return None  # disable tornado Etag

    async def get(self):
        logger.info("GOT A GET REQUEST!")
        logger.info('Handle %s request to %s', self.request.method, self.request.uri)        
        logger.info('headers {}'.format(self.request.headers))
        logger.info('Sending it to the WAF')

        if self.waf.check_request(self.request):
            #Passed WAF check
            body = self.request.body
            if not body:
                body = None
            try:
                if 'Proxy-Connection' in self.request.headers:
                    del self.request.headers['Proxy-Connection']
                response = await fetch_request(
                    self.request.uri,                
                    method="GET", body=body,
                    headers=self.request.headers, follow_redirects=False,
                    allow_nonstandard_methods=True)
            except tornado.httpclient.HTTPError as e:
                logger.error("Ooof we hit an error: {}".format(e))
                if hasattr(e, 'response') and e.response:
                    pass
                else:                
                    self.set_status(500)
                    self.write('Internal server error:\n' + str(e))
                    return
            except ConnectionRefusedError as e:
                self.set_status(502)
                self.write('Remote connection refused.')
                return

            if (response.error and not
                    isinstance(response.error, tornado.httpclient.HTTPError)):
                self.set_status(500)
                self.write('Internal server error:\n' + str(response.error))
            else:
                self.set_status(response.code, response.reason)
                self._headers = tornado.httputil.HTTPHeaders()  # clear tornado default header

                for header, v in response.headers.get_all():
                    if header not in ('Content-Length', 'Transfer-Encoding', 'Content-Encoding', 'Connection'):
                        self.add_header(header, v)  # some header appear multiple times, eg 'Set-Cookie'

                if response.body:
                    self.set_header('Content-Length', len(response.body))
                    self.write(response.body)
        else:
            #Failed WAF check -- this is returned to the attack, so choose wisely!
            self.set_status(403)
            self.write('Forbidden!')

    async def post(self):
        logger.info("GOT A POST REQUEST!")
        logger.info('Handle %s request to %s', self.request.method, self.request.uri)        
        logger.info('headers {}'.format(self.request.headers))
        body = self.request.body
        if not body:
            body = None
        if self.waf.check_request(self.request):
            #Passed WAF check
            try:
                if 'Proxy-Connection' in self.request.headers:
                    del self.request.headers['Proxy-Connection']
                response = await fetch_request(
                    self.request.uri,                
                    method="POST", body=body,
                    headers=self.request.headers, follow_redirects=False,
                    allow_nonstandard_methods=True)
            except tornado.httpclient.HTTPError as e:
                logger.error("Ooof we hit an error: {}".format(e))
                if hasattr(e, 'response') and e.response:
                    pass
                else:                
                    self.set_status(500)
                    self.write('Internal server error:\n' + str(e))
                    return
            except ConnectionRefusedError as e:
                self.set_status(502)
                self.write('Remote connection refused.')
                return

            if (response.error and not
                    isinstance(response.error, tornado.httpclient.HTTPError)):
                self.set_status(500)
                self.write('Internal server error:\n' + str(response.error))
            else:
                self.set_status(response.code, response.reason)
                self._headers = tornado.httputil.HTTPHeaders()  # clear tornado default header

                for header, v in response.headers.get_all():
                    if header not in ('Content-Length', 'Transfer-Encoding', 'Content-Encoding', 'Connection'):
                        self.add_header(header, v)  # some header appear multiple times, eg 'Set-Cookie'

                if response.body:
                    self.set_header('Content-Length', len(response.body))
                    self.write(response.body)
        else:
            #Failed WAF check -- this is returned to the attack, so choose wisely!
            self.set_status(403)
            self.write('Forbidden!')

def run_proxy(port, address, start_ioloop=True):
    """
    Run proxy on the specified port. If start_ioloop is True (default),
    the tornado IOLoop will be started immediately.
    """
    app = tornado.web.Application([
        (r'.*', ProxyHandler),
    ])
    app.listen(port, address)
    ioloop = tornado.ioloop.IOLoop.instance()
    if start_ioloop:
        ioloop.start()


if __name__ == '__main__':
    options.parse_command_line()
    if options.protected_uri is None:
        logger.error("You did not pass in a --protected_uri argument; e.g. --protected_uri=http://10.0.0.1:3000")
        exit()

    run_proxy(options.port, options.bind)