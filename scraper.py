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

for submission in reddit.subreddit(SUBREDDIT).new(limit=9999999999999999):
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
        except FileExistsError as ex:
            print('Symlink for ' + submission.id + ' already exists!')
        sleep(SCRAPE_DELAY)
    else:
        print(submission.id + ' has already been scraped')
        sleep(SCRAPE_SKIP_DELAY)
