cd /opt/hue-emulator
OLD="http://raw.githubusercontent.com/mariusmotea/diyHue/master/BridgeEmulator/updater"
NEW="http://raw.githubusercontent.com/diyhue/diyHue/master/BridgeEmulator/updater"
sed -i "s#$OLD#$NEW#g" "HueEmulator3.py"
