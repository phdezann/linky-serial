import logging
import linky_serial

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')

linky_serial = linky_serial.Linky()
thread = linky_serial.start_reading()
thread.join()
