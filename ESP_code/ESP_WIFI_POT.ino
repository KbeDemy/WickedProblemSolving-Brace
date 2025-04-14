#include <WiFi.h>
#include <WiFiManager.h> 
#include <HTTPClient.h>
#include "Adafruit_SHT4x.h" // tempsensor
#include <Adafruit_NeoPixel.h> 

const char* serverName = "http://192.168.0.242:5000/update";  // Controleer dit IP!

const uint8_t potentiometerPin = 32; // GPIO ...
const uint8_t onPin = 13; 
const uint8_t debugLed = 0;

Adafruit_SHT4x sht4 = Adafruit_SHT4x();
Adafruit_NeoPixel pixels(1, debugLed, NEO_GRB + NEO_KHZ800); // 1 = aantal leds

void setup() {
  Serial.begin(115200);
  pixels.begin(); 

  pinMode(onPin, OUTPUT);
  digitalWrite(onPin, HIGH);

  WiFiManager wifiManager;
  wifiManager.resetSettings(); // UNCOMMENT FOR TESTING!

  changeNeoColor(100,0,100);

  if (!wifiManager.autoConnect("smartbrace_SETUP")) {
    changeNeoColor(100,100,0);
    Serial.println("Failed to connect and hit timeout");
    ESP.restart();
  }

  Serial.println("Verbonden met WiFi!");
 
  if (! sht4.begin()) {
    Serial.println("Couldn't find SHT4x");
    while (1) delay(1);
  }

  sht4.setPrecision(SHT4X_HIGH_PRECISION);
  sht4.setHeater(SHT4X_NO_HEATER);
}

void loop() {
  sensors_event_t humidity, temp;
  sht4.getEvent(&humidity, &temp);

  int potentiometerValue = analogRead(potentiometerPin);
 
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
       changeNeoColor(0,100,0);
    } else {
      Serial.print("Fout bij versturen! HTTP-code: ");
      Serial.println(httpResponseCode);
      changeNeoColor(100,0,0);
    }

    http.end();
  } else {
    Serial.println("WiFi niet verbonden");
    changeNeoColor(100,100,0);
  }

  delay(500);  
}

void changeNeoColor(uint8_t red, uint8_t green, uint8_t bleu){
  pixels.setPixelColor(0, pixels.Color(red, green, bleu));
  pixels.show(); 
}
