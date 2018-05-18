Works perfectly in GL-MT300A with /overlay in microSD.

For easy install run:
sh easy_install_openwrt.sh


For manual install:
mkdir /opt

mkdir /opt/hue-emulator


opkg update

opkg install nano nmap python3-pip

pip3 install requests


After edit the following lines in /etc/config/uhttpd:

nano /etc/config/uhttpd

list listen_http '0.0.0.0:80'

list listen_http '[::]:80'

with:

list listen_http '0.0.0.0:82'

list listen_http '[::]:82'


deploy files:
- HueEmulator3.py
- config.json
- updater
- coap-client-linux

on: /opt/hue-emulator/


deploy file:

-hueemulator

on: /etc/init.d/


chmod +x /etc/init.d/hueemulator

chmod +x /opt/hue-emulator/HueEmulator3.py

chmod +x /opt/hue-emulator/coap-client-linux

chmod +x /opt/hue-emulator/updater


/etc/init.d/hueemulator enable

reboot 00
