import logging
import threading

import serial

PAYLOAD_DELIMITER = b'\x03\x02\n'


class ChecksumFailedException(Exception):
    pass


class Linky:
    def __init__(self):
        self.serial_port = None

    def forward_to_start_of_payload(self):
        while True:
            line = self.serial_port.readline()
            if line[-3:] == b'\x03\x02\n':
                return

    def read_raw_payload(self):
        lines = []
        while True:
            line = self.serial_port.readline()
            if line[-3:] == b'\x03\x02\n':
                return lines
            if line[-2:] == b'\r\n':
                line = line[:-2]
            lines.append(line.decode("utf-8", 'backslashreplace'))

    def compute_checksum(self, value):
        buf = 0
        for c in value:
            buf += ord(c)
        return chr((buf & 63) + 32)

    def try_convert_int(self, raw):
        try:
            return int(raw)
        except ValueError:
            return raw

    def decode(self, values):
        payload = dict()
        for value in values:
            [key, value, *checksum] = value.split(" ")
            checksum = ''.join(checksum)
            if checksum and not checksum == self.compute_checksum(f"{key} {value}"):
                raise ChecksumFailedException()
            payload[key] = self.try_convert_int(value)
        return payload

    def next(self):
        raw_payload = self.read_raw_payload()
        return self.decode(raw_payload)

    def read(self):
        self.serial_port = serial.Serial(port='/dev/ttyS0',
                                         baudrate=1200,
                                         parity=serial.PARITY_NONE,
                                         stopbits=serial.STOPBITS_ONE,
                                         bytesize=serial.SEVENBITS,
                                         timeout=1)
        self.forward_to_start_of_payload()
        while True:
            try:
                payload = self.next()
                logging.info(f"Got {payload}")
            except ChecksumFailedException:
                logging.info("Checksum check failed, ignoring current payload")
            except Exception as e:
                logging.exception(e)

    def start_reading(self):
        thread = threading.Thread(target=self.read, args=())
        thread.start()
        return thread
