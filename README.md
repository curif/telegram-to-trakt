This program explore a specific Telegram channel with movies information and, if the movie fullfill the configured requirements, is added to a Trakt list (only if the movie was not watched previously)

# Instalation

Download the code and copy to a directory of your preference. 

# Requeriments

Please read the `requirements.txt` to understand the dependencies.

Run de requirements install:

```bash
pip3 install -r requirements.txt
```
# config.json

Create a json file (you can copy the `config.json.example` in the `config/` subdir).

```json
{
    "schedule_hours": 6,

    "channel_username": "MoviesTorrentsReleases",
    "filters": {
	    "from_year": 2020,
	    "filter_list": [ {
		    "imdb_range": [5.5, 100],
		    "imdb_people": 100,
		    "include_genres": [ "Horror", "Sci-Fi" ],
		    "exclude_genres": [ "Comedy", "Animation", "Sports", "Documentary", "Biography", "Short" ]
		  }, {
		    "imdb_range": [6, 100],
		    "imdb_people": 500,
		    "include_genres": [ "Thriller", "Horror", "Mystery", "Action", "Adventure", "Crime", "Sci-Fi" ],
		    "exclude_genres": [ "Animation", "Sports", "Documentary", "Short" ]
		  }, {
		    "imdb_range": [7, 100],
		    "imdb_people": 1000,
		    "include_genres": [],
		    "exclude_genres": [ "Animation", "Sports", "Documentary", "Short" ]
		  }
      ]
    },
    "trakt": {
        "base_url": "https://api.trakt.tv",
        "id": "your id here",
        "secret": "your secret",
        "list": "MyList",
	"user": "MyTraktUser"
    },
   "telegram": {
      "api_id": "id number",
      "api_hash": "telegram hast",
      "username": "your user name",
       "phone": "+54115555555"
  }
}
```
* schedule_hours: time between executions
* channel_username: is the name of the channel to explore. Obviously if this specific channel changes o disappear the program will be useless.
* filters: requeriments to select a movie.
    * from_year: ignore movies realased before this date.
    * filter_list: list of filters to apply (in order)
        * imdb_range: from/to califications. A movie with califications between this range will be selected and added to the list.
        * imdb_people: minimal quantity of people who voted.
        * include_genres: the movie must to have at least one of those genres. Empty means "all"
        * exclude_genres: if the movie has at least one of those will be exluded. Empty means "all"
* trakt: 
    * trakt connection information (see below)
    * list: a trakt user list where you add the movies of intereset.
* telegram: telegram connection information (see below)

# Examples

In the configuration example above, a Drama movie with a calification of 8/17000 (17000 votes that result in a calification of eight) will be selected. Instead, if the movie is a Sport Drama will be excluded .

A Horror movie with a calification of 5.5/200 will be selected. The same but animation horror will be excluded. Usefull if you like Horror movies but not the Animation genre.

This configuration catches any movie with a calification 7/1000 or above. But exclude Shorts for example.

# Trakt

The `trakt.py` library needs to connect this application to Trakt, and to give permissions to your Trakt user. For that you will need to create a new application in Trakt to obtain your `id` and `secret`.

Goto https://trakt.tv/oauth/applications/new

Copy the id and secret to your config.json.

# Telegram

The connection with telegram is managed with the `telethon` library. You must to create a new application and fill the data in your `config.json` file in the `config` directory.

To know how to create the application please follow the instructions in the `telethon` page: https://docs.telethon.dev/en/latest/basic/signing-in.html

Telethon uses a `session` file (the program name it as `/config/<your user>.session`. To create the session file for first time you'd use the `create_session.py` program. Depending of the type of authentication you use the program may ask for a confirmation token that you will receive in your telegram client as a message.

# Docker

A `dockerfile` is provided in order to use the program under docker.

## docker create image

`docker build -t telegram-to-trakt .`

## create session

To create the session file using docker:

```bash
sudo docker run -v $(pwd)/telegram-to-trakt/config:/usr/src/app/config -it telegram-to-trakt bash
root@8e1193bedf7f:/usr/src/app# python create_session.py
connect to telegram API
Please enter the code you received: xxxxx
Signed in successfully as Curif
session created

```

## docker-compose example

```yaml
  telegram_to_track:
    build:
      context: ./<folder where the software was copied>
    image: telegram-to-trakt:latest
    volumes:
     - /home/<your user>/<folder where the software was copied>/config:/usr/src/app/config
    environment:
      TZ: America/Argentina/Buenos_Aires
    restart: unless-stopped

```
