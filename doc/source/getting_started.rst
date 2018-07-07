###############
Getting started
###############

To have the Hue Emulator running you will need just the files HueEmulator.py and config.json from BridgeEmulator folder. The file coap-client-linux is compiled for arm devices like raspberry pi and is used for communication with Ikea Tradfri Gateway so you will need it only if you want to control from Hue application(s) the lights paired with your Tradfri Gateway.

Automatic install
#################

just run the following command::

    curl -s https://raw.githubusercontent.com/mariusmotea/diyHue/master/BridgeEmulator/easy_install.sh | sudo bash /dev/stdin


Manual install
##############

* Download or clone the mirror with git (recommended)::

    git clone https://github.com/mariusmotea/diyHue.git

* Install nmap package for lights autodiscover ``sudo apt install nmap``.  On windows nmap utility is missing and the lights must be added manually in configuration witch is not simple.

* Create startup systemd file based on the following example::

    sudo nano /lib/systemd/system/hue-emulator.service

  paste the following code and edit the path of the emulator script::

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

  save and execute the following commands::

    sudo chmod 644 /lib/systemd/system/hue-emulator.service
    sudo systemctl daemon-reload
    sudo systemctl enable hue-emulator.service 
    sudo systemctl start hue-emulator.service

  if you want to disable logging to syslog you must add in systemd file ``StandardOutput=null``.
  You can check the service status with ``sudo systemctl status hue-emulator.service``.

link button
###########

Go to http://{IP_ADRESS}/hue/linkbutton when you want to allow new device on hue emulator.
Default username: Hue password: Hue

Config file
###########

Entire configuration is saved in config.json file.
Changes in bridge are saved in real time if new object is created or every hour automatically.
In case of state change of lights or sensors the configuration is not saved to avoid extensive writes to sd card.
If you want to save the configuration manually you can do it by accessing ``http://{emualtor ip}/save``.
If you want to manually edit the configuration file to change any king of resource i recommend to backup the file first.
In case the configuration file is corrupted you can look for backups that are done automatically every Sunday night.
