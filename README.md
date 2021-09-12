docker create image

docker build -t telegram-to-trakt .

create session

sudo docker run -v $(pwd)/telegram-to-trakt/config:/usr/src/app/config -it telegram-to-trakt bash
root@8e1193bedf7f:/usr/src/app# python create_session.py
connect to telegram API
Please enter the code you received: 93720
Signed in successfully as Curif
session created
