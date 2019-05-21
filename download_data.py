#!/usr/bin/python
# -*- coding: utf-8 -*-
# reverse-engineered interface to download recorded data from
# CONTEC Pulse Oximeter Model model CMS50D+

# Note USB-serial converter is in the CABLE: micro-B connector on device is serial, NOT USB.

### WARNING: UNFIT FOR ANY MEDICAL USE INCLUDING BUT NOT LIMITED TO DIAGNOSIS AND MONITORING
### NO WARRANTY EXPRESS OR IMPLIED, UNDOCUMENTED SERIAL INTERFACE: USE AT OWN RISK

# communication is over the USB-serial converter at 115200 baud, 8 bits, no parity or handshake.
# Serial protocol seems to be mostly 9-byte packets.

# the microusb connector is NOT USB it is serial at 3.3V TTL levels! 
# Pinout (flat side up, looking INTO device female jack)
#
# _____________
# | 1 2 3 4 5 |   
# \._________./
#  
# Pin 2: device RX (Host TX) (USB white wire)
# Pin 3: device TX (Host RX) (USB green wire)
# Pin 5: GND                 (USB black wire -- red wire unused.)
# other pins: NC?

import serial
import sys
import time
import argparse
import os


"""For downloaded (stored) data, data comes from device in 8 byte
packets starting with 0x0F, then 0x80, then three spo2 and pulse
measurements in the remaining six bytes with the high bit set.

e.g.

0F 8X S0 P0 S1 P1 S2 P2

Where S0 and P0 are Spo2 percentage and pulse BPM for one
measurement. Measurements are saved every second so the number of
packets will be 1/3 the time of the stored data in
seconds. Unrecognized pulse/SpO2 (because of finger out or bad
readings are zero.

The second byte 8X is used for flags, not all are understood. The
even-numbered bits are overflow bits to recover values greater than
127 in the pulse. which are masked by the set high bit. As far as I
can figure it out, bit 1 set -> add 127 to P0, bit 3 set _> add 127 to
P1, bit 5 set -> add 127 to P2

Presumably something similar for odd bits and the SpO2 values but
those are never greater than 100%. 

"""

# send this to start downloading stored data
cmd1 = "7D 81 A6 80 80 80 80 80 80"

# sent periodically by host --  Keep-alive? May not need this. 
cmd2 = "7d 81 af 80 80 80 80 80 80"

if __name__ == '__main__':

    if sys.version_info.major < 3:
        print("sorry, requires Python 3.")
        exit(1)

    parser = argparse.ArgumentParser(
        description='Download recorded data from ContecCMS50D+ pulse oximeter.' + "Device must be turned on and connected (insert finger)")
    parser.add_argument('--port', '-p', nargs='?',
                        default="/dev/ttyUSB0",
                        help='Serial port name, e.g. COM3, /dev/ttyUSB0')
    parser.add_argument('--raw_hex','-x',
                        action='store_true',
                        help='Print raw data as hex bytes to .raw file' )
    parser.add_argument('--raw_dec','-r',
                        action='store_true',
                        help='Print raw data as decimal bytes to .raw file' )
    parser.add_argument('--debug','-d',
                        action='store_true',
                        help='write raw data with cooked data' )
    parser.add_argument('--quiet','-q',
                        action='store_true',
                        help='Do not print progress and info to stderr')
    parser.add_argument('output_file', nargs = '?', 
                        help='Output data CSV file',
                        default="contec_data.csv")
    args = parser.parse_args()


    #for linuxes, mac: port = "/dev/ttyUSB1"
    #for windows: portname = "COM7"
    portbaud = 115200
    try:
        ser = serial.Serial(args.port, portbaud, timeout=0.1)
    except:
        print('Error opening device at ' + args.port)
        print('use "-p" flag to specify serial port')
        raise

    if not args.quiet:
        sys.stderr.write('opened port {}\n'.format(args.port))


    logfile = open(args.output_file, 'w')
    if not args.quiet:
        sys.stderr.write("Writing data to file {}\n".format(args.output_file))


    rawfile = None
    if args.raw_hex or args.raw_dec:
        rawfn, ext = os.path.splitext(args.output_file)
        rawfn = rawfn + ".raw"
        rawfile = open(rawfn, 'w')
        if not args.quiet:
            sys.stderr.write("Writing raw data to file {}\n".format(rawfn))

     
    logfile.write("seconds, flags, spO2 (%), pulse (bpm)\n".format(time.time()))
 
   # convert ascii hex to bytes
    cmd1 = [int(s,16) for s in cmd1.split()]
    cmd2 = [int(s,16) for s in cmd2.split()]
    
    ser.write(cmd1) # this command starts dumping downloaded data
    # there;s probably a command that returns how much data is available but
    # I don't know what it is. Just stream data until it stops. 

    ser.write(cmd2)
    time.sleep(0.05)

    packet_count = 0
    seconds = 0
    minutes = 0
    wait_count = 0
    keep_going = True

    while keep_going:  # stream data until it stops
        if ser.in_waiting >= 8:
            packet_count += 1
            inbytes = ser.read(8)
            #print("got " + str(inbytes))
            wait_count = 0
            if True or inbytes[0] == 0x01 or True: 
                #print("got " + str(inbytes))
                if True or inbytes[1] == 0xE0 or True:
                    # valid streaming data
                    #streaming pulse data

                    format_str = "".join("{:03d} " * 8)
                    if args.raw_hex:
                        format_str = "".join("{:02x} " * 8)
                    format_str = format_str + "\n"

                    if rawfile is not None: 
                        rawfile.write(format_str.format(*[inbytes[n]  for n in range(8)]))
                    if args.debug:
                        logfile.write(format_str.format(*[inbytes[n]  for n in range(8)]))

                    for i in range(0,6,2):
                        pulse = 0x7F & inbytes[3 + i]
                        #print("pulse bits: {:08b}\n".format(inbytes[1]))
                        #print(" mask bits: {:08b}\n".format(1 << i+1))
                        if inbytes[1] & (1 << i+1):
                            pulse += 127
                        cookedstr = "{}, {}, {}, {}".format(seconds,
                                                          inbytes[1],
                                                          0x7F & inbytes[2 + i],                                                          pulse)
                        logfile.write(cookedstr + "\n")
                        seconds += 1
                    logfile.flush()
                else:
                    if not args.quiet:
                        sys.stderr.write("Waiting for valid data\n")
            else:
                if not args.quiet:
                    sys.stderr.write("parse error? got " + str(inbytes))

            if (seconds % 60) == 0:
                minutes += 1
                if not args.quiet:
                    sys.stderr.write("downloaded {} minutes\n".format(minutes))
                    sys.stderr.flush()


            time.sleep(0.0001)
            
            if packet_count % 100 == 0:
                #print("sent cms2")
                ser.write(cmd2)
                
        else: # waiting for serial data, if there is no more than we are done.
            wait_count += 1
            if wait_count > 20:
                if not args.quiet:
                    sys.stderr.write("Timeout -- no more data?\n")
                keep_going = False
                break
            time.sleep(0.01)
    logfile.close()
    if not args.quiet:
        sys.stderr.write("Finished - {} seconds data saved to {}\n".format(seconds,args.output_file))
    exit(0)
