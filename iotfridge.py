#!/usr/bin/env python
"""
    iotfridge.py - An IoT fridge API

    This software acts as the API between an SQLite database
    and the interfaces to the fridge.

    Remember to initialise a database first!
"""

# Libraries that we need
import sys
import sqlite3 as sql
import json
#from outpan import OutpanApi
#myOutpanKey = "6d1c5d7cda5b8c56a865158b69890848"
import time

class IoTFridge:
    """
        Implements the IoT Fridge API
    """

    def __init__(self, dbpath, infile, outfile):
        self.db = sql.connect(dbpath)
        self.db.row_factory = sql.Row
        self.cur = self.db.cursor()
        self.infile = infile
        self.outfile = outfile
        #self.outpan = OutpanApi(myOutpanKey)
        self.userSignedIn = None
    # Begin API requests


    def req_listInventory(self, reqj):
        resp = { 'response': [], 'success': True }
        for row in self.cur.execute("SELECT itemName FROM items"):
            # Each row only contains one thing right now, name...
            resp['response'].append({'name': row[0] })
        print >> self.outfile, json.dumps(resp, indent = 1)


    def req_createUser(self, reqj):
        if "name" in reqj:
            userName = reqj['name']
        else:
            resp = { 'response': "ERROR: createUser requires a name.", 'success': False }

        self.cur.execute("INSERT INTO Users(name) VALUES ( ?)", (userName,))
        self.db.commit()
        resp = {'response': "user {0} created".format(userName),
        'success': True}
        print >> self.outfile, json.dumps(resp, indent = 1)


    def req_selectUser(self, reqj):
        userSelected = reqj['userName']
        row = self.cur.execute("SELECT * FROM users WHERE users.name=?",
        (userSelected,)).fetchone()
        if row is not None:
            self.userSignedIn = row["ID"]
            resp = { 'response': "user {0} selected".format(userSelected), 'success': True }
        else:
            resp = { 'response': "user {0} not found".format(userSelected), 'success': False }
        print >> self.outfile, json.dumps(resp, indent = 1)

    def req_addProduct(self, reqj):
        data = (reqj['EAN'], reqj['name'], reqj['daysToUseByAfterOpening'],
        reqj['storageRequirementsID'])
        self.cur.execute(
        "INSERT INTO products(EAN, name, daysToUseByAfterOpening, storageRequirementsID) VALUES ( ?, ?, ?, ?)",
        data)
        self.db.commit()
        row = self.cur.execute("SELECT * FROM products WHERE products.EAN=?",
        (reqj['EAN'],)).fetchone()
        if row is not None:
            resp = { 'response': "product added: {0}".format(row["EAN"]), 'success': True }
        else:
            resp = { 'response': "product not added", 'success': False }
        print >> self.outfile, json.dumps(resp, indent = 1)
        
        
    def req_addItemToInventory(self, reqj):
        if "useByDate" in reqj:
            data = (time.strftime("%d-%m-%Y"), reqj['useByDate'], reqj['EAN'],
             self.userSignedIn)
            self.cur.execute(
            "INSERT INTO inventory(dateAdded, useByDate, productEAN, ownerID) VALUES ( ?, ?, ?, ?)",
             data)
        else:
            data = (time.strftime("%d-%m-%Y"), reqj['EAN'], self.userSignedIn)
            self.cur.execute(
            "INSERT INTO inventory(dateAdded, useByDate, productEAN, ownerID) VALUES ( ?, ?, ?)",
             data)
        self.db.commit()
        resp = {'response': 'OK', 'success': True}
        print >> self.outfile, json.dumps(resp)


    def req_inventoryItemOpened(self, reqj):
        print "ok"
    

    # End API requests


    def processRequest(self, req):
        """
            Takes a JSON request, does some simple checking, and tries to call
            the appropriate method to handle the request. The called method is
            responsible for any output.
        """
        jsonData = json.loads(req)
        if "request" in jsonData:
            reqstr = 'req_{0}'.format(jsonData['request'])
            # Echo the request for easier output debugging
            print req
            if reqstr in dir(self):
                getattr(self,reqstr)(jsonData)
            else:
                print >> sys.stderr, "ERROR: {0} not implemented".format(
                    jsonData['request'])
                errorResp = {
                        'response': "{0} not implemented".format(
                            jsonData['request']),
                        'success': False}
                print >> self.outfile, json.dumps(errorResp)
        else:
                print >> sys.stderr, "ERROR: No request attribute in JSON"

    def run(self):
        """
            Read data input, assume a blank line signifies that the buffered
            data should now be parsed as JSON and acted upon
        """
        lines = []
        while True:
            line = self.infile.readline()
            if line == '': break
            lines.append(line.strip())
            if len(lines) > 1 and lines[-1] == '':
                self.processRequest( ''.join(lines) )
                lines = []


if __name__ == '__main__':
    """
        Connect stdin and stdout to accept and emit JSON data

        Non-API content is printed to stderr, so it can be redirected
        independently.
    """
    if len(sys.argv) != 2:
        print >> sys.stderr, "Usage: python iotfridge.py dbfilename"
        sys.exit(1)
    print >> sys.stderr, "Starting IoTFridge..."
    IOTF = IoTFridge(sys.argv[1], sys.stdin, sys.stdout)
    print >> sys.stderr, "Ready."
    try:
        IOTF.run()
    except KeyboardInterrupt:
        print >> sys.stderr, "Received interrupt, quitting..."
    print >> sys.stderr, "Done"
