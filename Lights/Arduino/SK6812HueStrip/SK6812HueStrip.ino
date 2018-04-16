#include <ESP8266WiFi.h>
#include <ESP8266mDNS.h>
#include <WiFiUdp.h>
#include <ArduinoOTA.h>
#include <ESP8266WebServer.h>
#include <NeoPixelBus.h>
#include <WiFiManager.h>
#include <EEPROM.h>

#define lightsCount 3
#define pixelCount 60

#define use_hardware_switch false // To control on/off state and brightness using GPIO/Pushbutton, set this value to true.
//For GPIO based on/off and brightness control, it is mandatory to connect the following GPIO pins to ground using 10k resistor
#define button1_pin 4 // on and brightness up
#define button2_pin 5 // off and brightness down

// if you want to setup static ip uncomment these 3 lines and line 72
//IPAddress strip_ip ( 192,  168,   10,  95);
//IPAddress gateway_ip ( 192,  168,   10,   1);
//IPAddress subnet_mask(255, 255, 255,   0);

uint8_t rgbw[lightsCount][4], color_mode[lightsCount], scene;
bool light_state[lightsCount], in_transition;
int transitiontime[lightsCount], ct[lightsCount], hue[lightsCount], bri[lightsCount], sat[lightsCount];
float step_level[lightsCount][4], current_rgbw[lightsCount][4], x[lightsCount], y[lightsCount];
byte mac[6];

ESP8266WebServer server(80);

RgbwColor red = RgbwColor(255, 0, 0, 0);
RgbwColor green = RgbwColor(0, 255, 0, 0);
RgbwColor white = RgbwColor(255);
RgbwColor black = RgbwColor(0);

NeoPixelBus<NeoGrbwFeature, Neo800KbpsMethod> strip(pixelCount);

void convert_hue(uint8_t light)
{
  double      hh, p, q, t, ff, s, v;
  long        i;

  rgbw[light][3] = 0;
  s = sat[light] / 255.0;
  v = bri[light] / 255.0;

  if (s <= 0.0) {      // < is bogus, just shuts up warnings
    rgbw[light][0] = v;
    rgbw[light][1] = v;
    rgbw[light][2] = v;
    return;
  }
  hh = hue[light];
  if (hh >= 65535.0) hh = 0.0;
  hh /= 11850, 0;
  i = (long)hh;
  ff = hh - i;
  p = v * (1.0 - s);
  q = v * (1.0 - (s * ff));
  t = v * (1.0 - (s * (1.0 - ff)));

  switch (i) {
    case 0:
      rgbw[light][0] = v * 255.0;
      rgbw[light][1] = t * 255.0;
      rgbw[light][2] = p * 255.0;
      break;
    case 1:
      rgbw[light][0] = q * 255.0;
      rgbw[light][1] = v * 255.0;
      rgbw[light][2] = p * 255.0;
      break;
    case 2:
      rgbw[light][0] = p * 255.0;
      rgbw[light][1] = v * 255.0;
      rgbw[light][2] = t * 255.0;
      break;

    case 3:
      rgbw[light][0] = p * 255.0;
      rgbw[light][1] = q * 255.0;
      rgbw[light][2] = v * 255.0;
      break;
    case 4:
      rgbw[light][0] = t * 255.0;
      rgbw[light][1] = p * 255.0;
      rgbw[light][2] = v * 255.0;
      break;
    case 5:
    default:
      rgbw[light][0] = v * 255.0;
      rgbw[light][1] = p * 255.0;
      rgbw[light][2] = q * 255.0;
      break;
  }

}

