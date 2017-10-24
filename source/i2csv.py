#!/usr/bin/python

# Utility to download, upload and delete test data from an Infusionsoft database.
#
# e.g.
#   ./intocsv.py Contact --upload TestContacts.csv
#   ./intocsv.py Contact --download newdownload.csv
#   ./intocsv.py Contact --credentials somefile --delete '1862 1864'
#
#   ./intocsv.py --help
#   ./intocsv.py Contact --download - Contact --maxrecords 2 | ./intocsv.py Contact --upload -

import csv
from collections import defaultdict
from InfusionsoftFieldNames import Fields
import argparse
import sys

try:
    from xmlrpclib import ServerProxy, Error
except ImportError:
    from xmlrpc.client import ServerProxy, Error

def mainEntry():
    # Main program entry point
    parser = argparse.ArgumentParser(description='Infusionsoft test data uploader and downloader')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-u','--upload', help='Upload, passing CSV file to upload', nargs=1, type=argparse.FileType('rU' ))
    group.add_argument('-d','--download', help='Download, passing file to create', nargs=1, type=argparse.FileType('wb' ))
    group.add_argument('-x','--delete', help='Delete records, passed a single item space-separated list of ids', nargs=1)
    parser.add_argument('-c', '--credentials', default='credentials',
                        help='Infusionsoft credentials file, containing one line with username and API key separated by a comma')
    parser.add_argument('table', help='Infusionsoft table to download data from or upload it to')
    parser.add_argument('-m', '--maxrecords', type=int, default=25, help='Maximum number of records to download')
    args = parser.parse_args()

    global infusionsoftCredentialFile
    infusionsoftCredentialFile=args.credentials

    if (args.upload):
        idsCreated = writeCsvRecordsToDatabase(args.table,args.upload[0])
        print ' '.join([str(id) for id in idsCreated])
    elif (args.download):
        originalRecords = findSomeRecords(args.table,args.maxrecords)
        writeRecords(args.download[0], originalRecords)
    else: # args.delete
        recordIds = args.delete[0].split()
        deleteRecords( args.table, recordIds )
        print '%d record(s) deleted'%len(recordIds)

# Import credentials from single line file in format:
#username, apiKey

infusionsoftCredentialFile='credentials'
infusionsoft=0 # There's probabably a better way to do singletons, but life's too short.
def getInfusionsoft():
    global infusionsoft
    if infusionsoft == 0:
        with open(infusionsoftCredentialFile,'rU') as cfile:
            infusionsoftCredentials = csv.reader(cfile).next()
            infusionsoft = Infusionsoft(infusionsoftCredentials[0], infusionsoftCredentials[1])
    return infusionsoft

UserDefinedTableIdentities = defaultdict( lambda: 0, { #zero for keys not found
    'Contact': -1,
    # -3:  '', # Referral Partner
    'Lead':-4, # Opportunity
    'Company': -6,
    'ContactAction': -5, # Task/Note/Appointment
    'Job': -9 # Order
})

def addTableEntries( table, entries ):
    # Adds the entries, an array of dictionaries, to the given Infusionsoft table:
    return [getInfusionsoft().DataService('add', table, entry) for entry in entries]

def fieldsForTable(table):
    # Answers all the Infusionsoft fields for the given table
    return Fields[table].splitlines() + ([] if table == 'DataFormField' else userDefinedFieldsFor( table ))

def findSomeRecords(table, numRecords=10):
    # Answers the first numRecords from the given table (or a selection, at least)
    resultArray = getInfusionsoft().DataService('query', table, numRecords, 0,
                                           {'Id': '~<>~ 0'}, fieldsForTable(table))
    return resultArray

def userDefinedFieldsFor(table):
    # Answers a list of all the user defined fields for the given table.
    fieldDefinitions = findSomeRecords('DataFormField', 1000) #Could optimise, but who cares?
    idNumber = UserDefinedTableIdentities[table]
    return [('_' + definition['Name']) for definition in fieldDefinitions if definition['FormId'] == idNumber ]

def writeCsvRecordsToDatabase( table, csvFileStream ):
    # Writes all the rows in the given csvFile to IFS table, table.
    return addTableEntries( table, readRecords(csvFileStream) )

def readRecords(csvFileStream):
    # Reads CSV records from the given file, using its header row.
    reader = csv.DictReader(csvFileStream)
    return [{k: row[k] for k in row.keys() if row[k] != ''} for row in reader]


def writeRecords( csvFileStream, records ):
    # Writes the given records as CSV to file filename.
    fieldNames = list(sorted(set([key for record in records for key in record.keys()])))
    csvwriter = csv.DictWriter(csvFileStream, fieldnames=fieldNames)
    csvwriter.writeheader()
    for record in records:
        csvwriter.writerow(record)

def deleteRecords( table, recordIds ):
    # Deletes the given records.
    for id in recordIds:
        getInfusionsoft().DataService('delete', table, id)


# Lifted from Infusionsoft Python API library, and amended to give more helpful error handling:

class Infusionsoft(object):
    base_uri = 'https://%s.infusionsoft.com/api/xmlrpc'
    
    def __init__(self, name, api_key, use_datetime=False):
        uri = self.base_uri % name
        self.client = ServerProxy(uri, use_datetime=use_datetime)
        self.client.error = Error
        self.key = api_key
    
    def __getattr__(self, service):
        def function(method, *args):
            call = getattr(self.client, service + '.' + method)
            
            try:
                return call(self.key, *args)
            except self.client.error as v:
                sys.exit('Infusionsoft error: %s' % str(v))
    
        return function



if __name__ == '__main__':
    mainEntry()

    
    
