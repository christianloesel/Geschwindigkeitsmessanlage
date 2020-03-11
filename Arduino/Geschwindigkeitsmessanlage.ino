#include <LiquidCrystal.h>
#include <EEPROM.h>
#include "TimerOne.h"

LiquidCrystal lcd( 7, 8, 9, 10, 11, 12);

float distance = 100.0;
int distance_address = 0;

float scale = 0.0;
int scale_address = 10;

int sensitivity = 150;
int sensitivity_address = 15;

int sensor_A = A0;
int sensor_B = A1;
int sensor_1 = 900;
int sensor_2 = 900;
int Zeitmesser = 0;
int Loeschen = 0;
int start = 0;
int stop = 0;
int speed = 0;

const byte numChars = 32;
char receivedChars[numChars];
char message[numChars];
String command;
char messageFromPC[numChars] = {0};
float distanceFromPC = 0.0;
float scaleFromPC = 0.0;
boolean newData = false;


void setup()
{
  EEPROM.get(distance_address, distance);
  EEPROM.get(scale_address, scale);
  EEPROM.get(sensitivity_address, sensitivity);
  
  lcd.begin(16,2);
  lcd.setCursor(0,0);
  lcd.print("Messung:");
  lcd.setCursor(0,1);
  lcd.print("Bereit");

  Timer1.initialize(50000);
  Timer1.attachInterrupt(Zeitkonstante);

  Serial.begin(9600);
  Serial.println("<settings," + String(distance) + "," + String(scale) + "," +String(sensitivity) + ">");
}

void Zeitkonstante()
{
  // Start der Zeit
  if (start == 1 || start == 2 && stop == 0)
  {
    Zeitmesser++;
  }

  // Zeit zum Löschen des Displays auf Grundstellung
  if (Loeschen > 0)
  {
    Loeschen++;
  }

}

void loop()
{
  sensor_1 = analogRead(sensor_A); 
  sensor_2 = analogRead(sensor_B);
  
  // Messung wenn Zug aus Richtung 1 kommt
  if (sensor_1 < sensitivity && sensor_2 > sensitivity && start == 0)
  {
    start = 1;
    Serial.println("<display,Messung:,laeuft>");
    lcd.begin(16,2);
    lcd.setCursor(0,0);
    lcd.print("Messung:");
    lcd.setCursor(0,1);
    lcd.print("l");
    lcd.setCursor(1,1);
    lcd.print(char(225));
    lcd.setCursor(2,1);
    lcd.print("uft");
  }
  // Messung gestoppt
  if (sensor_2 < sensitivity && start == 1)
  {
    stop = 1;
  }

  // Messung wenn Zug aus Richtung 2; kommt
  if (sensor_2 < sensitivity && sensor_1 > sensitivity && start == 0)
  {
    start = 2;
    Serial.println("<display,Messung:,laeuft>");
    lcd.begin(16,2);
    lcd.setCursor(0,0);
    lcd.print("Messung:");
    lcd.setCursor(0,1);
    lcd.print("l");
    lcd.setCursor(1,1);
    lcd.print(char(225));
    lcd.setCursor(2,1);
    lcd.print("uft");
  }
  // Messung gestoppt
  if (sensor_1 < sensitivity && start == 2)
  {
    stop = 1;
  }

  // Ausgabe der Geschwindigkeit
  if (stop == 1 && Loeschen == 0)
  {
    // v = s / t; s = Streckenlänge (in cm) / 100 * 87 (Maßstab) * 3,6 * 20 (Auflösung des Interrupts)
    speed = distance / 100 * scale * 3.6 * 20 / Zeitmesser;
    //speed = 3182 / Zeitmesser;
    Zeitmesser = 0;
    Loeschen = 1;
    Serial.println("<display,Geschwindigkeit:," + String(speed) + " km/h>");
    lcd.begin(16,2);
    lcd.setCursor(0,0);
    lcd.print("Geschwindigkeit:");
    lcd.setCursor(0,1);
    lcd.print(speed);
    if (speed < 10)
    {
      lcd.setCursor(2,1);
      lcd.print("km/h");
    }
    else if (speed < 100)
    {
      lcd.setCursor(3,1);
      lcd.print("km/h");
    }
    else if (speed < 1000)
    {
      lcd.setCursor(4,1);
      lcd.print("km/h");
    }
    else
    {
      lcd.setCursor(5,1);
      lcd.print("km/h");
    }
  }

  // Displays löschen, Grundstellung
  if (Loeschen > 150)
  {
    start = 0;
    stop = 0;
    Zeitmesser = 0;
    Loeschen = 0;
    Serial.println("<display,Messung:,Bereit>");
    lcd.begin(16,2);
    lcd.setCursor(0,0);
    lcd.print("Messung:");
    lcd.setCursor(0,1);
    lcd.print("Bereit");
  }

  // Ausgabe wenn beide Sensoren auslösen = Gleis ist belegt
  if (sensor_1 < sensitivity && sensor_2 < sensitivity && start == 0)
  {
    start = 3;
    Serial.println("<display,Messung:,Gleis ist belegt>");
    lcd.begin(16,2);
    lcd.setCursor(0,0);
    lcd.print("Messung:");
    lcd.setCursor(0,1);
    lcd.print("Gleis ist belegt");
  }

  // beide Sensoren wieder in Grundstellung = Gleis ist nicht mehr belegt
  if (sensor_1 > sensitivity && sensor_2 > sensitivity && start == 3)
  {
    start = 0;
    Zeitmesser = 0;
    Serial.println("<display,Messung:,Bereit>");
    lcd.begin(16,2);
    lcd.setCursor(0,0);
    lcd.print("Messung:");
    lcd.setCursor(0,1);
    lcd.print("Bereit");
  }

  // wenn nach dem Auslösen des ersten Sensors eine Zeit von 40 Sekunden überschritten wird: Grundstellung und Ausgabe "Messung ungültig"
  if (Zeitmesser > 800)
  {
    Zeitmesser = 0;
    Loeschen = 1;
    Serial.println("<display,Messung:,ungueltig>");
    lcd.begin(16,2);
    lcd.setCursor(0,0);
    lcd.print("Messung:");
    lcd.setCursor(0,1);
    lcd.print("Ung");
    lcd.setCursor(3,1);
    lcd.print(char(245));
    lcd.setCursor(4,1);
    lcd.print("ltig");
  }
  
  recvWithStartEndMarkers();
  if (newData == true) {
        showParsedData();
        newData = false;
    }
}

