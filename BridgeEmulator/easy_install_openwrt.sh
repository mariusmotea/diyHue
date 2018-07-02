#!/bin/bash


opkg update

wait

opkg install git git-http nano nmap python3 python3-pip

wait

export LC_ALL=C

mkdir /opt

mkdir /opt/hue-emulator

pip3 install requests ws4py

wait

cd /tmp

git clone -b OpenWrt git://github.com/juanesf/diyHue.git

wait

cd /tmp/diyHue/BridgeEmulator

cp HueEmulator3.py config.json updater coap-client-linux cert.pem /opt/hue-emulator/

cp -r web-ui /opt/hue-emulator/

cp -r functions /opt/hue-emulator/

wait

cp hueemulator /etc/init.d/

wait

chmod +x /etc/init.d/hueemulator

chmod +x /opt/hue-emulator/HueEmulator3.py

chmod +x /opt/hue-emulator/coap-client-linux

chmod +x /opt/hue-emulator/updater

chmod +x /opt/hue-emulator/web-ui

chmod +x /opt/hue-emulator/functions

chmod +x /opt/hue-emulator/config.json

/etc/init.d/hueemulator enable

wait


echo -e "\033[32m Installation completed. run: nano /etc/config/uhttpd and mod htpp port 80 for 82, run: nano /etc/lighttpd/lighttpd.conf and mod server.port = 80 for 82. For save changes ctrl +x, y, and enter..\033[0m"
sleep 20s
nano /etc/config/uhttpd
wait
nano /etc/lighttpd/lighttpd.conf

echo -e "\033[32m Installation completed.\033[0m"

exit 0



