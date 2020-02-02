#!/usr/bin/env python

# TODO parse args: bus, verbose, hpa/mmhg, c/f/k, addr, port

import time
from bmp280 import BMP280
from prometheus_client import start_http_server, Summary, Gauge

temperature_scale='celsius'
pressure_scale='mmhg'
listen='0.0.0.0'
port=8000
smbus_bus=1

usage_message = """Prometheus exporter for BMP280 air temperature and pressure sensor
           Homepage:
           Options:
           --temperature-scale=[celsius|farenheit|kelvin], default is celsius
           --pressure-scale=[hpa|mmhg], default is hpa
           --bus=<bus id>, default is 1
           --refresh_interval=<seconds>, default is 1
           --verbose
           --listen=<ip>, default is 0.0.0.0
           --port=<port>, default is 8000 #TODO"""

REQUEST_TIME = Summary('request_processing_seconds', 'Time spent processing request')


try:
    from smbus2 import SMBus
except ImportError:
    from smbus import SMBus


# Initialise the BMP280
bus = SMBus(smbus_bus)
bmp280 = BMP280(i2c_dev=bus)

pressure = Gauge('bmp280_pressure', 'Athomsperic pressure, ' + pressure_scale)
temperature = Gauge('bmp280_temperature', 'Air temperature, ' + temperature_scale)

def usage():
    print('usage_message')
    exit(0)

@REQUEST_TIME.time()
def get_data():
    temperature_raw=bmp280.get_temperature()
    pressure_raw=bmp280.get_pressure()

    if temperature_scale=='celsius':
        temperature_processed=temperature_raw
    elif pressure_scale=='kelvin':
        temperature_processed=temperature_raw+273.15
    elif temperature_scale=='farenheit':
        temperature_processed= 9.0/5.0 * temperature_raw + 32
    else:
        print('ERROR: Wrong temperature_scale: only celsius|farenheit|kelvin supported')
        exit(1)

    if pressure_scale=='hpa':
        pressure_processed=pressure_raw
    elif pressure_scale=='mmhg':
        pressure_processed=pressure_raw * 0.7500616827
    else:
        print('ERROR: Wrong pressure_scale: only hpa|mmhg supported')
        exit(1)


    temperature.set(temperature_processed)
    pressure.set(pressure_processed)
#    print('{:05.2f}*C {:05.2f}hPa'.format(temperature, pressure))

if __name__ == '__main__':
    start_http_server(port)
    while True:
        get_data()
        time.sleep(1)
