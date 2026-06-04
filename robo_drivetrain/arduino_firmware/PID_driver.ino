#include <PID_v1.h>

// --- Pins ---
const int PWM_L = 5; const int DIR_L = 7; 
const int ENC_L_A = 2; const int ENC_L_B = 4;

const int PWM_R = 6; const int DIR_R = 8; 
const int ENC_R_A = 3; const int ENC_R_B = 9;

// --- Absolute Encoders (For ROS Odom) ---
volatile long ticks_L = 0;
volatile long ticks_R = 0;

// --- Velocity Tracking (For PID) ---
long prev_ticks_L = 0;
long prev_ticks_R = 0;

// --- PID Variables ---
double target_L = 0, current_vel_L = 0, pwm_out_L = 0;
double target_R = 0, current_vel_R = 0, pwm_out_R = 0;

// Tuning Parameters: (Proportional, Integral, Derivative)
double Kp = 4.0, Ki = 5.0, Kd = 0.1;

PID pidLeft(&current_vel_L, &pwm_out_L, &target_L, Kp, Ki, Kd, DIRECT);
PID pidRight(&current_vel_R, &pwm_out_R, &target_R, Kp, Ki, Kd, DIRECT);

// --- Timing & Safety ---
unsigned long last_time = 0;
unsigned long last_cmd_time = 0;
const int LOOP_TIME = 50; // 50ms = 20Hz control loop
const unsigned long WATCHDOG_TIMEOUT = 500; // 500ms without command = stop

// --- Serial Buffer ---
char serialBuffer[32];
int bufferIndex = 0;

void setup() {
  Serial.begin(115200);

  pinMode(PWM_L, OUTPUT); pinMode(DIR_L, OUTPUT);
  pinMode(PWM_R, OUTPUT); pinMode(DIR_R, OUTPUT);
  
  // INPUT_PULLUP is generally safer for encoders to prevent floating pins
  pinMode(ENC_L_A, INPUT_PULLUP); pinMode(ENC_L_B, INPUT_PULLUP);
  pinMode(ENC_R_A, INPUT_PULLUP); pinMode(ENC_R_B, INPUT_PULLUP);

  attachInterrupt(digitalPinToInterrupt(ENC_L_A), countLeft, RISING);
  attachInterrupt(digitalPinToInterrupt(ENC_R_A), countRight, RISING);

  // Setup PIDs
  pidLeft.SetMode(AUTOMATIC);
  pidLeft.SetOutputLimits(-255, 255); 
  pidLeft.SetSampleTime(LOOP_TIME); // CRITICAL FIX: Match loop time

  pidRight.SetMode(AUTOMATIC);
  pidRight.SetOutputLimits(-255, 255);
  pidRight.SetSampleTime(LOOP_TIME); 
}

void loop() {
  // 1. NON-BLOCKING SERIAL READ
  // Expected format: "T,15.5,-15.5\n"
  while (Serial.available() > 0) {
    char c = Serial.read();
    if (c == '\n' || c == '\r') {
      serialBuffer[bufferIndex] = '\0'; // Null-terminate the string
      parseCommand(serialBuffer);
      bufferIndex = 0; // Reset buffer for next message
    } else if (bufferIndex < 31) {
      serialBuffer[bufferIndex++] = c;
    }
  }

  // 2. SAFETY WATCHDOG
  if (millis() - last_cmd_time > WATCHDOG_TIMEOUT) {
    target_L = 0;
    target_R = 0;
  }

  // 3. THE 20Hz CONTROL LOOP
  unsigned long now = millis();
  if (now - last_time >= LOOP_TIME) {
    last_time = now;

    // Grab a safe snapshot of the total ticks
    noInterrupts();
    long current_total_L = ticks_L;
    long current_total_R = ticks_R;
    interrupts();

    // Calculate velocity (ticks changed since last loop)
    current_vel_L = (double)(current_total_L - prev_ticks_L);
    current_vel_R = (double)(current_total_R - prev_ticks_R);

    // Save for next time
    prev_ticks_L = current_total_L;
    prev_ticks_R = current_total_R;

    // RUN THE PID MATH
    pidLeft.Compute();
    pidRight.Compute();

    // DRIVE THE MOTORS
    driveLeftMotor(pwm_out_L);
    driveRightMotor(pwm_out_R);

    // SEND ODOMETRY TO PYTHON
    // Format: "O,LeftTotal,RightTotal"
    Serial.print("O,");
    Serial.print(current_total_L);
    Serial.print(",");
    Serial.println(current_total_R);
  }
}

// --- Serial Parsing Helper ---
void parseCommand(char* cmd) {
  // Check if it starts with 'T' (Target command)
  if (cmd[0] == 'T' && cmd[1] == ',') {
    char* strtokIndx = strtok(cmd + 2, ","); // Skip "T,"
    if (strtokIndx != NULL) {
      target_L = atof(strtokIndx); 
      strtokIndx = strtok(NULL, ",");
      if (strtokIndx != NULL) {
        target_R = atof(strtokIndx);
        last_cmd_time = millis(); // Reset watchdog
      }
    }
  }
}

// --- Motor Helpers ---
void driveLeftMotor(double pwm) {
  if (pwm >= 0) {
    digitalWrite(DIR_L, HIGH);
    analogWrite(PWM_L, pwm);
  } else {
    digitalWrite(DIR_L, LOW);
    analogWrite(PWM_L, -pwm); // Make positive
  }
}

void driveRightMotor(double pwm) {
  if (pwm >= 0) {
    digitalWrite(DIR_R, HIGH);
    analogWrite(PWM_R, pwm);
  } else {
    digitalWrite(DIR_R, LOW);
    analogWrite(PWM_R, -pwm);
  }
}

// --- Interrupts ---
void countLeft() {
  if (digitalRead(ENC_L_B) == HIGH) { ticks_L++; } else { ticks_L--; }
}
void countRight() {
  if (digitalRead(ENC_R_B) == HIGH) { ticks_R++; } else { ticks_R--; }
}