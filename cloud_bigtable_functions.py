#! /usr/bin/env python3.8

import datetime

from google.cloud import bigtable
from google.cloud.bigtable import column_family
from google.cloud.bigtable import row_filters

from asilo_variant_cloudBigTable import logPrinter


def implicit():
    '''
        this checks connection credentials for GCP
    '''
    from google.cloud import storage
    # If you don't specify credentials when constructing the client, the
    # client library will look for credentials in the environment.
    try:
        storage_client = storage.Client()
        # Make an authenticated API request
        buckets = list( storage_client.list_buckets() )
        # print( buckets )
        return( True )
    except:
        return( False )
    return( False )





def cloudBigTable_create( projectID, bigtableID, tableID, column_family_ID ):
    '''
        this function creates a GCP BigTable and returns True if the table is created and False otherwise:
        - projectID: GCP project ID
        - bigtableID: GCP BigTable instance ID
        - tableID: GCP BigTable name
    '''
    ### CONNECTION
    client = bigtable.Client( project = projectID, admin = True )
    instance = client.instance( bigtableID )

    ### CREATE the TABLE
    # tableID = "test0"

    print('Creating the {} table.'.format( tableID ))
    table = instance.table( tableID )

    print('Creating column family cf1 with Max Version GC rule...')
    # Create a column family with GC policy : most recent N versions
    # Define the GC policy to retain only the most recent 2 versions
    max_versions_rule = column_family.MaxVersionsGCRule(2)
    # column_family_id = 'cf1'
    column_families = { column_family_ID: max_versions_rule }
    if not table.exists() :
        table.create( column_families = column_families )
        return( True )
    else:
        print( "Table {} already exists.".format( tableID ) )
        return( False )
    return( False )





def cloudBigTable_listCOL( projectID, bigtableID, tableID ) :
    '''
        this returns a LIST of all column families in the table
    '''
    client = bigtable.Client( project = projectID, admin = True )
    instance = client.instance( bigtableID )
    table = instance.table( tableID )
    try:
        column_families = table.list_column_families()
        return( list( column_families.keys() ) )
    except:
        return( False )
    return( False )


def cloudBigTable_createCOL( projectID, bigtableID, tableID, column_family_ID, maxVersionsGC = 2 ) :
    '''
        this creates a column
        - if the COL already exists it fails
    '''
    client = bigtable.Client( project = projectID, admin = True )
    instance = client.instance( bigtableID )
    table = instance.table( tableID )

    ### check column NOT already in table
    column_families = cloudBigTable_listCOL( projectID, bigtableID, tableID )
    if column_family_ID in column_families :
        return( False )

    gc_rule = column_family.MaxVersionsGCRule( maxVersionsGC )
    column_family_obj = table.column_family( column_family_ID, gc_rule = gc_rule )

    try:
        column_family_obj.create()
        return( True )
    except:
        return( False )

    return( False )

@logPrinter
def cloudBigTable_KEYexists( projectID, bigtableID, tableID, row_key ):
    '''
        this function checks wether the row_key exists in the table
    '''
    client = bigtable.Client( project = projectID, admin = True )
    instance = client.instance( bigtableID )
    table = instance.table( tableID )

    if table.read_row( row_key.encode() ):
        return( True )
    else:
        return( False )
    return( False )

