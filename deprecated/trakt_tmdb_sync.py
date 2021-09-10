

from __future__ import absolute_import, division, print_function
import sys
from typing import Optional
 #2017  pip3 install pycliarr==1.0.14
 #2018  pip3 install trakt.py

from trakt import Trakt

import time

import os
import json
from datetime import datetime, timedelta

import pprint

from tmdbv3api import TMDb
from tmdbv3api import Account
from tmdbv3api import Authentication
from tmdbv3api import Find

from threading import Condition

config = {}

pp = pprint.PrettyPrinter(indent=2)

class Application(object):
    def __init__(self):
        self.is_authenticating = Condition()

        self.authorization = None
        
        # Bind trakt events
        Trakt.on('oauth.token_refreshed', self.on_token_refreshed)

    def authenticate(self):
        if not self.is_authenticating.acquire(blocking=False):
            print('Authentication has already been started')
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
            print('ERROR: Authentication required')
            exit(1)
     
        #STrakt.configuration.oauth.from_response(self.authorization)   
        Trakt.configuration.defaults.oauth.from_response(self.authorization)
        
        tmdb = TMDb()
        tmdb.api_key = config["tmdb"]["api_key"]
        auth = Authentication(username=config["tmdb"]["user"], password=config["tmdb"]["password"])
        account = Account()
        details = account.details()
        print(
            "You are logged in to tmdb as %s. Your account ID is %s." % (details.username, details.id)
        )

        print("Retrieve watched from trakt")
        # ('imdb', 'tt1815862'): <Movie 'After Earth' (2013)>
        watched = {}
        Trakt['sync/watched'].movies(watched, exceptions=True)
        #pp.pprint(watched)
        imdbInWatched = [ movie[1] 
                        if "imdb" == movie[0] else "no" 
                        for movie in watched 
                    ]

        print("Retrieve movies in list [{}]".format(config["trakt"]["list"]))
        traktInList = Trakt['users/*/lists/*'].items(
                            config["trakt"]["user"],
                            config["trakt"]["list"],
                            media="movies",
                            exceptions=True
                            )
        #pp.pprint(traktInList)
        if not traktInList:
            raise(Exception("can't retrieve list movies"))


        #delete watched from list
        filtered = list(filter(
                lambda m: m.pk[0]=="imdb" and m.pk[1] not in imdbInWatched, 
                traktInList
                ))
        pp.pprint(list(filtered))
        pp.pprint([m.pk[0] for m in traktInList])

        #add to tmdb watched
        find = Find() 
        for m in filtered:
            print("find {}".format(m.pk[1]))
            tmdbMovie = find.find_by_imdb_id(m.pk[1])
            pp.pprint(tmdbMovie)
        

        print("Finished =====")


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
        print(config)
    
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

