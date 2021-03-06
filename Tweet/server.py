import collections
import logging
from dotenv import load_dotenv, find_dotenv
import tweepy
import os
import shutil
import sys
import tempfile
import requests
import time

status_template = \
    "Seattle BikeTag!\n\n" + \
    "This is bike tag number {} by {}.\n" + \
    "Find this mystery location and move the tag to your favorite spot. " + \
    "The latest tag, instructions, and a hint are at https://seattle.biketag.org\n" + \
    "\n" + \
    "#SeattleBikeTag #SeaBikes #BikeSeattle"

biketagsite = 'https://seattle.biketag.org/current/?data=true'

def oauth_login(api):
    try:
        api.verify_credentials()
    except:
        logging.debug("Searching for login credentials")
        if os.path.exists('.env'):
            load_dotenv(find_dotenv())
        else:
            sys.exit("OAuth keys .env not found. Aborting.")
        consumer_key = os.environ.get("consumer_key")
        consumer_secret = os.environ.get("consumer_secret")
        access_token = os.environ.get("access_token")
        access_token_secret = os.environ.get("access_token_secret")
        try:
            logging.debug("Authenticating with Twitter")
            auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
            auth.set_access_token(access_token, access_token_secret)
            api = tweepy.API(auth)
            logging.info("Authenticated as: {}".format(api.me().screen_name))
        except tweepy.TweepError:
            sys.exit("Failed to authorize user. Aborting.")
    return api

def get_last_tag_tweet(api):
    # Read last tweeted tag from the SeattleBikeTag timeline.
    # Precondition: First number in the tweet being the tag number.
    logging.debug ("Getting last tweeted tag number")
    tweet = api.user_timeline(id=api.me().id, count=1)
    tagnumber = [int(w) for w in tweet[0].text.split() if w.isdigit()]
    if len(tagnumber) == 0: # If first tweet isn't a tag tweet, return something
        return 0
    else:
        return tagnumber[0]

def upload_photo(tag, api):
    # Download image and save in temporary file: Twitter can't upload from URL
    logging.debug ("Uploading photo")
    filename = tempfile.gettempdir() + os.sep + 'biketag' + tag.extension
    r = requests.get(tag.image, stream=True)
    if r.status_code == 200:
        with open(filename, 'wb') as f:
            r.raw.decode_content = True
            shutil.copyfileobj(r.raw, f)   
    alttext = "{}'s bike at SeattleBikeTag mystery location #{}.".format(tag.credit, tag.number)
    image = api.media_upload(filename)
    api.create_media_metadata(image.media_id, alttext)  
    if os.path.exists(filename):
        os.remove(filename)
    return image

def update_status(text, image, tag, api):
    logging.debug ("Updating status")
    text = text.format(tag.number, tag.credit)
    status = api.update_status(status=text, media_ids=[image.media_id])
    logging.info("Tweeted #{} with id {}".format(tag.number, status.id))
    logging.info("https://twitter.com/tag/status/{}".format(status.id))

def get_tag(biketagsite):
    logging.debug ("Fetching data from biketag.org")
    tag_data = requests.get(biketagsite).json()
    tag = collections.namedtuple('tag', 'credit, number, image, extension')
    tag.credit = tag_data['credit']
    tag.number = tag_data["currentTagNumber"]
    tag.extension = tag_data['currentTagURLExt']
    # Imgur's 'huge' thumbnail is 1024x1024, accessed with 'h' at end of filename
    image_url = tag_data["currentTagURL"]
    if image_url.endswith(tag.extension):
        tag.image = image_url[:-len(tag.extension)] + 'h' + tag.extension
    else:
        tag.image = image_url
    return tag

# TODO Make this more intelligent with regards to sleeping longer at night, shorter in busy periods, etc.
def wait(delay):
    local_time = time.localtime(time.time())
    logging.info ("Sleeping for {} minutes at {}".format(delay, time.asctime(local_time)))
    time.sleep(delay * 60)

    hour = local_time.tm_hour
    # day = local_time.tm_wday

    max_delay = 60
    if hour < 8 or hour > 20:       # middle of the night
        max_delay = 120
    elif hour > 14 and hour < 20:   # middle of the day
        max_delay = 30
    if delay < max_delay:
        delay += 5
    elif delay > max_delay:
        delay = max_delay
    return delay

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    while(True):
        api = 0
        lasttweet = 0
        delay = 5
        try:
            while(True):
                tag = get_tag(biketagsite)
                if (tag.number > lasttweet):
                    lasttweet = int(tag.number) 
                    delay = 5
                    api = oauth_login(api)
                    lasttag = get_last_tag_tweet(api)
                    if lasttag < int(tag.number): 
                        image = upload_photo(tag, api)
                        update_status(text=status_template, image=image, tag=tag, api=api)
                    else:
                        logging.info("Already tweeted tag number {}".format(lasttag))
                else:
                    delay = wait(delay)
        except Exception as e:
            if hasattr(e, 'message'):
                print(e.message)
            else:
                print(e)
            wait(5)
            continue
        





