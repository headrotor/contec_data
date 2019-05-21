# contec_data

Reverse-engineered interface to stream live or download recorded data from CONTEC Pulse Oximeter Model model CMS50D+

Note USB-serial converter is in the CABLE: micro-B connector on device is serial, NOT USB. See code comments for pinout. 

WARNING: UNFIT FOR ANY MEDICAL USE INCLUDING BUT NOT LIMITED TO
DIAGNOSIS AND MONITORING

NO WARRANTY EXPRESS OR IMPLIED. UNDOCUMENTED SERIAL INTERFACE: USE AT OWN RISK


`download_data.py` usage: with contec plugged in and powered on (you may need to insert finger) `python3 download_data.py  contec_data.csv` downloads all data stored in device to output in csv format with a one-line header. 

`positional arguments:
  output_file           Output data CSV file

optional arguments:
  -h, --help            show this help message and exit
  --port [PORT], -p [PORT]
                        Serial port name, e.g. COM3, /dev/ttyUSB0
  --raw_hex, -x         Print raw data as hex bytes to .raw file
  --raw_dec, -r         Print raw data as decimal bytes to .raw file
  --debug, -d           write raw data with cooked data in csv output
  --quiet, -q           Do not print progress and info to stderr
`

`stream_data.py` usage: with contec plugged in and powered on with finger inserted, streams heart rate, spO2 values, and instantaneous pulse value to stdout. Edit file to select serial port 
