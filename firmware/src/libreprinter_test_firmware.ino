/*
 * Libreprinter is a software allowing to use the Centronics and serial printing
 * functions of vintage computers on modern equipement through a tiny hardware
 * interface.
 * Copyright (C) 2020-2024  Ysard
 */
 #define VERSION     "1.0.0.rc1"

// Enable Serial CDC (USB) for Atmega32u4 (Pro-Micro only for now ?)
#if defined(ARDUINO_AVR_PROMICRO)
#define SerialCDC    Serial
#else
#error "Please Use Atmega32u4 based board!"
#endif

/* Serial config */
// Data pins
#define SERIAL_RX_PIN       0
#define SERIAL_TX_PIN       1
// Hardware flow control pins
#define SERIAL_DSR_DCD_PIN  2
#define SERIAL_DTR_PIN      7
#define SERIAL_REV_OUT_PIN  8
#define SERIAL_RTS_PIN      9

 /* Parallel config */
// Flow control pins
#define STROBE_PIN    3
#define ACK_PIN       4
#define BUSY_PIN      5
#define SELECT_PIN    6
// Data pins
#define DATA0_PIN     A3
#define DATA1_PIN     A2
#define DATA2_PIN     A1
#define DATA3_PIN     A0
#define DATA4_PIN     15
#define DATA5_PIN     14
#define DATA6_PIN     16
#define DATA7_PIN     10

/* Misc config */
// PD4
#define setAckPin()     PORTD |= (1 << PD4)
#define clrAckPin()     PORTD &= ~(1 << PD4)
// PC6
#define setBusyPin()    PORTC |= (1 << PC6)
#define clrBusyPin()    PORTC &= ~(1 << PC6)
// PE6
#define setDtrPin()     PORTE |= (1 << PE6)
#define clrDtrPin()     PORTE &= ~(1 << PE6)
// PB5
#define setRtsPin()     PORTB |= (1 << PB5)
#define clrRtsPin()     PORTB &= ~(1 << PB5)

uint8_t incomingByte = 0;
uint8_t pin_value = 0;
uint8_t total_errors = 0;
char buffer[50];

// Test dataset
const char* default_pin_names[] = { "RST/Reset", "AFD/Autofeed", "ERR/Error", "S.IN/SelectIn", "18" };
const uint8_t output_pins[] = { SERIAL_TX_PIN, SERIAL_REV_OUT_PIN, SERIAL_DTR_PIN, SERIAL_RTS_PIN, ACK_PIN, BUSY_PIN, SELECT_PIN };
const char* output_pin_names[] = { "SERIAL_TX_PIN:D1:DB25_2", "SERIAL_REV_OUT_PIN:D8:J6", "SERIAL_DTR_PIN:D7:DB25_20", "SERIAL_RTS_PIN:D9:J5", "ACK_PIN", "BUSY_PIN", "SELECT_PIN" };
const uint8_t input_pins[]  = { SERIAL_RX_PIN, SERIAL_DSR_DCD_PIN, STROBE_PIN, DATA0_PIN, DATA1_PIN, DATA2_PIN, DATA3_PIN, DATA4_PIN, DATA5_PIN, DATA6_PIN, DATA7_PIN };
const char* input_pin_names[]  = { "SERIAL_RX_PIN:D0:DB25_3", "SERIAL_DSR_DCD_PIN:D2:DB25_6-8", "STROBE_PIN", "DATA0_PIN", "DATA1_PIN", "DATA2_PIN", "DATA3_PIN", "DATA4_PIN", "DATA5_PIN", "DATA6_PIN", "DATA7_PIN" };


void wait_serial_input()
{
    SerialCDC.println(F("Press enter to continue [Enter]"));
    while (true) {
      if (SerialCDC.available() > 0) {
        incomingByte = SerialCDC.read();

        if (incomingByte == '\n')
          break;

        delay(100);
      }
    }
}

void setup()
{
    // Wait USB serial connection (USB CDC 500 Kbauds is still 0 error transmission)
    SerialCDC.begin(500000);
    while (!SerialCDC) {
        // Wait for serial port to connect.
    }

    SerialCDC.print(F("Online version: "));
    SerialCDC.print(F(VERSION));
    SerialCDC.println(F(" - Test firmware"));

    /* Serial config */
    pinMode(SERIAL_RX_PIN, OUTPUT);
    pinMode(SERIAL_TX_PIN, OUTPUT);
    pinMode(SERIAL_REV_OUT_PIN, OUTPUT);
    pinMode(SERIAL_DTR_PIN, OUTPUT);
    pinMode(SERIAL_RTS_PIN, OUTPUT);
    pinMode(SERIAL_DSR_DCD_PIN, INPUT);

    /* Parallel config */
    // Flow control pins
    pinMode(STROBE_PIN, INPUT_PULLUP);
    pinMode(SELECT_PIN, OUTPUT);
    pinMode(ACK_PIN, OUTPUT);
    pinMode(BUSY_PIN, OUTPUT);
    
    // Data pins
    pinMode(DATA0_PIN, INPUT_PULLUP);
    pinMode(DATA1_PIN, INPUT_PULLUP);
    pinMode(DATA2_PIN, INPUT_PULLUP);
    pinMode(DATA3_PIN, INPUT_PULLUP);
    pinMode(DATA4_PIN, INPUT_PULLUP);
    pinMode(DATA5_PIN, INPUT_PULLUP);
    pinMode(DATA6_PIN, INPUT_PULLUP);
    pinMode(DATA7_PIN, INPUT_PULLUP);
}

