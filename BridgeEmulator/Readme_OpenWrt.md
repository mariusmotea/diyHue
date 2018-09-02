
opkg update
wait
opkg install wget ca-bundle
wait
cd /tmp
wget --no-check-certificate https://raw.githubusercontent.com/juanesf/diyHue/OpenWrt/BridgeEmulator/easy_install_openwrt.sh
sh easy_install_openwrt.sh
wait
exit 0