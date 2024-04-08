import module
import string
import wiringpi
import time

import spotipy
from spotipy.oauth2 import SpotifyOAuth
from time import sleep

import RPi.GPIO as GPIO

DEVICE_ID="<DEVICE-ID"
CLIENT_ID="CLIENT-ID"
CLIENT_SECRET="CLIENT-SECRET"

ALBUM_ID=0

BUTTON_PRESS_TIME=0
PLAYBACK_STATE=0

# Spotify Authentication
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=CLIENT_ID,
                                                client_secret=CLIENT_SECRET,
                                                redirect_uri="http://localhost:8080",
                                                scope="user-read-playback-state,user-modify-playback-state"))

rc = module.Rc522_api()
rc.init()
wiringpi.softPwmCreate(24,0,8)

def button_callback(channel):
    global BUTTON_PRESS_TIME
    global PLAYBACK_STATE
    if (time.time() - BUTTON_PRESS_TIME) > 1:
        if PLAYBACK_STATE == 0:
            print("Pausing playback...")
            sp.pause_playback(device_id=DEVICE_ID)
            PLAYBACK_STATE = 1
        else:
            print("Resuming playback...")
            sp.transfer_playback(device_id=DEVICE_ID, force_play=True)
            PLAYBACK_STATE = 0
        BUTTON_PRESS_TIME = time.time()

GPIO.setwarnings(False) # Ignore warning for now
GPIO.setmode(GPIO.BOARD) # Use physical pin numbering
GPIO.setup(10, GPIO.IN, pull_up_down=GPIO.PUD_DOWN) # Set pin 10 to be an input pin and set initial value to be pulled low (off)
GPIO.add_event_detect(10,GPIO.RISING,callback=button_callback) # Setup event on pin 10 rising edge

def play_music(id, resume):
    uri = "spotify:album:" + str(id)
    try :
        # Transfer playback to the Raspberry Pi if music is playing on a different device
        sp.transfer_playback(device_id=DEVICE_ID, force_play=resume)
        # Play the spotify track at URI with album ID
        sp.start_playback(device_id=DEVICE_ID, context_uri=uri)
        sp.volume(100, device_id=DEVICE_ID)
    except:
        # If exception, reset playback state and resume loop
        print("An exception occurred")
        PLAYBACK_STATE = 1

while True:
    if rc.read(rc.block_num):  # read RFID card data
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
            ALBUM_ID="0fWLW9j35eQTrOb8mHcnyX"
            print("Playing Megadeth on Spotify")
            play_music(ALBUM_ID, False)
        elif s == "1111111111111111":
            ALBUM_ID="38W7WU8kz5SHqcNdx9ZtmC"
            print("Playing Mitski on Spotify")
            play_music(ALBUM_ID, False)
        else:
            print("Error: uknown id...")
