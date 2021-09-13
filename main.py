from __future__ import absolute_import, division, print_function
import sys
from typing import Optional
 #2017  pip3 install pycliarr==1.0.14
 #2018  pip3 install trakt.py

from trakt import Trakt

from pycliarr.api import RadarrCli
import schedule
import time

from threading import Condition
import logging
import os
import json
from datetime import datetime, timedelta

import re
import html
import pprint

from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError
from telethon.tl.functions.messages import (GetHistoryRequest)
from telethon.tl.types import (PeerChannel)

logging.basicConfig(format='%(asctime)s [%(levelname)s] %(message)s', level=logging.INFO)


config = {}

pp = pprint.PrettyPrinter(indent=2)

# Python program to illustrate the intersection
# of two lists in most simple way
def intersection(lst1, lst2):
    lst3 = [value for value in lst1 if value in lst2]
    return lst3

class Application(object):
    def __init__(self):
        self.is_authenticating = Condition()

        self.authorization = None
        
        # Bind trakt events
        Trakt.on('oauth.token_refreshed', self.on_token_refreshed)

    def authenticate(self):
        if not self.is_authenticating.acquire(blocking=False):
            logging.info('Authentication has already been started')
            return False

        # Request new device code
        code = Trakt['oauth/device'].code()

        print('Enter the code "%s" at %s to authenticate your account' % (
            code.get('user_code'),
            code.get('verification_url')
        ))

        # Construct device authentication poller
        poller = Trakt['oauth/device'].poll(**code)\
            .on('aborted', self.on_aborted)\
            .on('authenticated', self.on_authenticated)\
            .on('expired', self.on_expired)\
            .on('poll', self.on_poll)

        # Start polling for authentication token
        poller.start(daemon=False)

        # Wait for authentication to complete
        return self.is_authenticating.wait()

    def run(self):
        if not self.authorization:
          self.authenticate()

        if not self.authorization:
            logging.error('ERROR: Authentication required')
            exit(1)
     
        #STrakt.configuration.oauth.from_response(self.authorization)   
        Trakt.configuration.defaults.oauth.from_response(self.authorization)
        
        logging.info("Retrieve watched from trakt")
        # ('imdb', 'tt1815862'): <Movie 'After Earth' (2013)>
        watched = {}
        Trakt['sync/watched'].movies(watched, exceptions=True)
        #pp.pprint(watched)

        imdb_in_watched = [
                imdb_key[1]
                for imdb_key in watched.keys()
                if imdb_key[0] == "imdb"
                ]
        #pp.pprint(imdb_in_watched)        

        logging.info("Retrieve movies in list [{}]".format(config["trakt"]["list"]))
        trakt_in_list = Trakt['users/*/lists/*'].items(
                            config["trakt"]["user"],
                            config["trakt"]["list"],
                            media="movies",
                            exceptions=True
                            )
        #pp.pprint(trakt_in_list)
        if not trakt_in_list:
            raise(Exception("can't retrieve list movies"))
        
        imdb_in_list = [ 
                movie.pk[1] 
                for movie in trakt_in_list 
                if movie.pk[0] == "imdb"
                ]
        #pp.pprint(imdb_in_list)

        # Create the client and connect
        logging.info("Connect to telegram API")
        client = TelegramClient(
                "./config/{}.session".format(config["telegram"]["username"]), 
                config["telegram"]["api_id"], 
                config["telegram"]["api_hash"]
                )
        client.start(phone=config["telegram"]["phone"])
                 
        collected = {}
        for msg in client.iter_messages(config["channel_username"], limit=500):
          #print("===============================================================")
          txt = msg.message.split('\n')
          
          #name y year
          name = html.unescape(txt[0])
          
          year = name.rsplit(' ', 1)[1]
          year = 0 if year == "N/A" or not year else int(year)

          name = name.rsplit(' ', 1)[0]
          #print(name, year)
          
          #genero
          #Animation', 'Action', 'Adventure'
          #['Drama', 'Horror', 'Mystery']
          m = re.search(r"Genre: (.+)", txt[1])
          genres = m.group(1).split('|')
          #print('genero: ', genres)

          #imdb rating
          m = re.search(r"IMDB Rating: (.+)", txt[2])
          rating = m.group(1)
          if rating == 'N/A/N/A':
              rat = [0,0]
              evaluation = 0
              people = 0
          else:
              rat = rating.split('/')
              evaluation = float(rat[0])
              people = int(rat[1])
          #print('rating de la IMDB: ', rat, 'its good:', itsGoodQual )

          imdb_key = None
          m = re.search(r"https://www.imdb.com/title/(.+)/", txt[3])
          if m:
              imdb_key = m.group(1)
          
          if not imdb_key:
              logging.debug("[{}] don't have and imdb key".format(name))
              continue
          
          if imdb_key not in imdb_in_list and imdb_key not in imdb_in_watched:
             collected[imdb_key] = {
                     "imdb": imdb_key,
                     "name": name,
                     "year": year,
                     "to_download": False,
                     "calification": evaluation,
                     "people": people,
                     "genres": genres
                  }
          logging.debug("Discovered: {} ({}) [imdb: {}] {}/{} - {}".format(name, year, imdb_key, evaluation, people, genres))        
        

        logging.info("Filter {} collected movies".format(len(collected))) 
        for imdb_key, movie in collected.items():
          if movie["year"] >= config["filters"]["from_year"]:
              for fil in config["filters"]["filter_list"]:
                  if movie["calification"] >= fil["imdb_range"][0] and movie["calification"] <= fil["imdb_range"][1]:
                      if movie["people"] >= fil["imdb_people"]:
                        if ( len(fil["include_genres"]) == 0 or len(intersection(movie["genres"] , fil["include_genres"])) > 0 ) \
                             and ( len(fil["exclude_genres"]) == 0 or len(intersection(movie["genres"], fil["exclude_genres"])) == 0 ): 
                              movie["to_download"] = True
                              break
        
        #pp.pprint([movie for imdb, movie in collected.items() if movie["to_download"]])

        to_add = { "movies": [ 
                   {"ids": {
                       'imdb': imdb
                       }
                   } for imdb, movie in collected.items() if movie["to_download"]
                ]
        }
        logging.info("Add movies to list [{}]".format(config["trakt"]["list"]))
        if len(to_add["movies"]) > 0:
            logging.info(pprint.pformat(to_add))
            result = Trakt['users/*/lists/*'].add(
                                config["trakt"]["user"],
                                config["trakt"]["list"],
                                to_add,
                                exceptions=True
                                )
            logging.info("{} added to the list".format(result["added"]["movies"]))
            logging.info("not found: {}".format(pprint.pformat(result["not_found"]["movies"])))
        else:
            logging.info("No new movies to add.")
        
        logging.debug("telegram disconnect.")
        client.disconnect() 
        
        logging.info("Finished =====")

        #for name, d in toDownload.items():
        #     muvi = Trakt["movies"].get(d["imdb"])
        #     print(muvi)
        #      #print(vars(muvi))
        #      print("listed", muvi.listed_at)
        #      print("collected:", muvi.collected_at)
        #      print("watched:", muvi.watched_at)
        #      pp.pprint(muvi.to_json())
        #      print("-------------")
 

    def on_aborted(self):
        """Device authentication aborted.

        Triggered when device authentication was aborted (either with `DeviceOAuthPoller.stop()`
        or via the "poll" event)
        """

        print('Authentication aborted')

        # Authentication aborted
        self.is_authenticating.acquire()
        self.is_authenticating.notify_all()
        self.is_authenticating.release()

    def on_authenticated(self, authorization):
        """Device authenticated.

        :param authorization: Authentication token details
        :type authorization: dict
        """

        # Acquire condition
        self.is_authenticating.acquire()

        # Store authorization for future calls
        self.authorization = authorization

        print('Authentication successful - authorization: %r' % self.authorization)

        # Authentication complete
        self.is_authenticating.notify_all()
        self.is_authenticating.release()

        self.save_token()

    def on_expired(self):
        """Device authentication expired."""

        print('Authentication expired')

        # Authentication expired
        self.is_authenticating.acquire()
        self.is_authenticating.notify_all()
        self.is_authenticating.release()

    def on_poll(self, callback):
        """Device authentication poll.

        :param callback: Call with `True` to continue polling, or `False` to abort polling
        :type callback: func
        """

        # Continue polling
        callback(True)

    def on_token_refreshed(self, authorization):
        # OAuth token refreshed, store authorization for future calls
        self.authorization = authorization

        print('Token refreshed - authorization: %r' % self.authorization)
        self.save_token()

    def save_token(self):
        with open("config/authtoken.json", 'w') as outfile:
          json.dump(self.authorization, outfile)

def execute():
    app = Application()
    if os.path.exists("config/authtoken.json"):
        #authorization = os.environ.get('AUTHORIZATION')
        with open("config/authtoken.json", 'r') as file:
            app.authorization = json.load(file)
    app.run()

if __name__ == '__main__':
    #global config

    # Configure
    if not os.path.exists("config/config.json"):
        raise Exception("Error config.json not found")
    with open("config/config.json", 'r') as file:
        config  = json.load(file)
        #print(config)

    
    Trakt.base_url = config["trakt"]["base_url"]

    Trakt.configuration.defaults.client(
      id=config["trakt"]["id"],
      secret=config["trakt"]["secret"],
    )

    # first auth
    if not os.path.exists("config/authtoken.json"):
        print('auth...')
        app = Application()
        app.authenticate()
        if not os.path.exists("config/authtoken.json"):
            print('Auth failed!')
            sys.exit(-1)
    
    execute()
    
    logging.info("Waiting...")

    schedule.every(config["schedule_hours"]).hours.do(execute)
    while True:
        schedule.run_pending()
        #print("waiting...")
        time.sleep(60)  
