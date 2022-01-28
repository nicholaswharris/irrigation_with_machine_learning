// This is the Arduino program. The Arduino is plugged into a Raspberry Pi. 
// From the Arduino are connected 3 capacitive soil-moisture sensors. 
// Data from these sensors is fed to serial where the Raspberry Pi can read it.



// These two ints are used to calibrate sensors
const int airValue = 915;
const int waterValue = 730;

// Settings ints
int soilMoistureValue0 = 0;
int soilMoistureValue1 = 0;
int soilMoistureValue2 = 0;
int soilMoisturePercent0 = 0;
int soilMoisturePercent1 = 0;
int soilMoisturePercent2 = 0;

void setup() {
  Serial.begin(9600);
}

void loop() {
  // Reading data from sensors placed in plants
  // Sensor 0: Grey/Purple/White, Left
  soilMoistureValue0 = analogRead(A0);

  // Sensor 1: Blue/Green/Yellow, Center
  soilMoistureValue1 = analogRead(A1);

  // Sensor 2: Brown/Orange/Red, Right
  soilMoistureValue2 = analogRead(A2);

  // Mapping output to scale of 1 to 100
  soilMoisturePercent0 = map(soilMoistureValue0, airValue, waterValue, 0, 100);
  soilMoisturePercent1 = map(soilMoistureValue1, airValue, waterValue, 0, 100);
  soilMoisturePercent2 = map(soilMoistureValue2, airValue, waterValue, 0, 100);

  // If moisture appears less than 0 or greater than 100, move it to whichever is closer
  if (soilMoisturePercent0 < 0) {
    soilMoisturePercent0 = 0;
  }
  if (soilMoisturePercent0 > 100) {
    soilMoisturePercent0 = 100;
  }
  
  if (soilMoisturePercent1 < 0) {
    soilMoisturePercent1 = 0;
  }
  if (soilMoisturePercent1 > 100) {
    soilMoisturePercent1 = 100;
  }  
  
  if (soilMoisturePercent2 < 0) {
    soilMoisturePercent2 = 0;
  }
  if (soilMoisturePercent2 > 100) {
    soilMoisturePercent2 = 100;
  }

  // Print values to serial
  Serial.print(soilMoisturePercent0);
  Serial.print(" ");
  Serial.print(soilMoisturePercent1);
  Serial.print(" ");
  Serial.print(soilMoisturePercent2);
  Serial.println();

  // Wait 5 seconds in between each print
  delay(5000);
}
