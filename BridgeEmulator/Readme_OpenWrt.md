Works perfectly in GL-MT300A with /overlay in microSD


Before edit the following lines in /etc/config/uhttpd:
nano /etc/config/uhttpd

list listen_http '0.0.0.0:80'
list listen_http '[::]:80'

with:

list listen_http '0.0.0.0:82'
list listen_http '[::]:82'

But also edit the line "server.port = 80" for: "server.port = 82" on /etc/lighttpd/lighttpd.conf:
nano /etc/lighttpd/lighttpd.conf

After run:

opkg update
wait
opkg install wget ca-bundle
wait
cd /tmp
wget https://raw.githubusercontent.com/juanesf/diyHue/OpenWrt/BridgeEmulator/easy_install_openwrt.sh
sh easy_install_openwrt.sh
wait
exit 0