# bunch-profile-monitor
This web-server application is used at Fermilab's IOTA electron storage ring to measure the electron bunch's longitudinal profile and bunch length.

The program talks to an oscilloscope, to which the signal from the wall-current monitor (a device, measuring the bunch profile) is connected. Then, the signal from the scope is processed using FFT to account for transmission characteristics of the cables and the amplifier, located between the wall-current monitor and the oscilloscope. In this way, the initial signal from the wall-current monitor is reconstructed. Finally, RMS and FWHM bunch lengths are calculated based on the reconstructed bunch profile.

## Running the server locally with synthetic data
Tested on Ubuntu 18.04 and Raspbian:
```
sudo apt install python3
sudo apt install python3-pip
pip3 install pandas matplotlib bokeh flask
git clone https://github.com/IharLobach/bunch-profile-monitor.git
cd bunch-profile-monitor
mv config_localhost.json config.json
cd ..
python3 -m bokeh serve bunch-profile-monitor
```
A new tab should open in a browser window.
