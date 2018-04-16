

/*
  This can control Generic Power Outlets with Remote Control over 433Mhz.
  Maximum 8 Devices.
  Simulates 2 Remotes with 4 Items each.
  Showing 8 Individual Hue Bulbs
  
  Edit Config as needed
  by Mevel

*/

#include <ESP8266WiFi.h>
#include <ESP8266mDNS.h>
#include <WiFiUdp.h>
#include <ArduinoOTA.h>
#include <ESP8266WebServer.h>
#include <WiFiManager.h>
#include <EEPROM.h>
#include <RCSwitch.h>

RCSwitch mySwitch = RCSwitch();


//############ CONFIG ############

#define devicesCount 8 // 4 or 8 --> Maximum 8
char* houseCodeA = "11110"; //Group A --> Remote Code for Socket 1-4
char* houseCodeB = "11100"; //Group B --> Remote Code for Socket 5-8

//##########END OF CONFIG ##############



uint8_t devicesPins[devicesCount] = {12, 13, 14, 5, 12, 13, 14, 5}; //irrelevant
uint8_t transmitterPin = 4;     // What Pin is the Transmitter conected?
uint8_t transmitterDelay = 100; // Delay between sending commands in ms
uint8_t repeatTransmit = 2; // Number of Transmit attempts
char* deviceId[] = {"10000", "01000", "00100", "00010", "10000", "01000", "00100", "00010"};
int c;




// if you want to setup static ip uncomment these 3 lines and line 72
//IPAddress strip_ip ( 192,  168,   10,  95);
//IPAddress gateway_ip ( 192,  168,   10,   1);
//IPAddress subnet_mask(255, 255, 255,   0);

bool device_state[devicesCount];
byte mac[6];

ESP8266WebServer server(80);

void handleNotFound() {
  String message = "File Not Found\n\n";
  message += "URI: ";
  message += server.uri();
  message += "\nMethod: ";
  message += (server.method() == HTTP_GET) ? "GET" : "POST";
  message += "\nArguments: ";
  message += server.args();
  message += "\n";
  for (uint8_t i = 0; i < server.args(); i++) {
    message += " " + server.argName(i) + ": " + server.arg(i) + "\n";
  }
  server.send(404, "text/plain", message);
}

void SwitchOn433(uint8_t c) {

  for (int x = 0; x < repeatTransmit; x++) {

    if (c <= 3) {
      mySwitch.switchOn(houseCodeA, deviceId[c]);
      delay(transmitterDelay);
    }
    else {
      mySwitch.switchOn(houseCodeB, deviceId[c]);
      delay(transmitterDelay);

    }

  }

}
void SwitchOff433(uint8_t c) {

  for (int x = 0; x < repeatTransmit; x++) {


    if (c <= 3) {
      mySwitch.switchOff(houseCodeA, deviceId[c]);
      delay(transmitterDelay);

    } else {

      mySwitch.switchOff(houseCodeB, deviceId[c]);
      delay(transmitterDelay);
    }

  }
}

