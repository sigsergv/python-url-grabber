"""
"""

import os
import sys
import json
import socket
import urllib.request
import urllib.error
from tempfile import mkstemp

from .error import (HTTPNotFoundError, NotProcessedError, OtherError,
    HTTPForbiddenError)

class Fetcher:
    HTTP_ERROR = 1

    def __init__(self, cache_path=False, cache_dir_name='.cache',
        user_agent=False):

        if not isinstance(cache_dir_name, str):
            raise TypeError('Invalid cache dir name type, must be a string')

        if user_agent is False:
            user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_1) AppleWebKit/537.73.11 (KHTML, like Gecko) Version/7.0.1 Safari/537.73.11'

        if cache_path == False:
            # use cwd as cache root along with cache_dir_name if specified
            cache_path = os.path.join(os.path.abspath('.'), cache_dir_name)

        # try to create cache dir
        if not os.path.exists(cache_path):
            os.makedirs(cache_path)
        self.cache_path = cache_path
        self.cache_index_file = os.path.join(self.cache_path, 'index.json')
    
        self.init_cache()

        self.request_headers = {
            'User-Agent': user_agent
        }


    def fetch_url(self, url):
        """Download URL or fetch it from cache if available
        """
        if url not in self.cache:
            # file not in cache, so download it
            headers = self.request_headers.copy()
            opener = urllib.request.build_opener()
            opener.addheaders = [(k,v) for (k,v) in headers.items()]

            try:
                f = opener.open(url)
                # TODO: add encoding detection from the response headers
                data = f.read().decode('utf-8')
                cfd, cache_data_filename = mkstemp(dir=self.cache_path, prefix='cache-')
                cache_data_filename = os.path.basename(cache_data_filename)
                cfp = os.fdopen(cfd, 'w')
                cfp.write(data)
                self.cache[url] = {
                    'cacheName': cache_data_filename 
                }
            except urllib.error.HTTPError as e:
                # remember, this URL could not be retrieved
                self.cache[url] = {
                    'error': self.HTTP_ERROR,
                    'errorCode': e.code
                }

        self.save_cache()

        if url in self.cache:
            cr = self.cache[url]

            if 'error' in cr:
                if cr['error'] == self.HTTP_ERROR:
                    if cr['errorCode'] == 404:
                        raise HTTPNotFoundError()
                    elif cr['errorCode'] == 403:
                        raise HTTPForbiddenError()
                    else:
                        raise OtherError('HTTP Error: {0}'.format(cr['errorCode']))
                raise OtherError()

            elif 'cacheName' in cr:
                cache_name = cr['cacheName']
                cache_name = os.path.join(self.cache_path, cache_name)
                with open(cache_name) as fp:
                    return fp.read()

        raise NotProcessedError()


    def save_cache(self):
        """Save cache data to the index file
        """
        # we need to sync data: open file, read, merge, write
        try:
            with open(self.cache_index_file, 'r') as fp:
                cache = json.load(fp)
        except FileNotFoundError:
            cache = {}
            pass

        # merge
        for (k,v) in self.cache.items():
            cache[k] = v

        with open(self.cache_index_file, 'w') as fp:
            json.dump(cache, fp)


    def init_cache(self):
        """Init cache index for first time
        """
        try:
            with open(self.cache_index_file, 'r') as fp:
                try:
                    self.cache = json.load(fp)
                except ValueError:
                    self.cache = {}
        except FileNotFoundError:
            self.cache = {}
