#!/bin/bash

echo -e "\033[36m Migrating Existing diyHue Install\033[0m"

OLD="http://raw.githubusercontent.com/mariusmotea/diyHue/master/BridgeEmulator/updater"
NEW="http://raw.githubusercontent.com/diyhue/diyHue/master/BridgeEmulator/updater"
sed -i "s#$OLD#$NEW#g" "HueEmulator3.py"
echo -e "\033[36m Existing Install Migrated Successfully\033[0m"

echo -e "\033[36m Checking if git was used."

if [[ -d "./.git" ]]; then
    echo -e "\033[36m Git Found, Updating\033[0m"
    git remote set-url origin https://github.com/diyhue/diyHue.git
    rm -rf ./Lights/
    git clone https://github.com/diyhue/Lights.git
    rm -rf ./Sensors/
    git clone https://github.com/diyhue/Devices.git
fi
