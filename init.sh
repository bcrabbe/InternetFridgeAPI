#!/bin/bash
# Example test script for the template that you are given
rm fridge.db 

# This initialises the database:
sqlite3 fridge.db < schema.sql

python2.6 iotfridge.py fridge.db < demo.json
