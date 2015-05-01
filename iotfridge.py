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
import datetime

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


    def req_iventoryItemDetails(self, reqj):
        if "ID" not in reqj:
            resp = { 'response': "ERROR: must provide an ID to req_iventoryItemDetails",
            'success': False }
        elif self.cur.execute("SELECT ID FROM inventory where inventory.ID=?",(reqj['ID'],)).fetchone() is None:
            resp = { 'response':
            "ERROR: no item with ID={0} in inventory".format(reqj['ID']),
            'success': False }
        else:
            row = self.cur.execute(
            "SELECT * FROM inventory WHERE inventory.ID=?",
            (reqj['ID'],)).fetchone()
            resp = { 'response': [], 'success': True }
            itemAsDict = {
                'ID' : row[0],
                'name': self.cur.execute("SELECT name FROM products WHERE EAN=?",
                (row["productEAN"],)).fetchone()[0],
                'owner' : self.cur.execute("SELECT name FROM users WHERE ID=?",
                (row["ownerID"],)).fetchone()[0],
                'dateAdded' : row["dateAdded"],
                'useByDate' : row["useByDate"],
                'dateOpened' : row["dateOpened"],
                'storageRequirements' :  self.cur.execute(
                "SELECT message FROM storageRequirements WHERE ID=?",(self.cur.execute(
                "SELECT storageRequirementsID FROM products WHERE EAN=?",
                (row["productEAN"],)).fetchone()[0],)).fetchone()[0],
                'productEAN' : row["productEAN"],
                'averageStock' : self.cur.execute("SELECT averageStock FROM products WHERE EAN=?",
                (row["productEAN"],)).fetchone()[0],
                'borrowingMessage' : self.cur.execute(
                "SELECT message FROM borrowingMessages WHERE ID=?",(row["borrowingMessageID"],)).fetchone()[0]
            }
            resp['response'].append(itemAsDict)
        print >> self.outfile, json.dumps(resp, indent = 1)

    def req_listInventory(self, reqj):
        resp = { 'response': [], 'success':True }
        for row in self.cur.execute("SELECT * FROM inventory").fetchall():
            itemAsDict = {
                'ID' : row["ID"],
                'name': self.cur.execute("SELECT name FROM products WHERE EAN=?",
                (row["productEAN"],)).fetchone()[0],
                'owner' : self.cur.execute("SELECT name FROM users WHERE ID=?",
                (row["ownerID"],)).fetchone()[0],
                'dateAdded' : row["dateAdded"],
                'useByDate' : row["useByDate"],
                'dateOpened' : row["dateOpened"],
                'daysToUseByAfterOpening' : self.cur.execute(
                "SELECT daysToUseByAfterOpening FROM products WHERE EAN=?",
                (row["productEAN"],)).fetchone()[0],
                'borrowingMessage' : self.cur.execute(
                "SELECT message FROM borrowingMessages WHERE ID=?",(row["borrowingMessageID"],)).fetchone()[0]
            }
            resp['response'].append(itemAsDict)
        print >> self.outfile, json.dumps(resp, indent = 1)

    def req_listExpiredItems(self, reqj):
        resp = { 'response': [], 'success': True }
        currentDay = datetime.datetime.today()
        for row in self.cur.execute("SELECT * FROM inventory").fetchall():
            if row["useByDate"] is not None:
                useBy = datetime.datetime.strptime(row["useByDate"], "%Y-%m-%d")
            else:
                useBy = datetime.datetime.today()
            if row["dateOpened"]=="unopened":
                dateOpened = datetime.datetime.today()
            else:
                dateOpened = datetime.datetime.strptime(row["dateOpened"], "%Y-%m-%d")

            daysToUseByAfterOpening = datetime.timedelta(days=self.cur.execute(
            "SELECT daysToUseByAfterOpening FROM products WHERE EAN=?",
            (row[4],)).fetchone()[0])
            if currentDay>useBy or currentDay>dateOpened+daysToUseByAfterOpening:
                itemAsDict = {
                    'ID' : row["ID"],
                    'name': self.cur.execute("SELECT name FROM products WHERE EAN=?",
                    (row["productEAN"],)).fetchone()[0],
                    'owner' : self.cur.execute("SELECT name FROM users WHERE ID=?",
                    (row["ownerID"],)).fetchone()[0],
                    'dateAdded' : row["dateAdded"],
                    'useByDate' : row["useByDate"],
                    'dateOpened' : row["dateOpened"],
                    'daysToUseByAfterOpening' : self.cur.execute(
                    "SELECT daysToUseByAfterOpening FROM products WHERE EAN=?",
                    (row["productEAN"],)).fetchone()[0],
                    'borrowingMessage' : self.cur.execute(
                    "SELECT message FROM borrowingMessages WHERE ID=?",(row["borrowingMessageID"],)).fetchone()[0]
                }
                resp['response'].append(itemAsDict)
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
        if "userName" not in reqj:
            resp = { 'response': "ERROR: selectUser requires a userName.", 'success': False }

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
        if "EAN"  not in reqj:
            resp = { 'response': "ERROR: product not added call did not provide EAN", 'success': False }
        elif "name" not in reqj:
            resp = { 'response': "ERROR: product not added call did not provide name", 'success': False }
        elif "daysToUseByAfterOpening"  not in reqj:
            resp = { 'response': "ERROR: product not added call did not provide daysToUseByAfterOpening", 'success': False }
        elif "storageRequirementsID" not in reqj:
            resp = { 'response': "ERROR: product not added call did not provide storageRequirementsID", 'success': False }
        else:
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
                resp = { 'response': "ERROR: failed to add product", 'success': False }
   

        print >> self.outfile, json.dumps(resp, indent = 1)
    
    def req_addItemToInventory(self, reqj):
        if "EAN" not in reqj:
            resp = { 'response': "ERROR: must provide an EAN to add an item to inventory",
             'success': False }
        if "useByDate" in reqj:
            data = (time.strftime("%Y-%m-%d"), reqj['useByDate'], reqj['EAN'],
             self.userSignedIn)
            self.cur.execute(
            "INSERT INTO inventory(dateAdded, useByDate, productEAN, ownerID) VALUES ( ?, ?, ?, ?)",
             data)
        else:
            data = (time.strftime("%Y-%m-%d"), reqj['EAN'], self.userSignedIn)
            self.cur.execute(
            "INSERT INTO inventory(dateAdded, productEAN, ownerID) VALUES ( ?, ?, ?)",
             data)
        self.db.commit()
        resp = {'response': "item added: {0}".format(reqj['EAN']), 'success': True}
        print >> self.outfile, json.dumps(resp, indent = 1)

    def req_addUseByToInventoryItem(self, reqj):
        if "useByDate" not in reqj:
            resp = { 'response':
            "ERROR: must provide an useByDate to addUseByToInventoryItem",
            'success': False }
        elif "ID" not in reqj:
            resp = { 'response':
            "ERROR: must provide an ID to addUseByToInventoryItem",
            'success': False }
        elif self.cur.execute("SELECT ID FROM inventory where inventory.ID=?",(reqj['ID'],)).fetchone() is None:
            resp = { 'response':
            "ERROR: no item with ID={0} in inventory".format(reqj['ID']),
            'success': False }
        else:
            data = (reqj['useByDate'],reqj['ID'])
            self.cur.execute(
            "UPDATE inventory SET useByDate=? WHERE ID=?",
             data)
            self.db.commit()
            resp = {'response': "use by date added", 'success': True}
        print >> self.outfile, json.dumps(resp, indent = 1)

    def req_addBorrowingMessageToInventoryItem(self, reqj):
        if "borrowingMessageID" not in reqj:
            resp = { 'response':
            "ERROR: must provide an borrowingMessageID to req_addBorrowingMessageToInventoryItem",
            'success': False }
        elif "ID" not in reqj:
            resp = { 'response':
            "ERROR: must provide an ID to req_addBorrowingMessageToInventoryItem",
            'success': False }
        elif self.cur.execute("SELECT ID FROM inventory where inventory.ID=?",(reqj['ID'],)).fetchone() is None:
            resp = { 'response':
            "ERROR: no item with ID={0} in inventory".format(reqj['ID']),
            'success': False }
        else:
            data = (reqj['borrowingMessageID'],reqj['ID'])
            self.cur.execute(
            "UPDATE inventory SET borrowingMessageID=? WHERE ID=?",
             data)
            self.db.commit()
            resp = {'response': "borrowingMessage added", 'success': True}
        print >> self.outfile, json.dumps(resp, indent = 1)

    def req_inventoryItemOpened(self, reqj):
        if "ID" not in reqj:
            resp = { 'response': "ERROR: must provide an ID to req_inventoryItemOpened",
            'success': False }
        elif self.cur.execute("SELECT ID FROM inventory where inventory.ID=?",(reqj['ID'],)).fetchone() is None:
            resp = { 'response':
            "ERROR: no item with ID={0} in inventory".format(reqj['ID']),
            'success': False }
        else:
            data = (time.strftime("%Y-%m-%d"),reqj['ID'])
            self.cur.execute("UPDATE inventory SET dateOpened=? WHERE ID=?",
             data)
            self.db.commit()
            row = self.cur.execute("SELECT dateOpened FROM inventory where inventory.ID=?",
            (reqj['ID'],)).fetchone()
            resp = {'response': "item opened on {0}".format(row[0]), 'success': True}
        print >> self.outfile, json.dumps(resp, indent = 1)

    def req_inventoryItemFinished(self, reqj):
        if "ID" not in reqj:
            resp = { 'response': "ERROR: must provide an ID to req_inventoryItemOpened",
            'success': False }
        elif self.cur.execute("SELECT ID FROM inventory where inventory.ID=?",(reqj['ID'],)).fetchone() is None:
            resp = { 'response':
            "ERROR: no item with ID={0} in inventory".format(reqj['ID']),
            'success': False }
        else:
            row = self.cur.execute(
            "SELECT ID,dateAdded,productEAN,ownerID FROM inventory where inventory.ID=?",
            (reqj['ID'],)).fetchone()
            data = (row["ID"],row["dateAdded"],time.strftime("%Y-%m-%d"),row["productEAN"],
            row["ownerID"])
            self.cur.execute(
            "INSERT INTO usedItems(ID, dateAdded, dateFinished, productEAN, ownerID) VALUES ( ?, ?, ?, ?, ?)",
             data)
            self.db.commit()
            self.cur.execute(
            "DELETE FROM inventory where ID=?",(reqj['ID'],))
            self.db.commit()
            resp = {'response': "item finished on {0}".format(time.strftime("%Y-%m-%d")), 'success': True}
        print >> self.outfile, json.dumps(resp, indent = 1)

    def req_generateShoppingList(self, reqj):
        self.req_calculateAverageStock(reqj)
        resp = { 'response': [], 'success':True }
        for product in self.cur.execute(
        "SELECT * FROM products WHERE products.EAN NOT IN ( SELECT DISTINCT productEAN FROM inventory WHERE inventory.ownerID=? ) ORDER BY products.averageStock DESC",
        (self.userSignedIn,)).fetchall():
            itemAsDict = {
                'name': product["name"],
                'averageStock' : product["averageStock"]
            }
            resp['response'].append(itemAsDict)
        print >> self.outfile, json.dumps(resp, indent = 1)



    def req_calculateAverageStock(self, reqj):
        startDateInUsedItems = self.cur.execute("SELECT MIN(dateAdded) FROM usedItems").fetchone()
        if startDateInUsedItems is None:
            return
        startDate = datetime.datetime.strptime( startDateInUsedItems[0], "%Y-%m-%d")
        currentDay = datetime.datetime.today()
        delta = (currentDay-startDate).days
        for product in self.cur.execute("SELECT EAN FROM products").fetchall():
            sum = 0
            for eachUsed in self.cur.execute(
            "SELECT * FROM usedItems WHERE productEAN=?",(product["EAN"],)).fetchall():
                dateAdded = datetime.datetime.strptime( eachUsed["dateAdded"], "%Y-%m-%d")
                dateFinished = datetime.datetime.strptime(eachUsed["dateFinished"], "%Y-%m-%d")
                deltaProd = (dateFinished-dateAdded).days
                sum += deltaProd
            averageStock=sum/float(delta)
            data = (averageStock,product["EAN"])
            self.cur.execute("UPDATE products SET averageStock=? WHERE EAN=?",data)




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
