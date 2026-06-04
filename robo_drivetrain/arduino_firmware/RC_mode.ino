// --- Cytron Pinout Configuration ---
const int PWM_L = 5; const int DIR_L = 7; 
const int PWM_R = 6; const int DIR_R = 8; 

// --- Raw Driving Outputs ---
int left_motor_pwm = 0;
int right_motor_pwm = 0;

// --- Safety Watchdog ---
unsigned long last_command_received = 0;
const unsigned long TIMEOUT_MS = 500; 

// --- Serial Parsing Buffer ---
char inputBuffer[32];
int bufferIdx = 0;

void setup() {
  Serial.begin(115200);

  pinMode(PWM_L, OUTPUT); pinMode(DIR_L, OUTPUT);
  pinMode(PWM_R, OUTPUT); pinMode(DIR_R, OUTPUT);

  // Hard stop on boot
  stopMotors();
}

void loop() {
  // 1. Process Incoming Serial Data
  while (Serial.available() > 0) {
    char incomingChar = Serial.read();
    
    if (incomingChar == '\n' || incomingChar == '\r') {
      inputBuffer[bufferIdx] = '\0'; // End string
      processRcPacket(inputBuffer);
      bufferIdx = 0; // Reset buffer
    } else if (bufferIdx < 31) {
      inputBuffer[bufferIdx++] = incomingChar;
    }
  }

  // 2. Watchdog Failsafe
  if (millis() - last_command_received > TIMEOUT_MS) {
    left_motor_pwm = 0;
    right_motor_pwm = 0;
  }

  // 3. Write directly to the Cytron Driver
  executeMotorMove(PWM_L, DIR_L, left_motor_pwm);
  executeMotorMove(PWM_R, DIR_R, right_motor_pwm);
}

void processRcPacket(char* packet) {
  // Expecting format: "P,120,-120"
  if (packet[0] == 'P' && packet[1] == ',') {
    char* token = strtok(packet + 2, ",");
    if (token != NULL) {
      left_motor_pwm = atoi(token);
      token = strtok(NULL, ",");
      if (token != NULL) {
        right_motor_pwm = atoi(token);
        last_command_received = millis(); // Refresh watchdog
      }
    }
  }
}

void executeMotorMove(int pwmPin, int dirPin, int speedValue) {
  speedValue = constrain(speedValue, -255, 255);
  
  if (speedValue >= 0) {
    digitalWrite(dirPin, HIGH);
    analogWrite(pwmPin, speedValue);
  } else {
    digitalWrite(dirPin, LOW);
    analogWrite(pwmPin, -speedValue); // Invert negative values to positive PWM
  }
}

void stopMotors() {
  analogWrite(PWM_L, 0);
  analogWrite(PWM_R, 0);
}