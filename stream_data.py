#!/usr/bin/python
# -*- coding: utf-8 -*-
# reverse-engineered interface to read streaming data from
# CONTEC Pulse Oximeter Model model CMS50D+

# Note USB-serial converter is in the CABLE: micro-B connector on device is serial, NOT USB.

### WARNING: UNFIT FOR ANY MEDICAL USE INCLUDING BUT NOT LIMITED TO DIAGNOSIS AND MONITORING
### NO WARRANTY EXPRESS OR IMPLIED, UNDOCUMENTED SERIAL INTERFACE: USE AT OWN RISK

# communication is over the USB-serial converter at 115200 baud, 8 bits, no parity or handshake.
# Serial protocol seems to be mostly 9-byte packets.

# Commands are all 9 bytes starting with  0x7D 0x81. 
# The third byte seems to be some kind of opcode. 
# Remaining bytes are padded with 0x80 although there may be data in a command I have not captured. 
# In the response, the high bit is set on all but the first byte. 


# the microusb connector is NOT USB it is serial! 
# Pinout (flat side up, looking INTO device female jack)

# _____________
# | 1 2 3 4 5 |   
# \._________./
#  
# Pin 2: device RX (Host TX) (white?)
# Pin 3: device TX (Host RX) (green?)
# Pin 5: GND                 (black)
# other pins: NC?

import serial
import sys
import time

# None to not log
logfn = "contec.log"


"""
         Captured data from serial port: on each line first 9 bytes are sent, remaining bytes are response
         Left column is sent data (9-byte packets), right data is response from device
         7D 81 A7 80 80 80 80 80 80  0C 80 
         7D 81 A2 80 80 80 80 80 80  0C 80 
         7D 81 A0 80 80 80 80 80 80  06 80 80 87 
         7D 81 B0 80 80 80 80 80 80  11 80 81 81 80 80 80 80 80 
         7D 81 AC 80 80 80 80 80 80  0E 80 81 
         7D 81 B3 80 80 80 80 80 80  13 80 A0 A0 A0 A0 A0 A0 A0 14 80 A0 A0 A0 A0 A0 80 80  
         7D 81 A8 80 80 80 80 80 80  02 80 80 A0 A0 A0 A0 A0 A0 02 81 FF A0 A0 A0 A0 A0 A0 
         7D 81 AA 80 80 80 80 80 80  04 80 F5 F3 E5 F2 A0 A0 A0 
         7D 81 A9 80 80 80 80 80 80  03 80 A0 A0 A0 A0 A0 A0 A0 
         7D 81 A1 80 80 80 80 80 80  01 E0 85 B3 96 C1 E1 FF FF 
                                     01 E0 85 B0 96 C1 E1 FF FF 
                                     01 E0 85 AE 95 C1 E1 FF FF 
                                     01 E0 85 AC 95 C1 E1 FF FF 
                                     01 E0 85 AB 95 C1 E1 FF FF 
                                     01 E0 85 AA 95 C1 E1 FF FF 
                                     01 E0 85 AA 95 C1 E1 FF FF 

         This is streaming data, first byte is 0x01, second is 0xEn where n indicates data validity: 
                                 0xE0 valid real-time and pulse data (takes a few seconds, not shown in trace above)
                                 0xE1 real-time  data is valid, pulse and spo2 not valid
                                 0xE2 no valid data 
                                 next two bytes are real-time pulse data (for graph) (with high bit set?)
                                 (unsure why two different values, but may echo bar graph and plot on device OLED.
                                 next two bytes are pulse in BPM, and spO2 percent (high bit is set so AND with 0x7F to get integer values)
                                 Last two bytes are 0xFF
"""


# starts streaming real-time data (pulse)
cmd1 = "7D 81 A1 80 80 80 80 80 80"

# starts downloading stored data
cmd1 = "7D 81 A6 80 80 80 80 80 80"

# sent periodically by host --  Keep-alive? May not need this. 
cmd2 = "7d 81 af 80 80 80 80 80 80"

if __name__ == '__main__':

    portname = "/dev/ttyUSB1"
    #portname = "COM7"
    portbaud = 115200
    try:
        ser = serial.Serial(portname, portbaud, timeout=2.0)
    except:
        print('Error opening device at ' + portname)
        print('Edit file to reflect serial port of device')
        raise
    ser = serial.Serial(portname, portbaud, timeout=0.0)
    sys.stderr.write('opened port {}\n'.format(portname))

    if len(sys.argv) > 1:
        logfn = sys.argv[1]
        logfile = open(logfn, 'w')
        sys.stderr.write("Writing data to file ()\n".format(logfn))
    else:
        logfn = "stdout"
        logfile = sys.stdout

    # convert ascii hex to bytes
    cmd1 = [int(s,16) for s in cmd1.split()]
    cmd2 = [int(s,16) for s in cmd2.split()]
    #print(pre_bytes)
    
    ser.write(cmd1) # this command starts dumping downloaded data
    # there;s probably a command that tells how much data is available but
    # I don't know what it is. Just stream data until it stops. 

    ser.write(cmd2)
    time.sleep(0.05)

    packet_count = 0
    wait_count = 0
    keep_going = True
    while keep_going:  # stream data until it stops
        if ser.in_waiting >= 9:
            packet_count += 1
            inbytes = ser.read(9)
            if inbytes[0] == 0x01: 
                #print("got " + str(inbytes))
                if inbytes[1] == 0xE0:
                    # valid streaming data
                    #streaming pulse data
                    print("pulse: {}".format(int(inbytes[5] & 0x7f)))
                    print("heart: {}".format(int(inbytes[3] & 0x7f)))

                    #print("spO: {}".format(int(inbytes[6] & 0x7f)))
                    #print("SpO2: {} ".format(int(inbytes[4])))
                    #print(chartx((inbytes[3] & 0x7F)/100.,80)) 
                    #print([inbytes[n] & 0x7F for n in [3,4,5,6]])
                    sys.stdout.flush()
                    logfile.write("{},".format(time.time()))
                    logfile.write("{},{},{},{},{}\n".format(*[inbytes[n] & 0x7F for n in [2,3,4,5,6]]))
                    logfile.flush()
                else:
                    sys.stderr.write("Waiting for valid data\n")
            else:
                print("got " + str(inbytes))
            time.sleep(0.0001)
            
            if packet_count % 100 == 0:
                #print("sent cms2")
                ser.write(cmd2)
                sys.stderr.write("wrote {} packets to {}\n".format(packet_count,logfn))
                sys.stderr.flush()
                
        else: # waiting for serial data, if there is no more than we are done.
            wait_count += 1
            if wait_count > 300:
                sys.stderr.write("Timeout -- no more data?\n")
                keep_going = False
                break
            time.sleep(0.01)
    logfile.close()
    sys.stderr.write("Finished.\n")
    exit(0)
