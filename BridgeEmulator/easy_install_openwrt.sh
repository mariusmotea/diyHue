#!/bin/bash

opkg update
sleep 60s
opkg install git git-http nano nmap python3 python3-pip
sleep 60s
export LC_ALL=C
mkdir /opt
mkdir /opt/hue-emulator
pip3 install requests
sleep 120s
cd /tmp
git clone -b OpenWrt git://github.com/juanesf/diyHue.git
sleep 200s
cd /tmp/diyHue/BridgeEmulator
cp  HueEmulator3.py config.json updater coap-client-linux /opt/hue-emulator/
sleep 3s
cp hueemulator /etc/init.d/
sleep 2s
chmod +x /etc/init.d/hueemulator
chmod +x /opt/hue-emulator/HueEmulator3.py
chmod +x /opt/hue-emulator/coap-client-linux
chmod +x /opt/hue-emulator/updater
/etc/init.d/hueemulator enable
sleep 1s
echo -e "\033[32m Installation completed. Open Hue app and search for bridges.\033[0m"

exit 0