void recvWithStartEndMarkers() {
  static boolean recvInProgress = false;
  static byte ndx = 0;
  char startMarker = '<';
  char endMarker = '>';
  char rc;
  
  while (Serial.available() > 0 && newData == false) {
    rc = Serial.read();
    if (recvInProgress == true) {
      if (rc != endMarker) {
        receivedChars[ndx] = rc;
        ndx++;
        if (ndx >= numChars) {
          ndx = numChars - 1;
        }
      }
      else {
        receivedChars[ndx] = '\0'; // terminate the string
        recvInProgress = false;
        ndx = 0;
        newData = true;
      }
    }
    else if (rc == startMarker) {
      recvInProgress = true;
    }
  }
}

void showParsedData() {
  if (newData == true) {
    strcpy(message, receivedChars);
    command = strtok(receivedChars,",");
    if (command == "who"){
      Serial.println("<Messanlage>");
    }
    if (command == "settings") {
      Serial.println("<settings," + String(distance) + "," + String(scale) + "," +String(sensitivity) + ">");
    }
    if (command == "change") {
      parseSettings(message);
    }
  }
}

void parseSettings(char tempChars[numChars]) {      // split the data into its parts
  char * strtokIndx; // this is used by strtok() as an index
  strtokIndx = strtok(tempChars,",");      // get the first part - the string
  strcpy(messageFromPC, strtokIndx); // copy it to messageFromPC

  strtokIndx = strtok(NULL, ","); // this continues where the previous call left off
  distance = atof(strtokIndx);
  EEPROM.put(distance_address, distance);

  strtokIndx = strtok(NULL, ",");
  scale = atof(strtokIndx);
  EEPROM.put(scale_address, scale);
  
  strtokIndx = strtok(NULL, ",");
  sensitivity = atoi(strtokIndx);
  EEPROM.put(sensitivity_address, sensitivity);
  
  Serial.println("<settings," + String(distance) + "," + String(scale) + "," +String(sensitivity) + ">");
}
