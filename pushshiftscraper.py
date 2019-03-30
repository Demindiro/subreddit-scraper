#!venv/bin/python3

from config import *
from time import sleep
from os import symlink
from os.path import isfile, join as pathjoin
import requests
from mimetypes import guess_extension
import json



"""
Globals
"""

if isfile('id_cache.txt'):
    with open('id_cache.txt', 'r') as f:
        cache = set([s.rstrip() for s in f.readlines()])
    cache_file = open('id_cache.txt', 'a')
else:
    cache = set()
    cache_file = open('id_cache.txt', 'w')



"""
Classes
"""

class Submission:

    def __init__(self, id, title, url, selftext, created_utc):
        self.id          = id
        self.title       = title
        self.url         = url
        self.selftext    = selftext
        self.created_utc = created_utc

    def _parse(data):
        return Submission(data['id'], data['title'], data['url'], data['selftext'], data['created_utc'])


class SubmissionGenerator:

    def __init__(self):
        self.before = None
        self._next_batch()

    def __iter__(self):
        return self

    def __next__(self):
        if self._index >= len(self._batch):
            self._next_batch()
        submission = self._batch[self._index]
        self._index += 1
        return submission

    def _next_batch(self):
        url = f'https://api.pushshift.io/reddit/submission/search?subreddit={SUBREDDIT}&sort=new&size=1024'
        if self.before:
            url += '&before=' + str(self.before)
        req = requests.get(url)
        req.raise_for_status()
        self._batch = [Submission._parse(j) for j in json.loads(req.text)['data']]
        self._index = 0
        self.before = self._batch[-1].created_utc


"""
Main
"""

for submission in SubmissionGenerator():

    if submission.id in cache:
        print('Skipping', submission.id, '(cache)')
        continue

    if submission.selftext != '':
        ext = '.txt'
    else:
        req = requests.head(submission.url)
        ctype = req.headers.get('content-type', '')
        if ctype.startswith('image/'):
            ext = guess_extension(ctype.split(' ', 2)[0])
            # Really? `image/*`?
            if ext is None:
                print('Extension couldn\'t be guessed (' + ctype + ')')
                # I'm done, this will do
                # I mean, come on Reddit: https://i.reddituploads.com/9cf2711854b84c0cb5f143f5456ad031?fit=max&h=1536&w=1536&s=7aa0269674cdd9c1170a1320c1997a61
                # ^^^ You expect me to guess the extension from that?
                # And no, I'm not going to analyze the image itself damnit
                ext = submission.url[submission.url.rfind('.'):].replace('/', '_')
                print('Guessing ' + ext + ' from URL (' + submission.url + ')')
            # Goddamnit mimetypes
            # Yes, .jpe is valid but come on, nobody uses that anymore
            if ext == '.jpe':
                ext = '.jpg'
        else:
            print('Skipping ' + submission.id + ' (MIME type is ' + ctype + ')')
            sleep(SCRAPE_SKIP_DELAY)
            continue # TODO what to do with other types of pages (e.g. articles?)

    path = submission.id + ext

    if not isfile(pathjoin(DOWNLOADS_DIR, path)):
        print('Saving ' + submission.id)
        if submission.selftext != '':
            with open(pathjoin(DOWNLOADS_DIR, path), 'w') as f:
                f.write(submission.selftext)
        else:
            with open(pathjoin(DOWNLOADS_DIR, path), 'wb') as f:
                print('Downloading ' + submission.id + ' (' + submission.url + ')')
                with requests.get(submission.url, stream=True) as r:
                    try:
                        r.raise_for_status()
                        for chunk in r.iter_content(CHUNK_SIZE):
                            if chunk:
                                f.write(chunk)
                    except Exception as ex:
                        print('Download failed: ' + str(ex))
                        continue
        try:
            symlink(path, pathjoin(DOWNLOADS_DIR, submission.title.replace('/', '_')[:256]))
        except FileExistsError as ex:
            print('Symlink for ' + submission.id + ' already exists!')
        sleep(SCRAPE_DELAY)
    else:
        sleep(SCRAPE_SKIP_DELAY)
        print(submission.id + ' has already been scraped')

    print(submission.id, file=cache_file)