void loop()
{
    total_errors = 0;

    SerialCDC.println(F("PLEASE Test NOT commanded pulled-up pins"));
    SerialCDC.println(F("========================================"));
    for (uint8_t i = 0; i < 5; i++) {
      SerialCDC.print(F("+ Expect HIGH on: "));
      SerialCDC.println(default_pin_names[i]);
    }
    SerialCDC.println();
    
    
    SerialCDC.println(F("Test OUTPUT pins"));
    SerialCDC.println(F("================"));

    // Set all output pins to LOW
    for (uint8_t i = 0; i < sizeof(output_pins); i++) {
      digitalWrite(output_pins[i], LOW);
      
      SerialCDC.print(F("+ Expect LOW on: "));
      SerialCDC.println(output_pin_names[i]);

      if (output_pins[i] == SELECT_PIN || output_pins[i] == SERIAL_RTS_PIN) {
        SerialCDC.println(F("Note: is pulled-up in a high state on default boards"));
      }

      if (output_pins[i] == SERIAL_DTR_PIN || output_pins[i] == SERIAL_REV_OUT_PIN) {
        SerialCDC.println(F("Note: RS-232 REV/DTR should be linked"));
      }
      
      if (output_pins[i] == SERIAL_DTR_PIN || output_pins[i] == SERIAL_REV_OUT_PIN || output_pins[i] == SERIAL_RTS_PIN) {
        SerialCDC.println(F("Note: Expect ASSERTED at 9V on RS-232 jumper"));
      }
      
      wait_serial_input();
    }

    SerialCDC.println(F("---"));

    // Set all ouput pins to HIGH
    for (uint8_t i = 0; i < sizeof(output_pins); i++) {
      digitalWrite(output_pins[i], HIGH);
      
      SerialCDC.print(F("+ Expect HIGH on: "));
      SerialCDC.println(output_pin_names[i]);

      if (output_pins[i] == SERIAL_DTR_PIN || output_pins[i] == SERIAL_REV_OUT_PIN || output_pins[i] == SERIAL_RTS_PIN) {
        SerialCDC.println(F("Note: Expect DEASSERTED at -9V on RS-232 jumper"));
      }
      
      wait_serial_input();
    }
    SerialCDC.println();
    

    SerialCDC.println(F("Test INPUT pins"));
    SerialCDC.println(F("==============="));

    bool retry_flag = 0;
    for (uint8_t i = 0; i < sizeof(input_pins); i++) {
      // Current value
      // Note: all values should be HIGH/1 since all pins are pulled-up internally
      pin_value = digitalRead(input_pins[i]);

      snprintf(buffer, sizeof buffer, "+ Read value on %s: %d", input_pin_names[i], pin_value);
      SerialCDC.println(buffer);

      SerialCDC.println(F("Waiting manual pin change..."));
      wait_serial_input();

      pin_value = digitalRead(input_pins[i]);
      
      SerialCDC.print(F("detected value: "));
      SerialCDC.println(pin_value);

      if (pin_value == HIGH) {
        SerialCDC.println(F("ERROR: pin didn't changed!!!"));
        
        if (!retry_flag) {
          // Retry one time
          retry_flag = 1;
          i--;
        } else {
          retry_flag = 0;
          total_errors++;
        }
      }
    }
    SerialCDC.println();
    

    SerialCDC.println(F("Autotest cross bridges on PARALLEL INPUT pins"));
    SerialCDC.println(F("============================================="));

    uint8_t error_count = 0;
    uint8_t current_pin;
    // Start from 2: Skip serial pins at the beginning
    for (uint8_t i = 2; i < sizeof(input_pins); i++) {
      // Temporary mode change and held it to LOW
      current_pin = input_pins[i];
      pinMode(current_pin, OUTPUT);
      delay(100);
      digitalWrite(current_pin, LOW);
      delay(50);
      
      // Check all the other pins
      // Start from 2: Skip serial pins at the beginning
      for (uint8_t j = 2; j < sizeof(input_pins); j++) {
        if (current_pin == input_pins[j])
          continue;

        pin_value = digitalRead(input_pins[j]);

        if (pin_value == LOW) {
          snprintf(buffer, sizeof buffer, "%s - %s", input_pin_names[i], input_pin_names[j]);
          SerialCDC.print(F("+ ERROR: bridge detected "));
          SerialCDC.println(buffer);
          
          error_count++;
        }
      }

      // Refresh mode
      pinMode(current_pin, INPUT_PULLUP);
      delay(50);
    }

    // Restore correct status (not pullup)
    pinMode(SERIAL_DSR_DCD_PIN, INPUT);

    if (error_count) {
      SerialCDC.print(F("Found errors: "));
      SerialCDC.println(error_count);

      total_errors += error_count;
    }
    SerialCDC.println();


    SerialCDC.print(F("Tests end! Total auto errors: "));
    SerialCDC.println(total_errors);
    
    SerialCDC.println(F("Restart..."));
    wait_serial_input();
}
