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

after_id = None
batch_num = 0
total_dl   = 0
total_skip = 0

while True:
    print('=== BATCH ' + str(batch_num) + ' ===')
    batch_num += 1
    batch_dl   = 0
    batch_skip = 0
    for submission in reddit.subreddit(SUBREDDIT).search(
            'subreddit:' + SUBREDDIT, # Empty queries don't work so...?
            sort   = SORT,
            # t3_ == type is a link == a submission, basically
            params = { 'after': 't3_' + str(after_id) },
            limit  = BATCH_SIZE
        ):
        if submission.selftext != '':
            ext = '.txt'
        else:
            req = requests.head(submission.url)
            ctype = req.headers.get('content-type', '')
            if ctype.startswith('image/'):
                ext = guess_extension(ctype.split(' ', 2)[0])
                # Goddamnit mimetypes
                if ext == '.jpe':
                    ext = '.jpg'
            else:
                print('Skipping ' + submission.id + ' (MIME type is ' + ctype + ')')
                batch_skip += 1
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
            batch_dl += 1
            sleep(SCRAPE_DELAY)
        else:
            print(submission.id + ' has already been scraped')
            batch_skip += 1
            sleep(SCRAPE_SKIP_DELAY)

    total_dl   += batch_dl
    total_skip += batch_skip
    if batch_dl == 0 and batch_skip == 0:
        break
    after_id = submission.id


print('Total batches:', batch_num)
print('Total downloads:', total_dl)
print('Total skips:', total_skip)
