#include <WiFi.h>
#include <HTTPClient.h>

const char* ssid = "naam van de wifi";
const char* password = "passwoord van de wifi";
const char* serverName = "http://IPADRESSVANPISERVER:5000/update";  // Controleer dit IP!

const int potentiometerPin = 34;  // Verander naar GPIO34

void setup() {
  Serial.begin(115200);
  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(1000);
    Serial.println("Verbindt met WiFi...");
  }

  Serial.println("Verbonden met WiFi!");
}

void loop() {
 

  int potentiometerValue = analogRead(potentiometerPin);
 

  int Angle = map(potentiometerValue, 0, 4095, 0, 230);

  Serial.print("Gelezen waarde: ");
  Serial.print(potentiometerValue);
  Serial.print(" -> Omgezet naar hoek: ");
  Serial.println(Angle);

  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;
    http.begin(serverName);
    http.addHeader("Content-Type", "application/json");
    http.setTimeout(5000); // Timeout van 5 seconden

    // JSON string maken
    String jsonData = "{\"value\": " + String(Angle) + "}";
    Serial.print("Verstuurde data: ");
    Serial.println(jsonData);

    int httpResponseCode = http.POST(jsonData);

    if (httpResponseCode > 0) {
      Serial.print("Server response: ");
      Serial.println(http.getString());
    } else {
      Serial.print("Fout bij versturen! HTTP-code: ");
      Serial.println(httpResponseCode);
    }

    http.end();
  } else {
    Serial.println("WiFi niet verbonden");
  }

  delay(5000);  // Wacht 5 seconden voor de volgende meting
}
