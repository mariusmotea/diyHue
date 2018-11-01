FROM debian:buster

RUN apt-get update && apt-get upgrade -y && apt-get install -y python3.6 python3-pip libyaml-dev

RUN pip3 install click-datetime
RUN mkdir /huebridgeemulator
WORKDIR /huebridgeemulator
#RUN apt-get update && apt-get install -y python3-six

COPY setup.py /huebridgeemulator
COPY huebridgeemulator /huebridgeemulator/huebridgeemulator
COPY LICENSE.txt test_requirements.txt requirements.txt /huebridgeemulator/

#RUN pip3 install pip --upgrade --force
#RUN pip3 install -r requirements.txt
#RUN pip3 install six --upgrade --force
RUN python3 setup.py install

ENTRYPOINT ["huebridgeemulator"]
CMD ["-c", "/config.json", "-l", "INFO"]