def cloudBigTable_KEYinsert( projectID, bigtableID, tableID, row_values_dict, print_time = 0 ):
    '''
        this insert values passed as DICT: K=row_key : { K=column_family_ID : V={ K=field : V=value } }
        - ex. {
                '1-1000-A-C': {
                                'AF': {
                                    'gnomAD_AF': 0.01,
                                    'gnomAD_exomes_AFR_AF': 0.001,
                                    'gnomAD_genomes_AFR_AF': 1e-05
                                },
                                'PRED': {
                                    'REVEL': 0.17,
                                    'CADD': 7,
                                    'polyphen2_HDIV_pred': 'B'
                                }
                },
                '1-2000-A-T': {
                                'AF': {
                                    'gnomAD_AF': 0.001,
                                    'gnomAD_exomes_AFR_AF': 1.45e-12,
                                    'gnomAD_genomes_AFR_AF': 0.001
                                },
                                'PRED': {
                                    'REVEL': 0.89,
                                    'CADD': 19,
                                    'polyphen2_HDIV_pred': 'P'
                                }
                }
            }

        every field will become a columnID inside the column_family_ID
    '''


    client = bigtable.Client( project = projectID, admin = True )
    instance = client.instance( bigtableID )
    table = instance.table( tableID )

    print( "  - adding {0} rows to table: {1} ( {2} @ {3} )".format( len( row_values_dict ), tableID, bigtableID, projectID ) )

    ### extract all column_family_ID in the DICT to insert
    column_families_to_insert = []
    for d in row_values_dict.values():
        for k in list(set(d.keys())):
            if k not in column_families_to_insert :
                column_families_to_insert.append( k )

    ### check column NOT already in table
    print( "  - checking for family columns {0}".format( column_families_to_insert ) )
    column_families_table = cloudBigTable_listCOL( projectID, bigtableID, tableID )
    for c in column_families_to_insert :
        if c not in column_families_table :
            try :
                cloudBigTable_createCOL( projectID, bigtableID, tableID, c  )
                print( "    - created column family: {0}".format( c ) )
            except:
                print( "     - !!! ERROR !!! column family {0} NOT created !!!".format( c ) )

    ### initiate a DICT where to store values to UPDATE in the Table (KEYs already existing)
    row_values_dict_toUpdate = {}
    ### then create row list to insert in table
    i = 0
    rows = []
    dt_start_chunk = datetime.datetime.now()
    for key, row_dict in row_values_dict.items() :

        ### print logs
        # dt_start_chunk = chunkLOGprinter( i, 'key', len( row_values_dict ), dt_start_chunk, chunkN = 2 )

        ### if row_key already in Table it updates it
        if cloudBigTable_KEYexists( projectID, bigtableID, tableID, key ) :
            print( "    - check for UPDATE: {}".format( key ) )
            row_values_dict_toUpdate.update({ key : row_dict })
        else :
            print( "    - INSERTING: {}".format( key ) )
            row_key = '{}'.format( key ).encode()
            row = table.direct_row( row_key )
            for column_family_ID, column_dict in row_dict.items() :
                column_family = column_family_ID.encode()
                for field, value in column_dict.items() :
                    field_encoded = field.encode()
                    row.set_cell(column_family,
                                 field_encoded,
                                 '{}'.format( value ),
                                 timestamp = datetime.datetime.utcnow() )
                    rows.append( row )
        i += 1

    try:
        table.mutate_rows( rows )
        print( "  - rows inserted!" )
        if cloudBigTable_KEYupdate( projectID, bigtableID, tableID, row_values_dict_toUpdate ):
            print( "  - rows updated!" )
        else:
            print( "  - !!! ERROR in UPDATE !!!")
        return( True )
    except:
        return( False )

    return( False )







def dictionarizeROW( cloudBigTableRow_object ) :
    '''
        this takes the row object from cloudBigTable and creates a DICT
    '''
    line = cloudBigTableRow_object.cells
    line_dict = {}
    if line :
        for k,v in line.items() :
            line_dict.update({ k : {} })
            for kk,vv in v.items() :
                line_dict[ k ].update({ kk.decode('utf-8') : vv[0].value.decode('utf-8') })
    else:
        return( False )
    return( line_dict )



def cloudBigTable_getRow( projectID, bigtableID, tableID, row_key ) :
    '''
        this takes the row associated with the passed row_key
    '''

    client = bigtable.Client( project = projectID, admin = True )
    instance = client.instance( bigtableID )
    table = instance.table( tableID )

    ### Before you read the data that you wrote, create a filter using row_filters.CellsColumnLimitFilter() to limit the data that Cloud Bigtable returns. This filter tells Cloud Bigtable to return only the most recent version of each value, even if the table contains older versions that haven't been garbage-collected.
    row_filter = row_filters.CellsColumnLimitFilter( 1 )
    ### select a row from the table
    key = row_key.encode()
    # print('Getting AF by row key.')
    row = table.read_row( key, row_filter )
    try :
        dict = { row_key : dictionarizeROW( row ) }
        return( dict )
    except:
        return( False )
    return( False )


def cloudBigTable_getCell( projectID, bigtableID, tableID, row_key, column_name, column_family_ID ) :
    '''
        this takes the CELL associated with the passed row_key and column_name
    '''

    client = bigtable.Client( project = projectID, admin = True )
    instance = client.instance( bigtableID )
    table = instance.table( tableID )

    ### Before you read the data that you wrote, create a filter using row_filters.CellsColumnLimitFilter() to limit the data that Cloud Bigtable returns. This filter tells Cloud Bigtable to return only the most recent version of each value, even if the table contains older versions that haven't been garbage-collected.
    row_filter = row_filters.CellsColumnLimitFilter( 1 )
    ### select a row from the table
    key = row_key.encode()
    column = column_name.encode()
    # print('Getting AF by row key.')
    row = table.read_row( key, row_filter )
    cell = row.cells[ column_family_ID ][ column ][ 0 ]
    val = cell.value.decode('utf-8')
    return( val )







