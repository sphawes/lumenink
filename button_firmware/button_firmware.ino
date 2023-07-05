#include <Keyboard.h>

int draw = 11;  //sends keyboard 1

void setup() {
  // put your setup code here, to run once:
  pinMode(draw, INPUT);
  Serial.begin(9600);

}

void loop() {
  // put your main code here, to run repeatedly:
  if(!digitalRead(draw)){
    delay(100);
    Keyboard.write('d');
    delay(500);
    while(!digitalRead(draw)){
      //do nothing, waiting for button to come up
    }
  }
}


