#!/usr/bin/env python3

# FOURTH CHALLENGE

import logging
import os
import sys
import time

# https://pycryptodome.readthedocs.io/en/latest/
from Crypto.Util.number import long_to_bytes

# Define logging output
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - [%(levelname)s] - %(message)s')

# Enable debugging messages
debugging = True
if not debugging:
	logging.disable(logging.DEBUG)
# Print start message and delay slightly
logging.info('Starting ' + os.path.relpath(sys.argv[0]))
time.sleep(.001)

# Cryptosystems like RSA works on numbers, but messages are made up of characters. How should we convert our messages
# into numbers so that mathematical operations can be applied? The most common way is to take the ordinal bytes of the
# message, convert them into hexadecimal, and concatenate. This can be interpreted as a base-16 number, and also
# represented in base-10. To illustrate:
#
# message: HELLO
# ascii bytes: [72, 69, 76, 76, 79]
# hex bytes: [0x48, 0x45, 0x4c, 0x4c, 0x4f]
# base-16: 0x48454c4c4f
# base-10: 310400273487
#
# Python's PyCryptodome library implements this with the methods Crypto.Util.number.bytes_to_long and Crypto.Util.number.long_to_bytes.

# Convert the following integer back into a message:
long = int('11515195063862318899931685488813747395775516287289682636499965282714637259206269')
print(long)

binary_str = long_to_bytes(long)
print(binary_str)

flag = binary_str.decode()
print(flag)
