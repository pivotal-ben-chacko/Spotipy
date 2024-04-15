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


