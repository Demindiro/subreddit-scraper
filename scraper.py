#!venv/bin/python3

from config import *
from praw import Reddit
from time import sleep
from os import symlink
from os.path import isfile, join as pathjoin
import requests
from mimetypes import guess_extension



"""
Globals
"""

reddit = Reddit(
    client_id     = CLIENT_ID,
    client_secret = CLIENT_SECRET,
    user_agent    = USER_AGENT
)


"""
Main
"""

for submission in reddit.subreddit(SUBREDDIT).new(limit=999999999999999999999999):

    if submission.selftext != '':
        ext = '.txt'
    else:
        req = requests.head(submission.url)
        ctype = req.headers.get('content-type', '')
        if ctype.startswith('image/'):
            ext = guess_extension(ctype.split(' ', 2)[0])
            # Goddamnit mimetypes
            if ext == 'jpe':
                ext = 'jpg'
        else:
            print('Skipping ' + submission.id + ' (MIME type is ' + ctype + ')')
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
        try:
            symlink(path, pathjoin(DOWNLOADS_DIR, submission.title.replace('/', '_')))
        except FileExistError as ex:
            print('Symlink for ' + submission.id + ' already exists!')
        sleep(SCRAPE_DELAY)
    else:
        print(submission.id + ' has already been scraped')
        sleep(SCRAPE_SKIP_DELAY)

