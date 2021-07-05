from bs4 import BeautifulSoup
from collections import namedtuple
from dotenv import load_dotenv, find_dotenv
from PIL import Image
import lxml # needed by bs4
import os
import requests
import sys
import tempfile
import time
import tweepy

status_template = \
    "Seattle BikeTag!\n\n" + \
    "This is bike tag number {} by {}.\n" + \
    "Find this mystery location and move the tag to your favorite spot. " + \
    "The latest tag, instructions, and a hint are at https://seattle.biketag.org\n" + \
    "\n" + \
    "#SeattleBikeTag #SeaBikes #BikeSeattle"

# TODO: Implement "catchup" for when we've missed a post
biketagsite = 'https://seattle.biketag.org/#'

def oauth_login():
    if os.path.exists('.env'):
        load_dotenv(find_dotenv())
    else:
        sys.exit("OAuth keys .env not found. Aborting.")
    consumer_key = os.environ.get("consumer_key")
    consumer_secret = os.environ.get("consumer_secret")
    access_token = os.environ.get("access_token")
    access_token_secret = os.environ.get("access_token_secret")

    try:
        auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
        auth.set_access_token(access_token, access_token_secret)
        api = tweepy.API(auth)
        print("Authenticated as: {}".format(api.me().screen_name))
    except tweepy.TweepError:
        sys.exit("Failed to authorize user. Aborting.")
    
    return api

def get_last_tag_tweet(api):
    tweet = api.user_timeline(id=api.me().id, count=1)
    # This relies on the first number in the tweet being the tag number
    tagnumber = [int(w) for w in tweet[0].text.split() if w.isdigit()]
    return tagnumber[0]

def get_imgur_post(page):
    soup = BeautifulSoup(requests.get(page).content, "lxml")
    body = soup.find('body')
    div = body.find('div', class_='m-imgur-post')
    return div

def create_photo_file(div):
    twitter_max_size = (2200, 2200)
    image = div.find('img')
    image_url = image['data-src']
    img = Image.open(requests.get(image_url, stream = True).raw)
    img.thumbnail(size = twitter_max_size)
    filename = tempfile.gettempdir() + '/biketag.jpg'
    img.save(filename)
    return filename

def delete_photo(filename):
    if os.path.exists(filename):
        os.remove(filename)

def get_tagdata(div):
    # string 1 is number, string 2 is name, relies on biketag post format
    tagstrings = []
    for string in div.stripped_strings:
        tagstrings.append(repr(string))
    TagData = namedtuple('TagData', 'number name')
    TagData.number = tagstrings[1].strip('\'')
    TagData.name = tagstrings[2].strip('\'')
    return TagData

def upload_photo(photo, tagdata, api):
    alttext = "{}'s bike at SeattleBikeTag mystery location #{}.".format(tagdata.name, tagdata.number)
    image = api.media_upload(photo)
    api.create_media_metadata(image.media_id, alttext)  
    delete_photo(photo)
    return image

def update_status(text, image, api):
    text = text.format(tagdata.number, tagdata.name)
    status = api.update_status(status=text, media_ids=[image.media_id])
    print("Tweeted with id {}".format(status.id))
    print("https://twitter.com/tag/status/{}".format(status.id))



if __name__ == "__main__":
    lasttweet = 0
    sleepytime = 5 
    while(True):
        post = get_imgur_post(biketagsite)
        tagdata = get_tagdata(post)
        if (int(tagdata.number) > lasttweet):
            sleepytime = 5
            photo = create_photo_file(post)
            try:
                api.verify_credentials()
            except:
                api = oauth_login()
            lasttag = get_last_tag_tweet(api)
            if lasttag < int(tagdata.number): 
                image = upload_photo(photo, tagdata, api)
                update_status(status_template, image, api)
            else:
                print("Already tweeted tag number {}".format(lasttag))
        else:
            time.sleep(sleepytime)
            print ("Sleeping for {} minutes.".format(sleepytime))
            if sleepytime < 40:
                sleepytime *= 2
        lasttweet = int(tagdata.number)