void convert_xy(uint8_t light)
{
  float Y = y[light];
  float X = x[light];
  float Z = 1.0f - x[light] - y[light];

  // sRGB D65 conversion
  float r =  X * 3.2406f - Y * 1.5372f - Z * 0.4986f;
  float g = -X * 0.9689f + Y * 1.8758f + Z * 0.0415f;
  float b =  X * 0.0557f - Y * 0.2040f + Z * 1.0570f;

  // Apply gamma correction
  r = r <= 0.0031308f ? 12.92f * r : (1.0f + 0.055f) * pow(r, (1.0f / 2.4f)) - 0.055f;
  g = g <= 0.0031308f ? 12.92f * g : (1.0f + 0.055f) * pow(g, (1.0f / 2.4f)) - 0.055f;
  b = b <= 0.0031308f ? 12.92f * b : (1.0f + 0.055f) * pow(b, (1.0f / 2.4f)) - 0.055f;

  if (r > b && r > g) {
    // red is biggest
    if (r > 1.0f) {
      g = g / r;
      b = b / r;
      r = 1.0f;
    }
  }
  else if (g > b && g > r) {
    // green is biggest
    if (g > 1.0f) {
      r = r / g;
      b = b / g;
      g = 1.0f;
    }
  }
  else if (b > r && b > g) {
    // blue is biggest
    if (b > 1.0f) {
      r = r / b;
      g = g / b;
      b = 1.0f;
    }
  }

  r = r < 0 ? 0 : r;
  g = g < 0 ? 0 : g;
  b = b < 0 ? 0 : b;

  rgbw[light][0] = (int) (r * bri[light]); rgbw[light][1] = (int) (g * bri[light]); rgbw[light][2] = (int) (b * bri[light]); rgbw[light][3] = 0;
}

void convert_ct(uint8_t light) {
  int hectemp = 10000 / ct[light];
  int r, g, b;
  if (hectemp <= 66) {
    r = 255;
    g = 99.4708025861 * log(hectemp) - 161.1195681661;
    b = hectemp <= 19 ? 0 : (138.5177312231 * log(hectemp - 10) - 305.0447927307);
  } else {
    r = 329.698727446 * pow(hectemp - 60, -0.1332047592);
    g = 288.1221695283 * pow(hectemp - 60, -0.0755148492);
    b = 255;
  }
  r = r > 255 ? 255 : r;
  g = g > 255 ? 255 : g;
  b = b > 255 ? 255 : b;
  rgbw[light][0] = r * (bri[light] / 255.0f); rgbw[light][1] = g * (bri[light] / 255.0f); rgbw[light][2] = b * (bri[light] / 255.0f); rgbw[light][3] = bri[light];
}

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

void infoLight(RgbwColor color) {
  // Flash the strip in the selected color. White = booted, green = WLAN connected, red = WLAN could not connect
  for (int i = 0; i < pixelCount; i++)
  {
    strip.SetPixelColor(i, color);
    strip.Show();
    delay(10);
    strip.SetPixelColor(i, black);
    strip.Show();
  }
}


void apply_scene(uint8_t new_scene, uint8_t light) {
  if ( new_scene == 0) {
    bri[light] = 144; ct[light] = 447; color_mode[light] = 2; convert_ct(light);
  } else if ( new_scene == 1) {
    bri[light] = 254; ct[light] = 346; color_mode[light] = 2; convert_ct(light);
  } else if ( new_scene == 2) {
    bri[light] = 254; ct[light] = 233; color_mode[light] = 2; convert_ct(light);
  }  else if ( new_scene == 3) {
    bri[light] = 254; ct[light] = 156; color_mode[light] = 2; convert_ct(light);
  }  else if ( new_scene == 4) {
    bri[light] = 77; ct[light] = 367; color_mode[light] = 2; convert_ct(light);
  }  else if ( new_scene == 5) {
    bri[light] = 254; ct[light] = 447; color_mode[light] = 2; convert_ct(light);
  }  else if ( new_scene == 6) {
    bri[light] = 1; x[light] = 0.561; y[light] = 0.4042; color_mode[light] = 1; convert_xy(light);
  }  else if ( new_scene == 7) {
    bri[light] = 203; x[light] = 0.380328; y[light] = 0.39986; color_mode[light] = 1; convert_xy(light);
  }  else if ( new_scene == 8) {
    bri[light] = 112; x[light] = 0.359168; y[light] = 0.28807; color_mode[light] = 1; convert_xy(light);
  }  else if ( new_scene == 9) {
    bri[light] = 142; x[light] = 0.267102; y[light] = 0.23755; color_mode[light] = 1; convert_xy(light);
  }  else if ( new_scene == 10) {
    bri[light] = 216; x [light] = 0.393209; y[light] = 0.29961; color_mode[light] = 1; convert_xy(light);
  }
}

