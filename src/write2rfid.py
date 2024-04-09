# Spotify RFID Jukebox
#
# Author: Ben Chacko, 2024
# Description: Helper script to write desired ID to MIFARE card
#
#
# Usage: $ > python3 write2rfid.py <DESIRED-ID>
#
# Hardware: RC522 RFID HAT
#             - https://seengreat.com/wiki/90/rc522-rfid-hat
#           Raspberry Pi 3 Model B+
#             - https://www.raspberrypi.com/products/raspberry-pi-3-model-b-plus/

import module
import sys
import time
import wiringpi

rc = module.Rc522_api()
rc.init()
wiringpi.softPwmCreate(24,0,8)

id = sys.argv[1]

def play_buzzer():
    wiringpi.digitalWrite(29,0)  # turn on red led
    wiringpi.softPwmWrite(24, 5)
    time.sleep(0.2)
    wiringpi.digitalWrite(29,1)  # turn off red led
    wiringpi.softPwmWrite(24,0)  # turn off buzzer
    time.sleep(0.3)

if (len(id) != 16) or (not id.isdigit()):
    print("Error: ID must be numerical and exactly 16 characters in length!")
    exit(1)

print("Ready to write to RFID card...")
while True:
    if rc.write(rc.block_num, id): # attempt to write to MIFARE card
        play_buzzer()
        print("Success: " + str(id) + " saved to card")
        break
