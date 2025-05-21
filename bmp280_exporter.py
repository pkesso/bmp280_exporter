#!/usr/bin/env python3
'''prometheus exporter for BMP280 sensor'''

import argparse
import time
from sys import exit as sys_exit
from bmp280 import BMP280
from prometheus_client import start_http_server, Summary, Gauge

parser = argparse.ArgumentParser(
    description="Prometheus exporter for BMP280 air temperature and pressure sensor")

parser.add_argument('--temperature_scale',
                    action='store',
                    default='celsius',
                    help='[celsius|farenheit|kelvin], default: celsius')
parser.add_argument('--pressure_scale',
                    action='store',
                    default='mmhg',
                    help='[hpa|mmhg], default: mmhg')
parser.add_argument('--listen',
                    action='store',
                    default='0.0.0.0',
                    help='bind to address, default: 0.0.0.0')
parser.add_argument('--port',
                    action='store',
                    type=int,
                    default=8000,
                    help='bind to port, default: 8000')
parser.add_argument('--smbus_bus',
                    action='store',
                    type=int,
                    default=1,
                    help='smbus bus id, default: 1')
parser.add_argument('--polling_interval',
                    action='store',
                    type=int,
                    default=1,
                    help='sensor polling interval, seconds, default: 1')
# TODO verbose

args = parser.parse_args()
#print(args)

REQUEST_TIME = Summary('request_processing_seconds', 'Time spent processing request')

try:
    from smbus2 import SMBus
except ImportError:
    from smbus import SMBus

# Initialise the BMP280
bus = SMBus(args.smbus_bus)
bmp280 = BMP280(i2c_dev=bus)

pressure = Gauge('bmp280_pressure', 'Athomsperic pressure, ' + args.pressure_scale)
temperature = Gauge('bmp280_temperature', 'Air temperature, ' + args.temperature_scale)

@REQUEST_TIME.time()
def get_data():
    '''poll data from bmp280'''

    temperature_raw=bmp280.get_temperature()
    pressure_raw=bmp280.get_pressure()

    if args.temperature_scale=='celsius':
        temperature_processed=temperature_raw
    elif args.temperature_scale=='kelvin':
        temperature_processed=temperature_raw+273.15
    elif args.temperature_scale=='farenheit':
        temperature_processed= 9.0/5.0 * temperature_raw + 32
    else:
        print('ERROR: Wrong temperature_scale: only celsius|farenheit|kelvin supported')
        sys_exit(1)

    if args.pressure_scale=='hpa':
        pressure_processed=pressure_raw
    elif args.pressure_scale=='mmhg':
        pressure_processed=pressure_raw * 0.7500616827
    else:
        print('ERROR: Wrong pressure_scale: only hpa|mmhg supported')
        sys_exit(1)


    temperature.set(temperature_processed)
    pressure.set(pressure_processed)
#    print('{:05.2f}*C {:05.2f}hPa'.format(temperature, pressure))

if __name__ == '__main__':
    start_http_server(args.port, args.listen)
    while True:
        get_data()
        time.sleep(args.polling_interval)
