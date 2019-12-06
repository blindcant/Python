#!/usr/bin/python3
import logging, sys, os, time

# Define logging output
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - [%(levelname)s] - %(message)s')

# Enable debugging messages
debugging = True
if not debugging:
	logging.disable(logging.DEBUG)
# Print start message and delay slightly	
logging.info('Starting ' + os.path.relpath(sys.argv[0]))
time.sleep(.001)

# Superclass must be in the same file and before the sub class(es)
class Car:
	# Constructor
	def __init__(self, make, model, year):
		self.make = make
		self.model = model
		self.year = year
		self.odometer = 0

	def get_details(self):
		return f"{self.year} {self.make} {self.model} {self.odometer} km"

	def read_odometer(self):
		return f"{self.odometer}"

	def update_odometer(self, kilometers):
		if kilometers >= self.odometer:
			self.odometer = kilometers
		else:
			print("Cannot roll back the odometer.")

	def increment_odometer(self, kilometers):
		self.odometer += kilometers
