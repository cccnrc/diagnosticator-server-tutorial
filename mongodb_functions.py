#! /usr/bin/env python3.8
from pymongo import MongoClient, errors

def check_mongoDB_connection( mongoDB_URL ):
    '''
        this simply check that the app is able to communicate with mongo DB
    '''
    try:
        maxSevSelDelay = 2
        client = MongoClient( mongoDB_URL,
                                         serverSelectionTimeoutMS = maxSevSelDelay)
        client.server_info() # force connection on a request as the
                             # connect=True parameter of MongoClient seems
                             # to be useless here
        return( True )
    except errors.ServerSelectionTimeoutError as err:
        return( False )

def accessDB( dbname, mongoDB_URL  ) :
    '''
        this function allows to access the required DB from mongo
        returning the DB object
    '''
    if not mongoDB_URL :
        return( False )
    #Step 1: Connect to MongoDB - Note: Change connection string as needed
    client = MongoClient( mongoDB_URL )
    #client = MongoClient( host='127.0.0.1', port=27017 )   ### alternative specification of DB URL
    db_obj = client[ dbname ]
    return( db_obj )


def checkDBexistance( dbname, mongoDB_URL  ) :
    '''
        this function checks wether a mongo DB exists already
    '''
    client = MongoClient( mongoDB_URL )
    dbnames = client.list_database_names()
    if dbname in dbnames:
        return( True )
    else:
        return( False )


def checkCleanDB( dbname, mongoDB_URL  ) :
    '''
        this function checks wether a mongo DB exists already and in case delete it
    '''
    if checkDBexistance( dbname, mongoDB_URL ):
        print("mongodb_functions.checkCleanDB(): DB {0} exists. Cleaning it ...".format( dbname ) )
        try:
            client = MongoClient( mongoDB_URL )
            client.drop_database( dbname )
            print("  - DB successfully deleted! ")
            return( True )
        except:
            print("  - !!! ERROR !!! in deleting DB! ")
            return( False )




def getAllKEYvalues( dbname, table_name, key_name, mongoDB_URL  ) :
    '''
        this function returns a list with all values from a specific key in the DB
    '''
    db_obj = accessDB( dbname, mongoDB_URL )
    if not db_obj:
        return( False )
    if not checkKEYexistance( dbname, table_name, key_name, mongoDB_URL ):
        return( False )
    print( "mongodb_functions.getAllKEYvalues() : extracting all values of key: {0} from table: {1} in DB: {2}".format( key_name, table_name, dbname ) )
    try:
        value_list = db_obj[ table_name ].distinct( key_name  )
        print( "  - {0} values found".format( len( value_list) ) )
    except:
        print( "  - !!! ERROR !!! problems extracting KEY {0}".format( key_name ) )
        return( False )
    return( value_list )


def checkKEYexistance( dbname, table_name, key_name, mongoDB_URL  ) :
    '''
        here is the function to check if a key already exists in the DB
    '''
    db_obj = accessDB( dbname, mongoDB_URL )
    if not db_obj:
        return( False )
    print("mongodb_functions.checkKEY() : checking existence of key: {0} in table: {1} in DB: {2}".format( key_name, table_name, dbname ))
    if db_obj[ table_name ].find_one( { key_name: { '$exists': False }}):
        print("  - key: {0} NOT found".format( key_name ) )
        return( False )
    else:
        print("  - key: {0} found".format( key_name ) )
        return( True )



def insertDICT( dbname, table_name, key_name, dict_obj, mongoDB_URL ):
    '''
        this function allows to insert the passed dict_obj with the associated key_name in the mongo DB
    '''
    db_obj = accessDB( dbname, mongoDB_URL )
    if not db_obj:
        return( False )
    ### check that the dict_obj is a dict
    if not isinstance( dict_obj, dict ):
        print("mongodb_functions.insertDICT() ERROR: dict_obj is NOT a DICT, Exiting ...".format( dict_obj ) )
        return( False )
    print( "mongodb_functions.insertDICT(): inserting {0} keys in {1}".format( len(dict_obj), table_name ) )
    for i,key in enumerate( dict_obj ) :
        insertion_dict = { key_name : key }
        if isinstance( dict_obj[ key ], dict ):
            for k,v in dict_obj[ key ].items() :
                insertion_dict.update({ k : v })
        else :
            insertion_dict.update({ 'value' : dict_obj[ key ] })
        try:
            result = db_obj[ table_name ].insert_one( insertion_dict )
            print('  - {3}/{4} inserted key: {0} with keys {1} and insertion ID: {2}'.format( key, insertion_dict.keys(), result.inserted_id, i+1, len(dict_obj) ))
        except:
            print('  - {1}/{2} !!! ERROR !!! inserting key: {0}. Trying to update ...'.format( key, i+1, len(dict_obj) ))
            updateDICT( dbname, table_name, key_name, key, dict_obj[ key ] )


