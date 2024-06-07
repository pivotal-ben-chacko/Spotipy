# Spotipy
Raspberry Pi based music streaming jukebox

Setup: 

1. Install Rasberry pi software 32 bit

2. sudo apt update

3. sudo apt upgrade

4. sudo pip3 install spidev

5. sudo pip3 install wiringpi

6. sudo pip install spotipy


Install Raspotipy 

curl -sL https://dtcooper.github.io/raspotify/install.sh | sh

Register device with Spotify by playing to device on the Spotify App and record the device ID given to the Raspberry Pi

Update Device ID in src/spotify.py



# RC522 RFID HAT

![RC522 RFID HAT](https://seengreat.com/upload/wiki/202312/07/17019373674916129220.jpg)

## Overview

The RC522 RFID HAT is a module designed for Raspberry Pi application in RFID scenarios, which is used for contact-less communication at 13.56MHz. It also supports I2C, SPI and UART serial port communication, and the communication interface can be set by the on-board DIP switch.

## Specifications

-   Power Supply 3.3V / 5V ● Supports ISO/IEC14443A/MIFARE
-   Supports MIFARE Classic encryption in reader/writer model
-   Supports interfaces of SPI/I2C/UART
-   Running at 13.56MHz
-   Dimensions: 85mm(Length) x 56.3mm(Width)
