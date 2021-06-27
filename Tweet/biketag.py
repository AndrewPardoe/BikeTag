from bs4 import BeautifulSoup
from collections import namedtuple
from dotenv import load_dotenv, find_dotenv
from PIL import Image
import os
import requests
import tempfile
import tweepy

status_text = \
    "Seattle BikeTag!\n\n" + \
    "This is bike tag number {} by {}.\n" + \
    "Find this mystery location and move the tag to your favorite spot. " + \
    "The latest tag, instructions, and a hint are at https://seattle.biketag.org\n" + \
    "\n" + \
    "#SeattleBikeTag #SeaBikes #BikeSeattle"

def safeprint(string):
    substitute = '~'
    try:
        print(string)
    except UnicodeEncodeError:
        for char in string:
            try:
                print(char, end='')
            except UnicodeEncodeError:
                print(substitute, end='')

def oauth_login():    
    load_dotenv(find_dotenv())
    consumer_key = os.environ.get("consumer_key")
    consumer_secret = os.environ.get("consumer_secret")
    access_token = os.environ.get("access_token")
    access_token_secret = os.environ.get("access_token_secret")
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)
    return tweepy.API(auth)

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

def create_photo(div):
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
    # string 1 is number, string 2 is name
    tagstrings = []
    for string in div.stripped_strings:
        tagstrings.append(repr(string))
    TagData = namedtuple('TagData', 'number name')
    TagData.number = tagstrings[1].strip('\'')
    TagData.name = tagstrings[2].strip('\'')
    return TagData

if __name__ == "__main__":
    post = get_imgur_post('https://seattle.biketag.org/#')
    photo = create_photo(post)
    tagdata = get_tagdata(post)


    # Log into Twitter
    api = oauth_login()
    print("Authenticated as: {}".format(api.me().screen_name))

    image = api.media_upload(photo)

    # TODO ALT text doesn't work?
    api.create_media_metadata(image.media_id, 'Bike at mystery BikeTag location')  

    lasttag = get_last_tag_tweet(api)
    if lasttag < int(tagdata.number): 
        status_text = status_text.format(tagdata.number, tagdata.name)
        status = api.update_status(status=status_text, media_ids=[image.media_id])
        print("Tweeted with id {}".format(status.id))
        print("https://twitter.com/tag/status/{}".format(status.id))
    else:
        print("Already tweeted tag number {}".format(lasttag))

    delete_photo(photo)


