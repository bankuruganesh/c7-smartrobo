#include <Servo.h>

#define IN1 8
#define IN2 7
#define IN3 4
#define IN4 5
#define ENA 9
#define ENB 3

#define trigPin 2
#define echoPin 6
#define SERVO_PIN 10

Servo camServo;

int speedValue = 120;
int obstacleThreshold = 30;


void setup() {

  pinMode(IN1, OUTPUT);
  pinMode(IN2, OUTPUT);
  pinMode(IN3, OUTPUT);
  pinMode(IN4, OUTPUT);

  pinMode(ENA, OUTPUT);
  pinMode(ENB, OUTPUT);

  pinMode(trigPin, OUTPUT);
  pinMode(echoPin, INPUT);

  Serial.begin(9600);

  camServo.attach(SERVO_PIN);
  camServo.write(90);

  stopMotors();

  delay(1000);
}

void loop() {

  // 🔥 NEW ROBUST SERIAL HANDLING
  if (Serial.available()) {

    String cmd = Serial.readStringUntil('\n');  // ✅ waits for full command

    cmd.trim();          // removes \r, spaces
    cmd.toUpperCase();   // normalize

    if (cmd.length() > 0) {

      Serial.print("Received: ");
      Serial.println(cmd);

      processCommand(cmd);
    }
  }
}

// =====================================
// COMMAND PROCESSOR
// =====================================

void processCommand(String cmd) {

  if (cmd == "F") {
    moveForward();
  }
  else if (cmd == "B") {
    moveBackward();
  }
  else if (cmd == "L") {
    turnLeftSmooth();
  }
  else if (cmd == "R") {
    turnRightSmooth();
  }
  else if (cmd == "S") {
    stopMotors();
  }
  else if (cmd == "A") {
    autonomousMode();
  }
  else if (cmd == "U") {
    sendUltrasonic();
  }
  else if (cmd.startsWith("P")) {
    int angle = cmd.substring(1).toInt();
    angle = constrain(angle, 0, 180);
    camServo.write(angle);
    Serial.print("SERVO:");
    Serial.println(angle);
  }
  else if (cmd.startsWith("V")) {
    speedValue = constrain(cmd.substring(1).toInt(), 0, 255);
    Serial.print("SPEED:");
    Serial.println(speedValue);
  }
}

// =====================================
// MOVEMENT FUNCTIONS
// =====================================

void moveForward() {

  Serial.println("MOVING FORWARD");  // 🔥 debug

  analogWrite(ENA, speedValue);
  analogWrite(ENB, speedValue);

  digitalWrite(IN1, HIGH);
  digitalWrite(IN2, LOW);

  digitalWrite(IN3, HIGH);
  digitalWrite(IN4, LOW);
}

void moveBackward() {

  Serial.println("MOVING BACKWARD");

  analogWrite(ENA, speedValue);
  analogWrite(ENB, speedValue);

  digitalWrite(IN1, LOW);
  digitalWrite(IN2, HIGH);

  digitalWrite(IN3, LOW);
  digitalWrite(IN4, HIGH);
}

void turnRightSmooth() {

  Serial.println("TURN RIGHT");

  analogWrite(ENA, speedValue);
  analogWrite(ENB, speedValue);

  digitalWrite(IN1, HIGH);
  digitalWrite(IN2, LOW);

  digitalWrite(IN3, LOW);
  digitalWrite(IN4, HIGH);
}

void turnLeftSmooth() {

  Serial.println("TURN LEFT");

  analogWrite(ENA, speedValue);
  analogWrite(ENB, speedValue);

  digitalWrite(IN1, LOW);
  digitalWrite(IN2, HIGH);

  digitalWrite(IN3, HIGH);
  digitalWrite(IN4, LOW);
}

void stopMotors() {

  Serial.println("STOP");

  analogWrite(ENA, 0);
  analogWrite(ENB, 0);

  digitalWrite(IN1, LOW);
  digitalWrite(IN2, LOW);

  digitalWrite(IN3, LOW);
  digitalWrite(IN4, LOW);
}

// =====================================
// AUTONOMOUS MODE
// =====================================

void autonomousMode() {

  Serial.println("AUTO MODE");

  long distance = getDistance();

  if (distance > 0 && distance < obstacleThreshold) {

    stopMotors();
    delay(200);

    while (distance > 0 && distance < obstacleThreshold) {

      turnRightSmooth();
      distance = getDistance();
    }

    moveForward();
  }
  else {
    moveForward();
  }
}

// =====================================
// ULTRASONIC
// =====================================

long getDistance() {

  digitalWrite(trigPin, LOW);
  delayMicroseconds(2);

  digitalWrite(trigPin, HIGH);
  delayMicroseconds(10);

  digitalWrite(trigPin, LOW);

  long duration = pulseIn(echoPin, HIGH, 30000);

  if (duration == 0) {
    return -1;
  }

  return duration * 0.034 / 2;
}

// =====================================
// SEND DISTANCE
// =====================================

void sendUltrasonic() {

  long d = getDistance();

  Serial.print("DIST:");
  Serial.println(d);
}
