
opkg update
wait
opkg install wget ca-bundle
wait
cd /tmp
wget --no-check-certificate https://raw.githubusercontent.com/juanesf/diyHue/OpenWrt/BridgeEmulator/openwrt.sh
sh openwrt.sh
wait
exit 0
