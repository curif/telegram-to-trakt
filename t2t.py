import config
import json
import re
import html

from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError
from telethon.tl.functions.messages import (GetHistoryRequest)
from telethon.tl.types import (PeerChannel)

# Create the client and connect
client = TelegramClient(config.username, config.api_id, config.api_hash)
client.start()

# Now you can use all client methods listed below, like for example...
#await client.send_message('me', 'Hello to myself!')
print("conectado")

# Python program to illustrate the intersection
# of two lists in most simple way
def intersection(lst1, lst2):
    lst3 = [value for value in lst1 if value in lst2]
    return lst3

toDownload = {}

username = "MoviesTorrentsReleases"
for msg in client.iter_messages(username, limit=500):
  print("===============================================================")
  txt = msg.message.split('\n')
  #j for t in txt:
  #  name = txt
  #  print(t + "=====")  
  #nombre y anio
  nombre = html.unescape(txt[0])
  anio = nombre.rsplit(' ', 1)[1]
  anio = 0 if anio == "N/A" or not anio else int(anio)

  nombre = nombre.rsplit(' ', 1)[0]
  print(nombre, anio)
  
  #genero
  #Animation', 'Action', 'Adventure'
  #['Drama', 'Horror', 'Mystery']
  m = re.search(r"Genre: (.+)", txt[1])
  generos = m.group(1).split('|')
  print('genero: ', generos)

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
  itsGoodQual = people > 100 and evaluation > 5.5
  print('rating de la IMDB: ', rat, 'its good:', itsGoodQual )

  if anio > 2018 \
     and itsGoodQual \
     and len(intersection(generos, [ 'Thriller', 'Horror', 'Mystery', 'Action', 'Adventure', 'Crime', 'Science Fiction' ])) > 0 \
     and len(intersection(generos, [ 'Animation', 'Sports', 'Documentary', 'Biography' ])) == 0: 
      print("DOWNLOAD IT!!!!")
      toDownload[nombre] = anio
  else:
      print("NOT match")

 # for t in txt:
 #   name = txt
 #   print(t + "=====")

print(toDownload)
