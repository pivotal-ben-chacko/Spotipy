# Spotify RFID Jukebox
#
# Author: Ben Chacko, Hana Chacko 2024
# Description: This project uses the RC522 RFID HAT to read tags and stream the
#              associated album using the Spotify API. You must sign up for a
#              developer account with premium streaming services in order to utilize
#              the Spotify API.
#
# Additional: For simplicity, API calls are made using the Spotipy python module.
#               - https://spotipy.readthedocs.io/en/2.22.1/
#
# Hardware: RC522 RFID HAT
#             - https://seengreat.com/wiki/90/rc522-rfid-hat
#           Raspberry Pi 3 Model B+
#             - https://www.raspberrypi.com/products/raspberry-pi-3-model-b-plus/

import module
import string
import wiringpi
import time
import json

import spotipy
from spotipy.oauth2 import SpotifyOAuth
from time import sleep

import RPi.GPIO as GPIO

DEVICE_ID=<DEVICE-ID>
CLIENT_ID=<CLIENT-ID>
CLIENT_SECRET=<CLIENT-SECRET>

BUTTON_PAUSE_MUSIC = 10
BUTTON_VOL_UP      = 16
BUTTON_VOL_DOWN    = 18


# Specify path to cache file so that Spotify API knows where to look regardles of what directory you are in
# See: https://github.com/spotipy-dev/spotipy/issues/712
CACHE_DIR="/home/pi/Spotipy/src/.cache"

albums = { 0: {"id": "0fWLW9j35eQTrOb8mHcnyX", "rfid": "0000000000000000", "artist": 'Megadeth', "title": "Symphony of Destruction"},
           1: {"id": "2Kh43m04B1UkVcpcRa1Zug", "rfid": "1111111111111111", "artist": 'Metallica', "title": "Black Album"},
           2: {"id": "4Gfnly5CzMJQqkUFfoHaP3", "rfid": "2222222222222222", "artist": 'Likin Park', "title": "Meteora"},
           3: {"id": "3AUIurHdBrfvqSs7EEr3AA", "rfid": "3333333333333333", "artist": 'Skillet', "title": "Rise"},
           4: {"id": "65GdWk0paVbY04benEKKIU", "rfid": "4444444444444444", "artist": "Fear Factory", "title": "Demanufacture"},
           5: {"id": "4Cn4T0onWhfJZwWVzU5a2t", "rfid": "5555555555555555", "artist": "Metallica", "title": "And Justice For All"},
           6: {"id": "5r4qa5AIQUVypFRXQzjaiu", "rfid": "6666666666666666", "artist": "Sepultura", "title": "Chaos A.D."},
           7: {"id": "2WRLwr5MIIXr9gAWOOQ6J5", "rfid": "7777777777777777", "artist": "Static X", "title": "Wisconsin Death Trip"},
           8: {"id": "5iBvQWRRazoyt7CrEPFBsW", "rfid": "8888888888888888", "artist": "Megadeth", "title": "Youthanasia"},
           9: {"id": "3HugnfabsMODIbxzwxS5xC", "rfid": "9999999999999999", "artist": "White Zombie", "title": "Astro-Creep:2000"},
          10: {"id": "09AwlP99cHfKVNKv4FC8VW", "rfid": "1000000000000001", "artist": "Alanis Morissette", "title": "Jagged Little Pill"},
          11: {"id": "1Vze7jtjAVQOdIIQ8oO2X7", "rfid": "2000000000000002", "artist": "Garbage", "title": "20th Anniversary"},
          12: {"id": "5B4PYA7wNN4WdEXdIJu58a", "rfid": "3000000000000003", "artist": "Pearl Jam", "title": "Ten"},
          13: {"id": "1iNAtkD0iP1wEE8ItzfjZk", "rfid": "4000000000000004", "artist": "Godsmack", "title": "Faceless"},
          14: {"id": "4K8bxkPDa5HENw0TK7WxJh", "rfid": "5000000000000005", "artist": "Soundgarden", "title": "Superunknown"},
          15: {"id": "4bPT6Q8ppaSNppk1kbEbLl", "rfid": "6000000000000006", "artist": "Smashing Pumpkins", "title": "Mellon Collie And The Infinite Sadness"},
          16: {"id": "47Z7zIEHWy2ZQQzmg6B1w5", "rfid": "7000000000000007", "artist": "KMFDM", "title": "NIHIL"},
          17: {"id": "2guirTSEqLizK7j9i1MTTZ", "rfid": "8000000000000008", "artist": "Nirvana", "title": "Nevermind"},
          18: {"id": "5QcdaEgknPDT2CwsQ3fKMn", "rfid": "9000000000000009", "artist": "Moist", "title": "Silver"},
          19: {"id": "4mWNf9f6fkznoMKchh2u1M", "rfid": "1100000000000011", "artist": "Our Lady Peace", "title": "Clumsy"},
          19: {"id": "4Io5vWtmV1rFj4yirKb4y4", "rfid": "1200000000000021", "artist": "Rage Against the Machine", "title": "Rage Against the Machine"},
          19: {"id": "0KAj2FT0oe4PgCHdVHjojX", "rfid": "1300000000000031", "artist": "Stabbing Westward", "title": "Wither Blister Burn + Peel"}}

