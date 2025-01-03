#!/usr/bin/python
# Script based on https://tutorials-raspberrypi.com/raspberry-pi-lcd-display-16x2-characters-display-hd44780/
import time
import RPi.GPIO as GPIO

LCD_RS = 4
LCD_E  = 17
LCD_DATA4 = 18
LCD_DATA5 = 22
LCD_DATA6 = 23
LCD_DATA7 = 24

LCD_WIDTH = 20
LCD_CHR = GPIO.HIGH
LCD_CMD = GPIO.LOW
E_PULSE = 40e-6 # 40 microseconds
E_DELAY = 40e-6 # 40 microseconds

BIT7 = 1 << 7
BIT6 = 1 << 6
BIT5 = 1 << 5
BIT4 = 1 << 4
BIT3 = 1 << 3
BIT2 = 1 << 2
BIT1 = 1 << 1
BIT0 = 1 << 0

LCD_CMD_4BIT_MODE     = (BIT5 | BIT4 | BIT1 | BIT0)
LCD_CMD_FUNCTION_SET  = (BIT5 | BIT4 | BIT1)    # 4 bit interface, 2 line, 5x7
LCD_CMD_DISPLAY_ON    = (BIT3 | BIT2)           # cursor off, blinking off
LCD_CMD_DISPLAY_OFF   = (BIT3)
LCD_CMD_CLEAR_DISPLAY = (BIT0)
LCD_CMD_CURSOR_HOME   = (BIT1)
LCD_CMD_ENTRY_MODE    = (BIT1 | BIT2)           # incremental
LCD_CMD_DD_RAM_ADDR   = (BIT7)
LCD_CMD_CG_RAM_ADDR   = (BIT6)

LCD_LINE_1 = LCD_CMD_DD_RAM_ADDR + 0
LCD_LINE_2 = LCD_CMD_DD_RAM_ADDR + 64
LCD_LINE_3 = LCD_CMD_DD_RAM_ADDR + 20
LCD_LINE_4 = LCD_CMD_DD_RAM_ADDR + 64 + 20
LCD_LINES = [ LCD_LINE_1, LCD_LINE_2, LCD_LINE_3, LCD_LINE_4 ]

def lcd_send_byte(bits, mode, e_delay=E_DELAY, e_pulse=E_PULSE):
    GPIO.output(LCD_RS, mode)
    if bits & 0x10 != 0:
        GPIO.output(LCD_DATA4, GPIO.HIGH)
    else:
        GPIO.output(LCD_DATA4, GPIO.LOW)
    if bits & 0x20 != 0:
        GPIO.output(LCD_DATA5, GPIO.HIGH)
    else:
        GPIO.output(LCD_DATA5, GPIO.LOW)
    if bits & 0x40 != 0:
        GPIO.output(LCD_DATA6, GPIO.HIGH)
    else:
        GPIO.output(LCD_DATA6, GPIO.LOW)
    if bits & 0x80 != 0:
        GPIO.output(LCD_DATA7, GPIO.HIGH)
    else:
        GPIO.output(LCD_DATA7, GPIO.LOW)
    time.sleep(e_delay)
    GPIO.output(LCD_E, GPIO.HIGH)
    time.sleep(e_pulse)
    GPIO.output(LCD_E, GPIO.LOW)
    time.sleep(e_delay)
    if bits & 0x01 != 0:
        GPIO.output(LCD_DATA4, GPIO.HIGH)
    else:
        GPIO.output(LCD_DATA4, GPIO.LOW)
    if bits & 0x02 != 0:
        GPIO.output(LCD_DATA5, GPIO.HIGH)
    else:
        GPIO.output(LCD_DATA5, GPIO.LOW)
    if bits & 0x04 != 0:
        GPIO.output(LCD_DATA6, GPIO.HIGH)
    else:
        GPIO.output(LCD_DATA6, GPIO.LOW)
    if bits & 0x08 != 0:
        GPIO.output(LCD_DATA7, GPIO.HIGH)
    else:
        GPIO.output(LCD_DATA7, GPIO.LOW)
    time.sleep(e_delay)    
    GPIO.output(LCD_E, GPIO.HIGH)  
    time.sleep(e_pulse)
    GPIO.output(LCD_E, GPIO.LOW)  
    time.sleep(e_delay)  

def lcd_init():
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    GPIO.setup(LCD_E, GPIO.OUT)
    GPIO.setup(LCD_RS, GPIO.OUT)
    GPIO.setup(LCD_DATA4, GPIO.OUT)
    GPIO.setup(LCD_DATA5, GPIO.OUT)
    GPIO.setup(LCD_DATA6, GPIO.OUT)
    GPIO.setup(LCD_DATA7, GPIO.OUT)

    # initialize 4-bit mode
    lcd_send_byte(LCD_CMD_4BIT_MODE, LCD_CMD, 0.005) # wait for more than 4.1 ms
    lcd_send_byte(LCD_CMD_FUNCTION_SET, LCD_CMD, 0.005)
    # 4-bit mode initialized
    lcd_send_byte(LCD_CMD_DISPLAY_OFF, LCD_CMD)
    lcd_send_byte(LCD_CMD_CLEAR_DISPLAY, LCD_CMD)
    lcd_send_byte(LCD_CMD_ENTRY_MODE, LCD_CMD)
    lcd_send_byte(LCD_CMD_CURSOR_HOME, LCD_CMD)
    lcd_send_byte(LCD_CMD_DISPLAY_ON, LCD_CMD)

def lcd_message(message):
    message = message.ljust(LCD_WIDTH," ")  
    for i in range(LCD_WIDTH):
      lcd_send_byte(ord(message[i]),LCD_CHR)

def lcd_print(line, message):
    lcd_send_byte(LCD_LINES[line], LCD_CMD)
    lcd_message(message)

if __name__ == '__main__':
    lcd_init()
    
    lcd_print(0, "first line  34567890")
    lcd_print(1, "second line 34567890")
    lcd_print(2, "third line  34567890")
    lcd_print(3, "fourth line 34567890")
    
