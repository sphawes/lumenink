int draw = 13;  //sends keyboard 1

void setup() {
  // put your setup code here, to run once:
  pinMode(draw, INPUT);

}

void loop() {
  // put your main code here, to run repeatedly:
  if(!digitalRead(draw)){
    while(!digitalRead(draw)){
      //do nothing, waiting for button to come up
    }
    Keyboard.write('d');
    delay(500);
  }

}
