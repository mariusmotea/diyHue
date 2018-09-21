Getting Started
===============

Setup is very quick and easy with two installation methods currently supported. diyHue can be installed eaither directly on the host machine, or via a docker image. Please note that although running diyHue on Windows is theoretically possible, many scripts and functions rely on Linux commands. As such, using Windows is not recommended!

It is best to have at least one compatible light ready in order to setup and test the system with.

Host Install
------------

When installing diyHue directly on the host, you have two installation methods available. An easy automatic installation script or the commands to install it manually. The automatic install is highly recommended and is kept most up to date.

Automatic Install
~~~~~~~~~~~~~~~~~

Just run the following command::

    curl -s https://raw.githubusercontent.com/mariusmotea/diyHue/master/BridgeEmulator/easy_install.sh | sudo bash /dev/stdin

Once complete, diyHue is installed and running. It will also automatically start on boot. diyHue can also be stopped, started and restarted with the following command::

    sudo systemctl [start/stop/restart] hue-emulator.service

Manual install
~~~~~~~~~~~~~~

* Download or clone the mirror with git (recommended)::

    git clone https://github.com/mariusmotea/diyHue.git

* Install the nmap package for light autodiscovery ``sudo apt install nmap``.  On windows the nmap utility is missing and the lights must be added manually in configuration.

* Create a startup systemd file based on the following example::

    sudo nano /lib/systemd/system/hue-emulator.service

* Paste the following code and edit the path of the emulator script::

    [Unit]
    Description=Hue Emulator Service
    After=multi-user.target

    [Service]
    Type=idle
    Restart=always
    RestartSec=30
    StartLimitInterval=200
    StartLimitBurst=5

    WorkingDirectory=/home/pi
    ExecStart=/home/pi/HueEmulator.py

    [Install]
    WantedBy=multi-user.target

* Save and execute the following commands::

    sudo chmod 644 /lib/systemd/system/hue-emulator.service
    sudo systemctl daemon-reload
    sudo systemctl enable hue-emulator.service
    sudo systemctl start hue-emulator.service

If you want to disable logging to syslog, you must add the following to the systemd file ``StandardOutput=null``
You can check the service status with ``sudo systemctl status hue-emulator.service``

Docker Install
--------------

There are currently two docker images available. One for x86 systems and one for ARM systems (Raspberry Pi). Currently the ARM image has only been tested with a Raspberry Pi 3b+ If you have other ARM based devices and can test the image, please let us know on our Slack chat or in an issue. The images can be run with both host and bridge network modes. I recomend using the host network mode for ease, however this will give you less controll over your docker networks. Using bridge mode allows you to controll the traffic in and out of the container but requires more options to setup.

To run the container with the host network mode:

x86::

    docker run -d --name "diyHue" --network="host" -v '/mnt/hue-emulator/export/':'/opt/hue-emulator/export/':'rw' diyhue/core:amd64

ARM::

    docker run -d --name "diyHue" --network="host" -v '/mnt/hue-emulator/export/':'/opt/hue-emulator/export/':'rw' diyhue/core:armhf

When running with the bridge network mode you must provide the IP and MAC address of the host device. Four ports are also opened to the container. These port mappings must not be changed as the hue ecosystem expects to communicate over specific ports.

To run the container with bridge network mode:

x86::

    docker run -d --name "diyHue" --network="bridge" -v '/mnt/hue-emulator/export/':'/opt/hue-emulator/export/':'rw' -e 'MAC=XX:XX:XX:XX:XX:XX' -e 'IP=XX.XX.XX.XX' -p 80:80/tcp -p 443:443/tcp -p 1900:1900/udp -p 2100:2100/udp diyhue/core:amd64

ARM::

    docker run -d --name "diyHue" --network="bridge" -v '/mnt/hue-emulator/export/':'/opt/hue-emulator/export/':'rw' -e 'MAC=XX:XX:XX:XX:XX:XX' -e 'IP=XX.XX.XX.XX' -p 80:80/tcp -p 443:443/tcp -p 1900:1900/udp -p 2100:2100/udp diyhue/core:armhf

These commands will run the latest image available, however if you have automated updates enabled with a service such as watchtower then using latest is not recomended. The images are automatically rebuilt upon a new commit to this repo. As such, larges changes could occur and updates will be frequent. Each image is also taged with the comit hash. For example ``diyhue/core:armhf-391cc642072aac70d544fd428864f74bf9eaf636`` or ``diyhue/core:amd64-391cc642072aac70d544fd428864f74bf9eaf636`` It is then suggested you use one of these images instead and manually update every so often.

The mount directory /mnt/hue-emulator/export/ can be changed to any directory you wish. Backups of the config.json and cert.pem are saved here when changes are made to these files. They are then restored upon container reboot. If you need to make manual changes to these files, do so with the files mounted on the host (rather than the files in the container) and then restart the container to import your changes. To perform a manual export at any time, visit ``http://{emualtor ip}/save`` If there are no files in the mounted directory then they will be regenerated at container start.