import unittest
from collections import defaultdict
from InfusionsoftFieldNames import Fields
from i2csv import addTableEntries, findSomeRecords, userDefinedFieldsFor, writeCsvRecordsToDatabase, writeRecords, getInfusionsoft, readRecords, deleteRecords
import os

# Tests for the Infusionsoft-CSV utility.
#
# N.b. Requires at least one user-defined field, and for the first user-defined field for Contacts to be of type text.

TestCsvFile2Contacts='''FirstName,LastName,Email
John,Doe,MarkerEmail@email.com
John,Doe2,AnotherMarker@email.com'''

class TestInfusionsoftFunctions(unittest.TestCase):
    def setUp(self):
        self.itemsCreated = defaultdict( lambda: [] ) # key is table name, value is list of ids needing deleting.

        self.contact = {'FirstName' : 'John', 'LastName' : 'Doe', 'Email' : 'johndoe@email.com'}
        self.severalContacts= [{'FirstName' : 'Fred', 'LastName' : 'Doe', 'Email' : '1@email.com'},
                               {'FirstName' : 'Jim', 'LastName' : 'Doe', 'Email' : '2@email.com'},
                               {'FirstName' : 'Sheila', 'LastName' : 'Doe', 'Email' : '3@email.com'}]
                               
        self.tablesToTest=['Contact','Job','Lead','OrderItem','FileBox']

    def tearDown(self):
        for table, items in self.itemsCreated.items():
            for id in items:
                print( 'Deleting', table, id, getInfusionsoft().DataService('delete', table, id) )
        for name in self.tablesToTest:
            try:
                os.remove('%s.csv'%name)
            except:
                pass
            

    def markForDeletion(self, table, ids ):
        self.itemsCreated[table].extend( ids )
    
    def unmarkForDeletion(self, table, ids ):
        self.itemsCreated[table] = [id for id in self.itemsCreated[table] if id not in ids]

    def test_findSomeRecords(self):
        results = findSomeRecords('RecurringOrder')
        self.assertTrue( len(results) > 0 )

    def test_addAndDeleteSeveralContacts(self):
        idsAdded = addTableEntries( 'Contact', self.severalContacts )
        self.markForDeletion('Contact', idsAdded )
        #Check they're actually there:
        resultArray = getInfusionsoft().DataService('query', 'Contact', 1, 0, {'Email': '3@email.com'}, ['Id'])
        self.assertTrue(resultArray[0]['Id'] in idsAdded)
        
        deleteRecords( 'Contact', idsAdded )
        self.unmarkForDeletion( 'Contact', idsAdded )
        resultArray = getInfusionsoft().DataService('query', 'Contact', 1, 0, {'Email': '3@email.com'}, ['Id'])
        self.assertEqual(len(resultArray), 0)

    
    def test_userDefinedFields(self):
        contactFields = userDefinedFieldsFor('Contact')
        self.assertTrue( len(contactFields) > 0 )
        exampleUserField = contactFields[0]
        self.assertTrue( type(exampleUserField) is str )
        self.assertFalse( exampleUserField in userDefinedFieldsFor('RecurringOrder'))
        
        # Make a new contact with our user defined field.
        newContact = self.contact.copy()
        newContact[exampleUserField]='TestValue'
        idsAdded = addTableEntries( 'Contact', [newContact] )
        self.markForDeletion('Contact',idsAdded)
        # And make sure it's there:
        resultArray = getInfusionsoft().DataService('query', 'Contact', 1, 0, {exampleUserField: 'TestValue'}, ['Id'])
        self.assertTrue( len(resultArray)> 0)


    # CSV file tests
    
    def test_writeAndReadCSVFile(self):
        for db in self.tablesToTest:
            originalRecords = findSomeRecords(db,25)
            filename='%s.csv'%db
            with open(filename, 'wb') as filestream:
                writeRecords(filestream, originalRecords)
            
            with open(filename, 'rU') as filestream:
                recordsRead = readRecords(filestream)
            # This gives us only strings. No easy way (or wish) to convert back,
            # so just compare with the string version:
            originalRecordsAsStringsOnly=[{k: str(r[k]) for k in r.keys() }
                                          for r in originalRecords ]
            self.assertEqual( recordsRead, originalRecordsAsStringsOnly )

    def test_writeItemsFromCSVFileToInfusionsoft(self):
        idsWritten = writeCsvRecordsToDatabase('Contact',TestCsvFile2Contacts.splitlines())
        self.markForDeletion('Contact', idsWritten )
        #Check they're actually there:
        resultArray = getInfusionsoft().DataService('query', 'Contact', 1, 0, {'Email': 'MarkerEmail@email.com'}, ['Id'])
        self.assertTrue(resultArray[0]['Id'] in idsWritten)




if __name__ == '__main__':
    unittest.main()

    
    
