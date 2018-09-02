#!/bin/bash


opkg update
wait
opkg install gcc make automake ca-bundle git git-http nano nmap python3 python3-pip openssl-util curl unzip
wait
export LC_ALL=C
mkdir /opt
mkdir /opt/tmp
mkdir /opt/hue-emulator
pip3 install requests ws4py
wait
cd /opt/tmp
git clone -b OpenWrt git://github.com/juanesf/diyHue.git
wait

cd /opt/tmp/diyHue/BridgeEmulator
cp HueEmulator3.py config.json updater /opt/hue-emulator/
cp -r web-ui /opt/hue-emulator/
cp -r functions debug /opt/hue-emulator/
cp entertainment-mips /opt/hue-emulator/entertainment-srv
wait
cp hueemulator /etc/init.d/


wget -q https://github.com/sffjunkie/astral/archive/master.zip -O astral.zip
wait
unzip -q -o astral.zip
wait
cd astral-master/
python3 setup.py install
wait
cd ../
rm -rf astral.zip astral-master/


mac=`cat /sys/class/net/$(ip route get 8.8.8.8 | sed -n 's/.* dev \([^ ]*\).*/\1/p')/address`
curl https://raw.githubusercontent.com/mariusmotea/diyHue/9ceed19b4211aa85a90fac9ea6d45cfeb746c9dd/BridgeEmulator/openssl.conf -o openssl.conf
wait
serial="${mac:0:2}${mac:3:2}${mac:6:2}fffe${mac:9:2}${mac:12:2}${mac:15:2}"
dec_serial=`python3 -c "print(int(\"$serial\", 16))"`
openssl req -new -config openssl.conf -nodes -x509 -newkey ec -pkeyopt ec_paramgen_curve:P-256 -pkeyopt ec_param_enc:named_curve -subj "/C=NL/O=Philips Hue/CN=$serial" -keyout private.key -out public.crt -set_serial $dec_serial

touch /opt/hue-emulator/cert.pem
cat private.key > /opt/hue-emulator/cert.pem
cat public.crt >> /opt/hue-emulator/cert.pem
rm private.key public.crt



chmod +x /etc/init.d/hueemulator
chmod +x /opt/hue-emulator/HueEmulator3.py
chmod +x /opt/hue-emulator/debug
chmod +x /opt/hue-emulator/updater
chmod +x /opt/hue-emulator/web-ui
chmod +x /opt/hue-emulator/functions
chmod +x /opt/hue-emulator/config.json
chmod +x /opt/hue-emulator/entertainment-srv
/etc/init.d/hueemulator enable
wait
echo -e "\033[32m Installation completed. run: nano /etc/config/uhttpd and mod htpp port 80 for 82, run: nano /etc/lighttpd/lighttpd.conf and mod server.port = 80 for 82. For save changes ctrl +x, y, and enter..\033[0m"
sleep 20s
nano /etc/config/uhttpd
wait
nano /etc/lighttpd/lighttpd.conf
echo -e "\033[32m Installation completed.\033[0m"
rm -Rf /opt/tmp
wait
exit 0













