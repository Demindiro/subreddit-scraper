# A simple subreddit scraper


## Setup

0. Run this:
```
python3 -m venv venv
source venv/bin/activate
pip3 install -r requirements
```

1. Go here and get a client ID and secret: https://www.reddit.com/prefs/apps/

2. Paste this in `config.py` and fill in the blanks:
```
CLIENT_ID     = '<id>'
CLIENT_SECRET = '<secret>'

CHUNK_SIZE = 4096 * 4
DOWNLOADS_DIR = 'downloads'

USER_AGENT = 'Bond, James Bond'

SUBREDDIT = 'ProgrammerHumor'
BATCH_SIZE = 1
SORT = 'top'

SCRAPE_DELAY      = 1
SCRAPE_SKIP_DELAY = 0.25
```

3. Create the directory `downloads/` (Yes this should be done automatically but I'm lazy)


## Run

```
./scraper.py
```