def cloudBigTable_KEYupdate( projectID, bigtableID, tableID, row_values_dict ):
    '''
        this functions update fields in a specified KEY already existing in the Table
    '''
    client = bigtable.Client( project = projectID, admin = True )
    instance = client.instance( bigtableID )
    table = instance.table( tableID )

    ### check column families in table
    column_families_table = cloudBigTable_listCOL( projectID, bigtableID, tableID )

    print( "  - check updates for {0} rows in table: {1} ( {2} @ {3} )".format( len( row_values_dict ), tableID, bigtableID, projectID ) )

    ### this is to take count of all errors possibly happening
    error = 0

    for key, row_dict_NEW in row_values_dict.items() :
        ### get actual ROW values dictionarized
        row_dict_OLD = cloudBigTable_getRow( projectID, bigtableID, tableID, key )[ key ]
        row = table.direct_row( key.encode() )      ### get also the Table row to update
        ### loop over NEW dictionary
        for column_family_ID, column_dict in row_dict_NEW.items() :
            ### if column family already in OLD row
            if column_family_ID in row_dict_OLD:
                ### check all NEW fields : value
                for field, value in column_dict.items() :
                    ### if NEW field already in OLD row
                    if field in row_dict_OLD[ column_family_ID ]:
                        ### if NEW value == OLD value skip it
                        if '{}'.format( value ) == row_dict_OLD[ column_family_ID ][ field ] :
                            continue
                        else:
                            try:
                                row.set_cell(column_family_ID,
                                             field.encode(),
                                             '{}'.format( value ),
                                             timestamp = datetime.datetime.utcnow())
                                row.commit()
                                print( "  - updated key: {0}, column_family: {1}".format( key, column_family_ID ) )
                                print( "     - EX: {0} : {1}  moved to  {2} : {3}".format( field, row_dict_OLD[ column_family_ID ][ field ], field, value ) )
                            except:
                                print( " !!! ERROR !!! updating VALUE: {0}, in {1} : {2} @ KEY: {3}".format( value, field, column_family_ID, key ) )
                                print( "     - EX: {0} : {1}  moving to  {2} : {3}".format( field, row_dict_OLD[ column_family_ID ][ field ], field, value ) )
                                error += 1
                    ### if NEW field NOT in OLD row
                    else:
                        try:
                            row.set_cell(column_family_ID,
                                         field.encode(),
                                         '{}'.format( value ),
                                         timestamp = datetime.datetime.utcnow())
                            row.commit()
                            print( "  - updated key: {0}, column_family: {1}".format( key, column_family_ID ) )
                            print( "     - ADDED:  {2} : {3}".format( field, row_dict_OLD[ column_family_ID ][ field ], field, value ) )
                        except:
                            print( " !!! ERROR !!! updating FIELD: {1} (value: {0}), column family: {2} @ KEY: {3}".format( value, field, column_family_ID, key ) )
                            error += 1
            ### if column family NOT in OLD row
            else:
                ### if column family not in table column_families creates it
                if column_family_ID not in column_families_table :
                    try :
                        cloudBigTable_createCOL( projectID, bigtableID, tableID, c  )
                        print( "    - created column family: {0}".format( c ) )
                    except:
                        print( "     - !!! ERROR !!! column family {0} NOT created !!!".format( c ) )
                ### then add row
                for field, value in column_dict.items() :
                    try:
                        row.set_cell(column_family_ID,
                                     field.encode(),
                                     '{}'.format( value ),
                                     timestamp = datetime.datetime.utcnow())
                        row.commit()
                        print( "  - updated key: {0}, ADDED column_family: {1}".format( key, column_family_ID ) )
                        print( "     - ADDED:  {2} : {3}".format( field, row_dict_OLD[ column_family_ID ][ field ], field, value ) )
                    except:
                        print( " !!! ERROR !!! ADDING column family: {2} (field: {1} & value: {0}) @ KEY: {3}".format( value, field, column_family_ID, key ) )
                        error += 1
    if error == 0:
        return( True )
    else:
        return( False )






def cloudBigTable_delete( projectID, bigtableID, tableID ) :
    '''
        this deletes the BigTable
    '''
    client = bigtable.Client( project = projectID, admin = True )
    instance = client.instance( bigtableID )
    table = instance.table( tableID )
    try:
        table.delete()
        return( True )
    except:
        return( False )
    return( False )
