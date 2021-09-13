This program explore a specific Telegram channel with movies information and, if the movie cumpliment some requirements, is added to a Trakt list (only if the movie was not watched previously)

# requeriments

Please read the `requirements.txt` to understand the dependencies.

# config.json

Create a json file (you can copy the `config.json.example` in the `config/` subdir).

```json
{
    "schedule_hours": 6,

    "channel_username": "MoviesTorrentsReleases",
    "filters": {
	    "from_year": 2020,
	    "filter_list": [ {
            "imdb_range": [5.5, 5.99],
            "imdb_people": 100,
            "include_genres": [ "Horror", "Sci-Fi" ],
            "exclude_genres": [ "Comedy", "Animation", "Sports", "Documentary", "Biography", "Short" ]
          }, {
            "imdb_range": [6, 6.99],
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
        * imdb_range: from/to califications. If the movie has califications between this range the movie will be selected.
        * imdb_people: minimal quantity of people who voted.
        * include_genres: the movie must to have at least one of those genres. Empty means "all"
        * exclude_genres: if the movie has at least one of those will be exluded. Empty means "all"
* trakt: trakt connection information (see below)
* telegram: telegram connection information (see below)

# Trakt
In particular, the `trakt.py` library needs to connect this application to Trakt, and to give permissions to your Trakt user. For that you will need to create a new application in Trakt to obtain your `id` and `secret`.

Goto https://trakt.tv/oauth/applications/new

# Telegram

The connection with telegram is managed with the `telethon` library. You must to create a new application and fill the data in your `config.json` file in the `config` directory.

To know how to create the application please follow the instructions in the `telethon` page: https://docs.telethon.dev/en/latest/basic/signing-in.html

Telethon uses a `session` file (the program name it as `/config/<your user>.session`. To create the session file for first time you'd use the `create_session.py` program. Depending of the type of authentication you use the program will ask for a confirmation token that you will receive in your telegram client as a message.

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
      context: ./telegram-to-trakt
    image: telegram-to-trakt:latest
    volumes:
     - /home/xxxx/telegram-to-trakt/config:/usr/src/app/config
    environment:
      TZ: America/Argentina/Buenos_Aires
    restart: unless-stopped

```
