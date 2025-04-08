#include <WiFi.h>
#include <HTTPClient.h>
#include "Adafruit_SHT4x.h"

Adafruit_SHT4x sht4 = Adafruit_SHT4x();
const char* ssid = "*****"; // 
const char* password = "*****"; // 
const char* serverName = "http://192.168.0.242:5000/update";  // Controleer dit IP!

const uint8_t potentiometerPin = 32; // GPIO ...
const uint8_t onPin = 13; 
void setup() {
  Serial.begin(115200);
  WiFi.begin(ssid, password);

 
  pinMode(onPin, OUTPUT);
  digitalWrite(onPin, HIGH);

  if (! sht4.begin()) {
    Serial.println("Couldn't find SHT4x");
    while (1) delay(1);
  }
  
  sht4.setPrecision(SHT4X_HIGH_PRECISION);
  sht4.setHeater(SHT4X_NO_HEATER);

  while (WiFi.status() != WL_CONNECTED) {
    delay(1000);
    Serial.println("Verbindt met WiFi...");
  }

  Serial.println("Verbonden met WiFi!");
}

void loop() {
  sensors_event_t humidity, temp;
  sht4.getEvent(&humidity, &temp);

  int potentiometerValue = analogRead(potentiometerPin);
  Serial.println(potentiometerValue);
  int Angle = map(potentiometerValue, 0, 4095, 0, 180);

  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;
    http.begin(serverName);
    http.addHeader("Content-Type", "application/json");
    http.setTimeout(5000); // Timeout van 5 seconden

    // JSON string maken
    String jsonData = "{\"angle\": " + String(Angle) + ", \"temperature\": " + String(temp.temperature) + "}";
    Serial.print("Verstuurde data: ");
    Serial.println(jsonData);

    int httpResponseCode = http.POST(jsonData);

    if (httpResponseCode > 0) {
      Serial.println("Server Responded!");
    } else {
      Serial.print("Fout bij versturen! HTTP-code: ");
      Serial.println(httpResponseCode);
    }

    http.end();
  } else {
    Serial.println("WiFi niet verbonden");
  }

  delay(500);  // Wacht 5 seconden voor de volgende meting
}
