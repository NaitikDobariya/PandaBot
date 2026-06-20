#include <PID_v1.h>

// ==========================================
// --- PINS CONFIGURATION ---
// ==========================================
// LEFT MOTOR 
const int PWM_L = 5; 
const int DIR_L = 7; 
const int ENC_L_A = 3;  // Hardware Interrupt 1
const int ENC_L_B = 10; 

// RIGHT MOTOR 
const int PWM_R = 6; 
const int DIR_R = 8; 
const int ENC_R_A = 2;  // Hardware Interrupt 0
const int ENC_R_B = 4;  

// ==========================================
// --- GLOBAL VARIABLES ---
// ==========================================
volatile long ticks_L = 0;
volatile long ticks_R = 0;

long prev_ticks_L = 0;
long prev_ticks_R = 0;

double target_L = 0, current_vel_L = 0, pwm_out_L = 0;
double target_R = 0, current_vel_R = 0, pwm_out_R = 0;

// Optimized Tuning Parameters for smooth tracking
double Kp = 2.9, Ki = 1.0, Kd = 0.0; 

PID pidLeft(&current_vel_L, &pwm_out_L, &target_L, Kp, Ki, Kd, DIRECT);
PID pidRight(&current_vel_R, &pwm_out_R, &target_R, Kp, Ki, Kd, DIRECT);

unsigned long last_time = 0;
unsigned long last_cmd_time = 0;
const int LOOP_TIME = 50; // 50ms = 20Hz loop
const unsigned long WATCHDOG_TIMEOUT = 500; 

double prev_target_L = 0;
double prev_target_R = 0;

char serialBuffer[32];
int bufferIndex = 0;

void setup() {
  Serial.begin(115200);

  pinMode(PWM_L, OUTPUT); pinMode(DIR_L, OUTPUT);
  pinMode(PWM_R, OUTPUT); pinMode(DIR_R, OUTPUT);
  
  pinMode(ENC_L_A, INPUT_PULLUP); pinMode(ENC_L_B, INPUT_PULLUP);
  pinMode(ENC_R_A, INPUT_PULLUP); pinMode(ENC_R_B, INPUT_PULLUP);

  // Attach both healthy hardware interrupts
  attachInterrupt(digitalPinToInterrupt(ENC_L_A), countLeft, RISING);
  attachInterrupt(digitalPinToInterrupt(ENC_R_A), countRight, RISING);

  pidLeft.SetMode(AUTOMATIC); pidLeft.SetOutputLimits(-255, 255); pidLeft.SetSampleTime(LOOP_TIME); 
  pidRight.SetMode(AUTOMATIC); pidRight.SetOutputLimits(-255, 255); pidRight.SetSampleTime(LOOP_TIME); 
}

void loop() {
  while (Serial.available() > 0) {
    char c = Serial.read();
    if (c == '\n' || c == '\r') {
      serialBuffer[bufferIndex] = '\0'; parseCommand(serialBuffer); bufferIndex = 0; 
    } else if (bufferIndex < 31) {
      serialBuffer[bufferIndex++] = c;
    }
  }

  // Safety Watchdog
  if (millis() - last_cmd_time > WATCHDOG_TIMEOUT) {
    target_L = 0; target_R = 0;
  }

  unsigned long now = millis();
  if (now - last_time >= LOOP_TIME) {
    last_time = now;

    // Grab a safe snapshot of the ticks
    noInterrupts();
    long current_total_L = ticks_L;
    long current_total_R = ticks_R;
    interrupts(); 

    // Calculate raw velocity
    double raw_vel_L = (double)(current_total_L - prev_ticks_L);
    double raw_vel_R = (double)(current_total_R - prev_ticks_R);

    prev_ticks_L = current_total_L;
    prev_ticks_R = current_total_R;

    // --- CRITICAL REVERSE POLARITY GUARD ---
    if (target_L < 0 && raw_vel_L > 0) raw_vel_L = -raw_vel_L;
    if (target_L > 0 && raw_vel_L < 0) raw_vel_L = -raw_vel_L;
    if (target_R < 0 && raw_vel_R > 0) raw_vel_R = -raw_vel_R;
    if (target_R > 0 && raw_vel_R < 0) raw_vel_R = -raw_vel_R;

    current_vel_L = raw_vel_L;
    current_vel_R = raw_vel_R;

    // --- ZERO CROSSING INTEGRAL RESET ---
    // Clears PID memory when stopping or reversing to prevent jitter/panic
    if ((target_L > 0 && prev_target_L <= 0) || (target_L < 0 && prev_target_L >= 0) || target_L == 0) {
      pidLeft.SetMode(MANUAL); pwm_out_L = 0; pidLeft.SetMode(AUTOMATIC);
    }
    if ((target_R > 0 && prev_target_R <= 0) || (target_R < 0 && prev_target_R >= 0) || target_R == 0) {
      pidRight.SetMode(MANUAL); pwm_out_R = 0; pidRight.SetMode(AUTOMATIC);
    }

    prev_target_L = target_L; prev_target_R = target_R;

    // Compute PID (or bypass if target is 0)
    if (target_L == 0) pwm_out_L = 0; else pidLeft.Compute();
    if (target_R == 0) pwm_out_R = 0; else pidRight.Compute();

    driveLeftMotor(pwm_out_L);
    driveRightMotor(pwm_out_R);

    // Send Odom
    Serial.print("O,"); Serial.print(current_total_L); Serial.print(","); Serial.println(current_total_R);
  }
}

// ==========================================
// --- HARDWARE INTERRUPT SERVICE ROUTINES ---
// ==========================================
void countLeft() {
  if (digitalRead(ENC_L_B) == HIGH) { ticks_L++; } else { ticks_L--; }
}

void countRight() {
  // If your right wheel counts backward when moving forward after replacing the cable,
  // simply change the '==' to '!=' here.
  if (digitalRead(ENC_R_B) == HIGH) { ticks_R--; } else { ticks_R++; }
}

// ==========================================
// --- HELPERS ---
// ==========================================
void parseCommand(char* cmd) {
  if (cmd[0] == 'T' && cmd[1] == ',') {
    char* strtokIndx = strtok(cmd + 2, ","); 
    if (strtokIndx != NULL) { target_L = atof(strtokIndx); strtokIndx = strtok(NULL, ",");
      if (strtokIndx != NULL) { target_R = atof(strtokIndx); last_cmd_time = millis(); }
    }
  }
}

void driveLeftMotor(double pwm) {
  if (abs(pwm) < 5) pwm = 0; 
  if (pwm >= 0) {
    digitalWrite(DIR_L, LOW);  analogWrite(PWM_L, pwm);
  } else {
    digitalWrite(DIR_L, HIGH); analogWrite(PWM_L, -pwm); 
  }
}

void driveRightMotor(double pwm) {
  if (abs(pwm) < 5) pwm = 0; 
  if (pwm >= 0) {
    digitalWrite(DIR_R, LOW);  analogWrite(PWM_R, pwm);
  } else {
    digitalWrite(DIR_R, HIGH); analogWrite(PWM_R, -pwm);
  }
}