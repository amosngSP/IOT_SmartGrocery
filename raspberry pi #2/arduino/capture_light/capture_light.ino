int photoRpin = 0;
int lightlevel;

void setup(){
  Serial.begin(9600);
}

void loop(){
  lightlevel=analogRead(photoRpin);
  Serial.println(lightlevel);
  delay(1000);
}
