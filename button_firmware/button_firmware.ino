#include <Keyboard.h>

int draw = 11;  //sends keyboard 1
int meme = 12;

void setup() {
  // put your setup code here, to run once:
  pinMode(draw, INPUT);
  pinMode(meme, INPUT);
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
    if(!digitalRead(meme)){
    delay(100);
    //Keyboard.write('https://www.youtube.com/watch?v=dQw4w9WgXcQ');
    Keyboard.print("https://www.youtube.com/watch?v=dQw4w9WgXcQ");
    Keyboard.write(KEY_RETURN);
    delay(500);
    while(!digitalRead(meme)){
      //do nothing, waiting for button to come up
    }
  }
}