def findDBentry( dbname, table_name, key_name, key_value, mongoDB_URL ) :
    '''
        this is to find a single mongo DB entry
    '''
    db_obj = accessDB( dbname, mongoDB_URL )
    if not db_obj:
        return( False )
    print( "mongodb_functions.findDBentry() : trying to access {0} (key: {1}) from table: {2} in DB: {3}".format( key_value, key_name, table_name, dbname ) )
    try:
        entry = db_obj[ table_name ].find_one({ key_name : key_value })
    except:
        print( "  - !!! ERROR !!! Key not found ! " )
        return( False )
    return( entry )


def dbDefineUniqueKey( dbname, table_name, key_name, mongoDB_URL ):
    '''
        this allows to define a key that can NOT have duplicate
    '''
    db_obj = accessDB( dbname, mongoDB_URL )
    if not db_obj:
        return( False )
    print( "mongodb_functions.dbDefineUniqueKey() : setting unique key for {0} in table: {1} in DB: {2}".format( key_name, table_name, dbname ))
    try:
        db_obj[ table_name ].create_index( key_name, unique = True )
        print( "  - unique key for {0} is now set up".format( key_name, table_name, dbname ))
        return( True )
    except:
        print( "  - !!! ERROR !!! setting unique key. Exiting ..." )
        return( False )





def dictionaryUpdate( old_dict, new_dict ):
    '''
        this function update values in old_dict with new_dict
    '''
    if not isinstance( new_dict, dict ):
        print( "  - mongodb_functions.dictionaryUpdate() !!! ERROR !!! new_dict is NOT a dict" )
        return( False )
    if not isinstance( old_dict, dict ):
        print( "  - mongodb_functions.dictionaryUpdate() !!! ERROR !!! old_dict is NOT a dict" )
        return( False )
    updated_dict = old_dict
    for k,v in new_dict.items() :
        ### if present in OLD dict update V if NOT equal
        if k in old_dict:
            if new_dict[k] != old_dict[k]:
                updated_dict[k] = new_dict[k]
        ### if absent add K : V
        else:
            updated_dict.update({ k : v })
    return( updated_dict )


def listUpdate( old_list, new_list ):
    '''
        this takes 2 list and add elements absent from one to the other
    '''
    if not isinstance( new_list, list ):
        print( "  - mongodb_functions.listUpdate() !!! ERROR !!! new_list is NOT a list" )
        return( False )
    if not isinstance( old_list, dict ):
        print( "  - mongodb_functions.listUpdate() !!! ERROR !!! old_list is NOT a list" )
        return( False )
    updated_list = old_list
    for n in new_list:
        if n not in old_list:
            updated_list.append( n )
    return( updated_list )



def valueUpdate( old_obj, new_obj ):
    '''
        this takes 2 values and check if equals and update in case are not
    '''
    if not isinstance( new_obj, ( str, int, long, float, complex ) ):
        print( "  - mongodb_functions.valueUpdate() !!! ERROR !!! new_obj is NOT a string/value" )
        return( False )
    if not isinstance( old_obj, ( str, int, long, float, complex ) ):
        print( "  - mongodb_functions.valueUpdate() !!! ERROR !!! old_obj is NOT a string/value" )
        return( False )
    if new_obj:
        return( new_obj )
    else:
        print( "  - mongodb_functions.valueUpdate() !!! WARNING !!! NO new_obj passed" )
        return( old_obj )