void process_lightdata(uint8_t light,float transitiontime) {
  transitiontime *= 16 - (pixelCount / 40); //every extra led add a small delay that need to be counted
  if (color_mode[light] == 1 && light_state[light] == true) {
    convert_xy(light);
  } else if (color_mode[light] == 2 && light_state[light] == true) {
    convert_ct(light);
  } else if (color_mode[light] == 3 && light_state[light] == true) {
    convert_hue(light);
  }
  for (uint8_t i = 0; i <= 3; i++) {
    if (light_state[light]) {
      step_level[light][i] = ((float)rgbw[light][i] - current_rgbw[light][i]) / transitiontime;
    } else {
      step_level[light][i] = current_rgbw[light][i] / transitiontime;
    }
  }
}

void lightEngine() {
  for (int i = 0; i < lightsCount; i++) {
    if (light_state[i]) {
      if (rgbw[i][0] != current_rgbw[i][0] || rgbw[i][1] != current_rgbw[i][1] || rgbw[i][2] != current_rgbw[i][2] || rgbw[i][3] != current_rgbw[i][3]) {
        in_transition = true;
        for (uint8_t k = 0; k <= 3; k++) {
          if (rgbw[i][k] != current_rgbw[i][k]) current_rgbw[i][k] += step_level[i][k];
          if ((step_level[i][k] > 0.0 && current_rgbw[i][k] > rgbw[i][k]) || (step_level[i][k] < 0.0 && current_rgbw[i][k] < rgbw[i][k])) current_rgbw[i][k] = rgbw[i][k];
        }
        for (int j = 0; j < pixelCount / lightsCount ; j++)
        {
          strip.SetPixelColor(j + i * pixelCount / lightsCount, RgbwColor((int)current_rgbw[i][0], (int)current_rgbw[i][1], (int)current_rgbw[i][2], (int)current_rgbw[i][3]));
        }
        strip.Show();
      }
    } else {
      if (current_rgbw[i][0] != 0 || current_rgbw[i][1] != 0 || current_rgbw[i][2] != 0 || current_rgbw[i][3] != 0) {
        in_transition = true;
        for (uint8_t k = 0; k <= 3; k++) {
          if (current_rgbw[i][k] != 0) current_rgbw[i][k] -= step_level[i][k];
          if (current_rgbw[i][k] < 0) current_rgbw[i][k] = 0;
        }
        for (int j = 0; j < pixelCount / lightsCount ; j++)
        {
          strip.SetPixelColor(j + i * pixelCount / lightsCount, RgbwColor((int)current_rgbw[i][0], (int)current_rgbw[i][1], (int)current_rgbw[i][2], (int)current_rgbw[i][3]));
        }
        strip.Show();
      }
    }
  }
  if (in_transition) {
    delay(6);
    in_transition = false;
  } else if (use_hardware_switch == true) {
    if (digitalRead(button1_pin) == HIGH) {
      int i = 0;
      while (digitalRead(button1_pin) == HIGH && i < 30) {
        delay(20);
        i++;
      }
      for (int light = 0; light < lightsCount; light++) {
        if (i < 30) {
          // there was a short press
          light_state[light] = true;
        }
        else {
          // there was a long press
          bri[light] += 56;
          if (bri[light] > 254) {
            // don't increase the brightness more then maximum value
            bri[light] = 254;
          }
        }
        process_lightdata(light,4);
      }
    } else if (digitalRead(button2_pin) == HIGH) {
      int i = 0;
      while (digitalRead(button2_pin) == HIGH && i < 30) {
        delay(20);
        i++;
      }
      for (int light = 0; light < lightsCount; light++) {
        if (i < 30) {
          // there was a short press
          light_state[light] = false;
        }
        else {
          // there was a long press
          bri[light] -= 56;
          if (bri[light] < 1) {
            // don't decrease the brightness less than minimum value.
            bri[light] = 1;
          }
        }
        process_lightdata(light,4);
      }
    }
  }
}

