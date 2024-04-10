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

import spotipy
from spotipy.oauth2 import SpotifyOAuth
from time import sleep

import RPi.GPIO as GPIO

DEVICE_ID="<DEVICE-ID>"
CLIENT_ID="<CLIENT-ID>"
CLIENT_SECRET="<CLIENT-SECRET>"

# Singleton Class
class PlayerStateMachine:
  _instance = None

  STATE_PLAYING = 0
  STATE_PAUSED = 1

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
      self.sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=CLIENT_ID,
                                            client_secret=CLIENT_SECRET,
                                            redirect_uri="http://localhost:8080",
                                            scope="user-read-playback-state,user-modify-playback-state"))

  def play_music(self, id, resume):
      uri = "spotify:album:" + str(id)
      try :
          # Transfer playback to the Raspberry Pi if music is playing on a different device
          self.sp.transfer_playback(device_id=DEVICE_ID, force_play=resume)
          # Play the spotify track at URI with album ID
          self.sp.start_playback(device_id=DEVICE_ID, context_uri=uri)
          self.sp.volume(100, device_id=DEVICE_ID)
          self.albumId = id
          self.state = self.STATE_PLAYING
      except Exception as e:
          print("Error: " + str(e))
          self.state = self.STATE_PAUSED

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


player = PlayerStateMachine()

rc = module.Rc522_api()
rc.init()
wiringpi.softPwmCreate(24,0,8)

def button_callback(channel):
    player.pause_music()

GPIO.setwarnings(False) # Ignore warning for now
GPIO.setmode(GPIO.BOARD) # Use physical pin numbering
GPIO.setup(10, GPIO.IN, pull_up_down=GPIO.PUD_DOWN) # Set pin 10 to be an input pin and set initial value to be pulled low (off)
GPIO.add_event_detect(10,GPIO.RISING,callback=button_callback) # Setup callback event on pin 10 rising edge

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
        if s == "0000000000000000":
            print("Playing Megadeth on Spotify")
            player.play_music("0fWLW9j35eQTrOb8mHcnyX", False)
        elif s == "1111111111111111":
            print("Playing Mitski on Spotify")
            player.play_music("38W7WU8kz5SHqcNdx9ZtmC", False)
        else:
            print("Uknown id")