def updateDICT( dbname, table_name, key_name, key_value, new_dict_obj, mongoDB_URL ):
    '''
        this function allows to update the passed dict_obj with the associated key_name in the mongo DB
        - new_dict_obj: the updated dict object for the same key value
    '''
    print( "mongodb_functions.updateDICT(): updating {0} keys for master key: {3}={4} in table: {1} in DB: {2}".format( len( new_dict_obj ), table_name, dbname, key_name, key_value ) )
    print( "  - checking for updates in keys: {}".format( list( new_dict_obj.keys() ) ) )
    db_obj = accessDB( dbname, mongoDB_URL )
    if not db_obj:
        return( False )
    if not isinstance( new_dict_obj, dict ):
        print( "  - mongodb_functions.updateDICT() !!! ERROR !!! new_dict_obj is NOT a dict" )
        return( False )
    if '_id' in new_dict_obj:
        print( "  - removing _id from new_dict_obj")
        new_dict_obj.pop('_id')
    if key_name in new_dict_obj:
        print( "  - removing master key ({0}) from new_dict_obj".format( key_name ) )
        new_dict_obj.pop( key_name )
    ### get the actual DB entry
    old_dict_obj = findDBentry( dbname, table_name, key_name, key_value, mongoDB_URL )
    ### if entry was already present update it
    if old_dict_obj:
        if not isinstance( old_dict_obj, dict ):
            print( "  - mongodb_functions.updateDICT() !!! ERROR !!! old_dict_obj is NOT a dict" )
            return( False )
        ### arrange old_dict_obj
        #   - 1. remove _id value
        if '_id' in old_dict_obj:
            print( "  - removing _id from old_dict_obj")
            old_dict_obj.pop('_id')
        #   - 1. remove _id value
        if key_name in old_dict_obj:
            print( "  - removing master key ({0}) from old_dict_obj".format( key_name ) )
            old_dict_obj.pop( key_name )
        ### check if the 2 DICTs are identical and in case return True
        if new_dict_obj == old_dict_obj :
            print( "  - new_dict_obj and old_dict_obj are identical. Exiting...")
            return( True )
        ### create a DICT to populate with updated values
        updated_dict_obj = old_dict_obj
        for k,v in old_dict_obj.items() :
            ### does not update master key value
            if k == key_name:
                continue
            ### check if the V is a DICT itself or simply a value
            if isinstance( v, dict ):
                updated_dict_obj[ k ] = dictionaryUpdate( old_dict_obj[ k ], new_dict_obj[ k ] )
            elif isinstance( v, list ):
                updated_dict_obj[ k ] = listUpdate( old_dict_obj[ k ], new_dict_obj[ k ] )
            ### if V is simply a value
            else:
                if k in new_dict_obj:
                    updated_dict_obj[ k ] = new_dict_obj[ k ]
                    # updated_dict_obj[ k ] = valueUpdate( old_dict_obj[ k ], new_dict_obj[ k ] )
        ### replace the OLD entry with the NEW one
        deleteDBentry( dbname, table_name, key_name, key_value, mongoDB_URL )
        ### insert all key in new_dict_obj that are NOT in old_dict_obj
        for k,v in new_dict_obj.items():
            if k not in updated_dict_obj:
                updated_dict_obj.update({ k : v })
    else:
        updated_dict_obj = new_dict_obj
    ### insert the NEW entry
    insertion_dict = { key_value : updated_dict_obj }
    insertDICT( dbname, table_name, key_name, insertion_dict, mongoDB_URL )
    ### print logs
    print( "  - updated {0} : {1} in table: {2} in DB: {3}".format( key_name, key_value, table_name, dbname ) )
    return( True )




def deleteDBentry( dbname, table_name, key_name, key_value, mongoDB_URL ):
    '''
        this is to delete a mongoDB entry
    '''
    print( "mongodb_functions.deleteDBentry() : trying to delete {0} : {1} from table: {2} in DB: {3} ...".format( key_name, key_value, table_name, dbname ) )
    db_obj = accessDB( dbname, mongoDB_URL )
    if not db_obj:
        return( False )
    try:
        db_obj[ table_name ].delete_one( db_obj[ table_name ].find_one({ key_name : key_value }) )
        print( "  - deleted {}".format( key_value ) )
    except:
        print( "  - {} NOT found".format( key_value ))
    return( True )



def dictionarizeALLkeyElements( dbname, table_name, key_name, mongoDB_URL ):
    '''
        this returns a DICT with all elements for a key
    '''
    print( "mongodb_functions.dictionarizeALLkeyElements() : trying to get all elements for key: {0} from table: {1} in DB: {2} ...".format( key_name, table_name, dbname ) )
    db_obj = accessDB( dbname, mongoDB_URL )
    if not db_obj:
        return( False )
    k_list = getAllKEYvalues( dbname, table_name, key_name, mongoDB_URL )
    results_dict = {}
    for i,k in enumerate( k_list ):
        print("  - retrieving entry {0}/{1}".format( i, len( k_list ) ))
        v = findDBentry( dbname, table_name, key_name, k, mongoDB_URL )
        if '_id' in v:
            v.pop('_id')
            v.pop( key_name )
        results_dict.update({ k : v })
    return( results_dict )






















### ENDc