# Singleton Class
class PlayerStateMachine:
  _instance = None

  STATE_PLAYING = 0
  STATE_PAUSED = 1
  STATE_VOLUME = -1

  def __new__(cls):
    if cls._instance is None:
      print("Creating new state machine...")
      cls._instance = super(PlayerStateMachine, cls).__new__(cls)
      return cls._instance

  def __init__(self):
      self.state = 0
      self.albumId = 0
      self.lastButtonPress = 0

      # Spotify Authentication
      self.sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
                                            client_id=CLIENT_ID,
                                            client_secret=CLIENT_SECRET,
                                            cache_path=CACHE_DIR,
                                            redirect_uri="http://localhost:8080",
                                            scope="user-read-playback-state,user-modify-playback-state"))

  def play_music(self, id, resume):
      uri = "spotify:album:" + str(id)
      try :
          # Transfer playback to the Raspberry Pi if music is playing on a different device
          self.sp.transfer_playback(device_id=DEVICE_ID, force_play=resume)
          # Play the spotify track at URI with album ID
          self.sp.start_playback(device_id=DEVICE_ID, context_uri=uri)
          self.albumId = id
          self.state = self.STATE_PLAYING
          # Get current volume level
          self.set_volume()
      except Exception as e:
          print("Error: " + str(e))
          self.state = self.STATE_PAUSED

  def set_volume(self):
      if self.STATE_VOLUME == -1:
          data = self.sp.current_playback(market=None, additional_types=None)
          formated_data = json.dumps(data, indent=2)
          value = json.loads(formated_data)["device"]["volume_percent"]
          self.STATE_VOLUME = int(value / 10) * 10
          print("Current volume: " + str(self.STATE_VOLUME))

  def pause_music(self):
      if (time.time() - self.lastButtonPress) > 1: # Debounce logic to prevent multiple button presses being triggered
          try :
              if self.state == 0:
                  print("Pausing playback...")
                  self.sp.pause_playback(device_id=DEVICE_ID)
                  self.state = self.STATE_PAUSED
              else:
                  print("Resuming playback...")
                  self.sp.transfer_playback(device_id=DEVICE_ID, force_play=True)
                  self.state = self.STATE_PLAYING
              self.lastButtonPress = time.time()
          except Exception as e:
              print("Error: " + str(e))

  def volume_up(self):
      if (time.time() - self.lastButtonPress) > 1: # Debounce logic to prevent multiple button presses being triggered
          try :
             if (self.STATE_VOLUME + 10) <= 100:
                 self.STATE_VOLUME += 10
                 self.sp.volume(self.STATE_VOLUME, device_id=DEVICE_ID)
                 print("Volume set to " + str(self.STATE_VOLUME))
             self.lastButtonPress = time.time()
          except Exception as e:
              print("Error: " + str(e))

  def volume_down(self):
      if (time.time() - self.lastButtonPress) > 1: # Debounce logic to prevent multiple button presses being triggered
          try :
             if (self.STATE_VOLUME - 10) >= 0:
                 self.STATE_VOLUME -= 10
                 self.sp.volume(self.STATE_VOLUME, device_id=DEVICE_ID)
                 print("Volume set to " + str(self.STATE_VOLUME))
             self.lastButtonPress = time.time()
          except Exception as e:
              print("Error: " + str(e))

player = PlayerStateMachine()

rc = module.Rc522_api()
rc.init()
wiringpi.softPwmCreate(24,0,8)

def button_callback(channel):
    player.pause_music()

def volume_up_callback(channel):
    player.volume_up()

def volume_down_callback(channel):
    player.volume_down()

def play_album(index):
    print("Playing " + albums[index]["artist"] + " on Spotify")
    player.play_music(albums[index]["id"], False)

def get_album_size():
    return len(albums)

def get_rfid(index):
    return albums[index]["rfid"]

def play_if_album_exists(rfid):
    for index in albums:
        if get_rfid(index) == rfid:
            play_album(index)
            return True
    return False

# Puase music hardware setup
GPIO.setwarnings(False) # Ignore warning for now
GPIO.setmode(GPIO.BOARD) # Use physical pin numbering
GPIO.setup(BUTTON_PAUSE_MUSIC, GPIO.IN, pull_up_down=GPIO.PUD_DOWN) # Set pin 10 to be an input pin and set initial value to be pulled low (off)
GPIO.add_event_detect(BUTTON_PAUSE_MUSIC, GPIO.RISING,callback=button_callback) # Setup callback event on pin 10 rising edge

# Volume up hardware setup
GPIO.setwarnings(False) # Ignore warning for now
GPIO.setmode(GPIO.BOARD) # Use physical pin numbering
GPIO.setup(BUTTON_VOL_UP, GPIO.IN, pull_up_down=GPIO.PUD_DOWN) # Set pin 16 to be an input pin and set initial value to be pulled low (off)
GPIO.add_event_detect(BUTTON_VOL_UP, GPIO.RISING,callback=volume_up_callback) # Setup callback event on pin 16 rising edge

# Volume down hardware setup
GPIO.setwarnings(False) # Ignore warning for now
GPIO.setmode(GPIO.BOARD) # Use physical pin numbering
GPIO.setup(BUTTON_VOL_DOWN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN) # Set pin 18 to be an input pin and set initial value to be pulled low (off)
GPIO.add_event_detect(BUTTON_VOL_DOWN, GPIO.RISING,callback=volume_down_callback) # Setup callback event on pin 18 rising edge


while True:
    if rc.read(rc.block_num):  # read the content from MiFare RFID card
        wiringpi.digitalWrite(29,0)  # turn on red led
        wiringpi.softPwmWrite(24, 5)
        time.sleep(0.2)
        wiringpi.digitalWrite(29,1)  # turn off red led
        wiringpi.softPwmWrite(24,0)  # turn off buzzer
        time.sleep(0.3)
        s = ""
        for integer in rc.RFID:
            s += str(integer)
        print("read card:", s)
        play_if_album_exists(s) if True else print("Uknown id")