void setup() {
  strip.Begin();
  strip.Show();
  EEPROM.begin(512);

  //WiFi.config(strip_ip, gateway_ip, subnet_mask);

  for (uint8_t light = 0; light < lightsCount; light++) {
    float transitiontime = (16 - (pixelCount / 40)) * 4;
    apply_scene(EEPROM.read(2), light);
    for (uint8_t j = 0; j < 4; j++) {
      step_level[light][j] = ((float)rgbw[light][j] - current_rgbw[light][j]) / transitiontime;
    }
  }

  if (EEPROM.read(1) == 1 || (EEPROM.read(1) == 0 && EEPROM.read(0) == 1)) {
    for (int i = 0; i < lightsCount; i++) {
      light_state[i] = true;
    }
    for (int j = 0; j < 200; j++) {
      lightEngine();
    }
  }
  WiFiManager wifiManager;
  wifiManager.autoConnect("New Hue Light");

  if (! light_state[0]) {
    infoLight(white);
    while (WiFi.status() != WL_CONNECTED) {
      infoLight(red);
      delay(500);
    }
    // Show that we are connected
    infoLight(green);

  }

  WiFi.macAddress(mac);

  // Port defaults to 8266
  // ArduinoOTA.setPort(8266);

  // Hostname defaults to esp8266-[ChipID]
  // ArduinoOTA.setHostname("myesp8266");

  // No authentication by default
  // ArduinoOTA.setPassword((const char *)"123");

  ArduinoOTA.begin();

  pinMode(LED_BUILTIN, OUTPUT);     // Initialize the LED_BUILTIN pin as an output
  digitalWrite(LED_BUILTIN, HIGH);  // Turn the LED off by making the voltage HIGH
  pinMode(button1_pin, INPUT);
  pinMode(button2_pin, INPUT);

  server.on("/switch", []() {
    server.send(200, "text/plain", "OK");
    float transitiontime = (16 - (pixelCount / 40)) * 4;
    int button;
    for (uint8_t i = 0; i < server.args(); i++) {
      if (server.argName(i) == "button") {
        button = server.arg(i).toInt();
      }
    }
    for (int i = 0; i < lightsCount; i++) {
      if (button == 1000) {
        if (light_state[i] == false) {
          light_state[i] = true;
          scene = 0;
        } else {
          apply_scene(scene, i);
          scene++;
          if (scene == 11) {
            scene = 0;
          }
        }
      } else if (button == 2000) {
        if (light_state[i] == false) {
          bri[i] = 30;
          light_state[i] = true;
        } else {
          bri[i] += 30;
        }
        if (bri[i] > 255) bri[i] = 255;
        if (color_mode[i] == 1) convert_xy(i);
        else if (color_mode[i] == 2) convert_ct(i);
        else if (color_mode[i] == 3) convert_hue(i);
      } else if (button == 3000 && light_state[i] == true) {
        bri[i] -= 30;
        if (bri[i] < 1) bri[i] = 1;
        else {
          if (color_mode[i] == 1) convert_xy(i);
          else if (color_mode[i] == 2) convert_ct(i);
          else if (color_mode[i] == 3) convert_hue(i);
        }
      } else if (button == 4000) {
        light_state[i] = false;
      }
      for (uint8_t j = 0; j <= 3; j++) {
        if (light_state[i]) {
          step_level[i][j] = ((float)rgbw[i][j] - current_rgbw[i][j]) / transitiontime;
        } else {
          step_level[i][j] = current_rgbw[i][j] / transitiontime;
        }
      }
    }
  });

  server.on("/set", []() {
    uint8_t light;
    int transitiontime = 4;
    for (uint8_t i = 0; i < server.args(); i++) {
      if (server.argName(i) == "light") {
        light = server.arg(i).toInt() - 1;
      }
      else if (server.argName(i) == "on") {
        if (server.arg(i) == "True" || server.arg(i) == "true") {
          light_state[light] = true;
          if (EEPROM.read(1) == 0 && EEPROM.read(0) == 0) {
            EEPROM.write(0, 1);
          }
        }
        else {
          light_state[light] = false;
          if (EEPROM.read(1) == 0 && EEPROM.read(0) == 1) {
            EEPROM.write(0, 0);
          }
        }
        EEPROM.commit();
      }
      else if (server.argName(i) == "r") {
        rgbw[light][0] = server.arg(i).toInt();
        color_mode[light] = 0;
      }
      else if (server.argName(i) == "g") {
        rgbw[light][1] = server.arg(i).toInt();
        color_mode[light] = 0;
      }
      else if (server.argName(i) == "b") {
        rgbw[light][2] = server.arg(i).toInt();
        color_mode[light] = 0;
      }
      else if (server.argName(i) == "w") {
        rgbw[light][3] = server.arg(i).toInt();
        color_mode[light] = 0;
      }
      else if (server.argName(i) == "x") {
        x[light] = server.arg(i).toFloat();
        color_mode[light] = 1;
      }
      else if (server.argName(i) == "y") {
        y[light] = server.arg(i).toFloat();
        color_mode[light] = 1;
      }
      else if (server.argName(i) == "bri") {
        light_state[light] = true;
        if (server.arg(i).toInt() != 0)
          bri[light] = server.arg(i).toInt();
      }
      else if (server.argName(i) == "bri_inc") {
        bri[light] += server.arg(i).toInt();
        if (bri[light] > 255) bri[light] = 255;
        else if (bri[light] < 0) bri[light] = 0;
      }
      else if (server.argName(i) == "ct") {
        ct[light] = server.arg(i).toInt();
        color_mode[light] = 2;
      }
      else if (server.argName(i) == "sat") {
        sat[light] = server.arg(i).toInt();
        color_mode[light] = 3;
      }
      else if (server.argName(i) == "hue") {
        hue[light] = server.arg(i).toInt();
        color_mode[light] = 3;
      }
      else if (server.argName(i) == "alert" && server.arg(i) == "select") {
        if (light_state[light]) {
          current_rgbw[light][0] = 0; current_rgbw[light][1] = 0; current_rgbw[light][2] = 0; current_rgbw[light][3] = 0;
        } else {
          current_rgbw[light][3] = 255;
        }
      }
      else if (server.argName(i) == "transitiontime") {
        transitiontime = server.arg(i).toInt();
      }
    }
    process_lightdata(light, transitiontime);
    server.send(200, "text/plain", "OK, x: " + (String)x[light] + ", y:" + (String)y[light] + ", bri:" + (String)bri[light] + ", ct:" + ct[light] + ", colormode:" + color_mode[light] + ", state:" + light_state[light]);
  });

  server.on("/get", []() {
    uint8_t light;
    if (server.hasArg("light"))
      light = server.arg("light").toInt() - 1;
    String colormode;
    String power_status;
    power_status = light_state[light] ? "true" : "false";
    if (color_mode[light] == 1)
      colormode = "xy";
    else if (color_mode[light] == 2)
      colormode = "ct";
    else if (color_mode[light] == 3)
      colormode = "hs";
    server.send(200, "text/plain", "{\"on\": " + power_status + ", \"bri\": " + (String)bri[light] + ", \"xy\": [" + (String)x[light] + ", " + (String)y[light] + "], \"ct\":" + (String)ct[light] + ", \"sat\": " + (String)sat[light] + ", \"hue\": " + (String)hue[light] + ", \"colormode\": \"" + colormode + "\"}");
  });

  server.on("/detect", []() {
    server.send(200, "text/plain", "{\"hue\": \"strip\",\"lights\": " + (String)lightsCount + ",\"modelid\": \"LST001\",\"mac\": \"" + String(mac[5], HEX) + ":"  + String(mac[4], HEX) + ":" + String(mac[3], HEX) + ":" + String(mac[2], HEX) + ":" + String(mac[1], HEX) + ":" + String(mac[0], HEX) + "\"}");
  });

  server.on("/", []() {
    float transitiontime = (16 - (pixelCount / 40)) * 4;
    if (server.hasArg("startup")) {
      if (  EEPROM.read(1) != server.arg("startup").toInt()) {
        EEPROM.write(1, server.arg("startup").toInt());
        EEPROM.commit();
      }
    }

    for (int light = 0; light < lightsCount; light++) {
      if (server.hasArg("scene")) {
        if (server.arg("bri") == "" && server.arg("hue") == "" && server.arg("ct") == "" && server.arg("sat") == "") {
          if (  EEPROM.read(2) != server.arg("scene").toInt()) {
            EEPROM.write(2, server.arg("scene").toInt());
            EEPROM.commit();
          }
          apply_scene(server.arg("scene").toInt(), light);
        } else {
          if (server.arg("bri") != "") {
            bri[light] = server.arg("bri").toInt();
          }
          if (server.arg("hue") != "") {
            hue[light] = server.arg("hue").toInt();
          }
          if (server.arg("sat") != "") {
            sat[light] = server.arg("sat").toInt();
          }
          if (server.arg("ct") != "") {
            ct[light] = server.arg("ct").toInt();
          }
          if (server.arg("colormode") == "1" && light_state[light] == true) {
            convert_xy(light);
          } else if (server.arg("colormode") == "2" && light_state[light] == true) {
            convert_ct(light);
          } else if (server.arg("colormode") == "3" && light_state[light] == true) {
            convert_hue(light);
          }
          color_mode[light] = server.arg("colormode").toInt();
        }
      } else if (server.hasArg("on")) {
        if (server.arg("on") == "true") {
          light_state[light] = true; {
            if (EEPROM.read(1) == 0 && EEPROM.read(0) == 0) {
              EEPROM.write(0, 1);
            }
          }
        } else {
          light_state[light] = false;
          if (EEPROM.read(1) == 0 && EEPROM.read(0) == 1) {
            EEPROM.write(0, 0);
          }
        }
        EEPROM.commit();
      } else if (server.hasArg("alert")) {
        if (light_state[light]) {
          current_rgbw[light][0] = 0; current_rgbw[light][1] = 0; current_rgbw[light][2] = 0; current_rgbw[light][3] = 0;
        } else {
          current_rgbw[light][3] = 255;
        }
      }
      for (uint8_t j = 0; j <= 3; j++) {
        if (light_state[light]) {
          step_level[light][j] = ((float)rgbw[light][j] - current_rgbw[light][j]) / transitiontime;
        } else {
          step_level[light][j] = current_rgbw[light][j] / transitiontime;
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
    http_content += "<a class=\"pure-button"; if (light_state[0]) http_content += "  pure-button-primary"; http_content += "\" href=\"/?on=true\">ON</a>";
    http_content += "<a class=\"pure-button"; if (!light_state[0]) http_content += "  pure-button-primary"; http_content += "\" href=\"/?on=false\">OFF</a>";
    http_content += "</div>";
    http_content += "<div class=\"pure-control-group\">";
    http_content += "<label for=\"startup\">Startup</label>";
    http_content += "<select onchange=\"this.form.submit()\" id=\"startup\" name=\"startup\">";
    http_content += "<option "; if (EEPROM.read(1) == 0) http_content += "selected=\"selected\""; http_content += " value=\"0\">Last state</option>";
    http_content += "<option "; if (EEPROM.read(1) == 1) http_content += "selected=\"selected\""; http_content += " value=\"1\">On</option>";
    http_content += "<option "; if (EEPROM.read(1) == 2) http_content += "selected=\"selected\""; http_content += " value=\"2\">Off</option>";
    http_content += "</select>";
    http_content += "</div>";
    http_content += "<div class=\"pure-control-group\">";
    http_content += "<label for=\"scene\">Scene</label>";
    http_content += "<select onchange = \"this.form.submit()\" id=\"scene\" name=\"scene\">";
    http_content += "<option "; if (EEPROM.read(2) == 0) http_content += "selected=\"selected\""; http_content += " value=\"0\">Relax</option>";
    http_content += "<option "; if (EEPROM.read(2) == 1) http_content += "selected=\"selected\""; http_content += " value=\"1\">Read</option>";
    http_content += "<option "; if (EEPROM.read(2) == 2) http_content += "selected=\"selected\""; http_content += " value=\"2\">Concentrate</option>";
    http_content += "<option "; if (EEPROM.read(2) == 3) http_content += "selected=\"selected\""; http_content += " value=\"3\">Energize</option>";
    http_content += "<option "; if (EEPROM.read(2) == 4) http_content += "selected=\"selected\""; http_content += " value=\"4\">Bright</option>";
    http_content += "<option "; if (EEPROM.read(2) == 5) http_content += "selected=\"selected\""; http_content += " value=\"5\">Dimmed</option>";
    http_content += "<option "; if (EEPROM.read(2) == 6) http_content += "selected=\"selected\""; http_content += " value=\"6\">Nightlight</option>";
    http_content += "<option "; if (EEPROM.read(2) == 7) http_content += "selected=\"selected\""; http_content += " value=\"7\">Savanna sunset</option>";
    http_content += "<option "; if (EEPROM.read(2) == 8) http_content += "selected=\"selected\""; http_content += " value=\"8\">Tropical twilight</option>";
    http_content += "<option "; if (EEPROM.read(2) == 9) http_content += "selected=\"selected\""; http_content += " value=\"9\">Arctic aurora</option>";
    http_content += "<option "; if (EEPROM.read(2) == 10) http_content += "selected=\"selected\""; http_content += " value=\"10\">Spring blossom</option>";
    http_content += "</select>";
    http_content += "</div>";
    http_content += "<br>";
    http_content += "<div class=\"pure-control-group\">";
    http_content += "<label for=\"state\"><strong>State</strong></label>";
    http_content += "</div>";
    http_content += "<div class=\"pure-control-group\">";
    http_content += "<label for=\"bri\">Bri</label>";
    http_content += "<input id=\"bri\" name=\"bri\" type=\"text\" placeholder=\"" + (String)bri[0] + "\">";
    http_content += "</div>";
    http_content += "<div class=\"pure-control-group\">";
    http_content += "<label for=\"hue\">Hue</label>";
    http_content += "<input id=\"hue\" name=\"hue\" type=\"text\" placeholder=\"" + (String)hue[0] + "\">";
    http_content += "</div>";
    http_content += "<div class=\"pure-control-group\">";
    http_content += "<label for=\"sat\">Sat</label>";
    http_content += "<input id=\"sat\" name=\"sat\" type=\"text\" placeholder=\"" + (String)sat[0] + "\">";
    http_content += "</div>";
    http_content += "<div class=\"pure-control-group\">";
    http_content += "<label for=\"ct\">CT</label>";
    http_content += "<input id=\"ct\" name=\"ct\" type=\"text\" placeholder=\"" + (String)ct[0] + "\">";
    http_content += "</div>";
    http_content += "<div class=\"pure-control-group\">";
    http_content += "<label for=\"colormode\">Color</label>";
    http_content += "<select id=\"colormode\" name=\"colormode\">";
    http_content += "<option "; if (color_mode[0] == 1) http_content += "selected=\"selected\""; http_content += " value=\"1\">xy</option>";
    http_content += "<option "; if (color_mode[0] == 2) http_content += "selected=\"selected\""; http_content += " value=\"2\">ct</option>";
    http_content += "<option "; if (color_mode[0] == 3) http_content += "selected=\"selected\""; http_content += " value=\"3\">hue</option>";
    http_content += "</select>";
    http_content += "</div>";
    http_content += "<div class=\"pure-controls\">";
    http_content += "<span class=\"pure-form-message\"><a href=\"/?alert=1\">alert</a> or <a href=\"/?reset=1\">reset</a></span>";
    http_content += "<label for=\"cb\" class=\"pure-checkbox\">";
    http_content += "</label>";
    http_content += "<button type=\"submit\" class=\"pure-button pure-button-primary\">Save</button>";
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
  lightEngine();
}