void setup() {
  EEPROM.begin(512);
  Serial.begin(115200);
  mySwitch.enableTransmit(transmitterPin);

  for (uint8_t ch = 0; ch < devicesCount; ch++) {
    pinMode(devicesPins[ch], OUTPUT);
  }

  //WiFi.config(strip_ip, gateway_ip, subnet_mask);


  if (EEPROM.read(1) == 1 || (EEPROM.read(1) == 0 && EEPROM.read(0) == 1)) {
    for (uint8_t ch = 0; ch < devicesCount; ch++) {
      digitalWrite(devicesPins[ch], OUTPUT);
    }

  }

  WiFiManager wifiManager;
  wifiManager.autoConnect("New Hue Device");

  WiFi.macAddress(mac);

  // Port defaults to 8266
  // ArduinoOTA.setPort(8266);

  // Hostname defaults to esp8266-[ChipID]
  // ArduinoOTA.setHostname("myesp8266");

  // No authentication by default
  // ArduinoOTA.setPassword((const char *)"123");

  ArduinoOTA.begin();


  server.on("/set", []() {
    uint8_t device;

    for (uint8_t i = 0; i < server.args(); i++) {
      if (server.argName(i) == "light") {
        device = server.arg(i).toInt() - 1;
      }
      else if (server.argName(i) == "on") {
        if (server.arg(i) == "True" || server.arg(i) == "true") {
          if (EEPROM.read(1) == 0 && EEPROM.read(0) != 1) {
            EEPROM.write(0, 1);
            EEPROM.commit();
          }
          device_state[device] = true;
          digitalWrite(devicesPins[device], HIGH);
          SwitchOn433(device);
        }
        else {
          if (EEPROM.read(1) == 0 && EEPROM.read(0) != 0) {
            EEPROM.write(0, 0);
            EEPROM.commit();
          }
          device_state[device] = false;
          digitalWrite(devicesPins[device], LOW);
          SwitchOff433(device);
        }
      }
    }
    server.send(200, "text/plain", "OK, state:" + device_state[device]);
  });

  server.on("/get", []() {
    uint8_t light;
    if (server.hasArg("light"))
      light = server.arg("light").toInt() - 1;
    String power_status;
    power_status = device_state[light] ? "true" : "false";
    server.send(200, "text/plain", "{\"on\": " + power_status + "}");
  });

  server.on("/detect", []() {
    server.send(200, "text/plain", "{\"hue\": \"bulb\",\"lights\": " + String(devicesCount) + ",\"modelid\": \"Plug 01\",\"mac\": \"" + String(mac[5], HEX) + ":"  + String(mac[4], HEX) + ":" + String(mac[3], HEX) + ":" + String(mac[2], HEX) + ":" + String(mac[1], HEX) + ":" + String(mac[0], HEX) + "\"}");
  });

  server.on("/", []() {
    float transitiontime = 100;
    if (server.hasArg("startup")) {
      if (  EEPROM.read(1) != server.arg("startup").toInt()) {
        EEPROM.write(1, server.arg("startup").toInt());
        EEPROM.commit();
      }
    }

    for (uint8_t device = 0; device < devicesCount; device++) {

      if (server.hasArg("on")) {
        if (server.arg("on") == "true") {
          device_state[device] = true;
          digitalWrite(devicesPins[device], HIGH);

          SwitchOn433(device);

          if (EEPROM.read(1) == 0 && EEPROM.read(0) != 1) {
            EEPROM.write(0, 1);
            EEPROM.commit();
          }
        } else {
          device_state[device] = false;
          digitalWrite(devicesPins[device], LOW);
          SwitchOff433(device);
          if (EEPROM.read(1) == 0 && EEPROM.read(0) != 0) {
            EEPROM.write(0, 0);
            EEPROM.commit();
          }
        }
      }
    }
    if (server.hasArg("reset")) {
      ESP.reset();
    }


    String http_content = "<!doctype html>";
    http_content += "<html>";
    http_content += "<head>";
    http_content += "<meta charset=\"utf-8\">";
    http_content += "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">";
    http_content += "<title>Light Setup</title>";
    http_content += "<link rel=\"stylesheet\" href=\"https://unpkg.com/purecss@0.6.2/build/pure-min.css\">";
    http_content += "</head>";
    http_content += "<body>";
    http_content += "<fieldset>";
    http_content += "<h3>Light Setup</h3>";
    http_content += "<form class=\"pure-form pure-form-aligned\" action=\"/\" method=\"post\">";
    http_content += "<div class=\"pure-control-group\">";
    http_content += "<label for=\"power\"><strong>Power</strong></label>";
    http_content += "<a class=\"pure-button"; if (device_state[0]) http_content += "  pure-button-primary"; http_content += "\" href=\"/?on=true\">ON</a>";
    http_content += "<a class=\"pure-button"; if (!device_state[0]) http_content += "  pure-button-primary"; http_content += "\" href=\"/?on=false\">OFF</a>";
    http_content += "</div>";
    http_content += "</fieldset>";
    http_content += "</form>";
    http_content += "</body>";
    http_content += "</html>";

    server.send(200, "text/html", http_content);

  });


  server.onNotFound(handleNotFound);

  server.begin();
}

void loop() {
  ArduinoOTA.handle();
  server.handleClient();
}


