#! /usr/bin/env python3.8

import datetime

from google.cloud import bigtable
from google.cloud.bigtable import column_family
from google.cloud.bigtable import row_filters


def cloudBigTable_create( projectID, bigtableID, tableID, column_family_ID ):
    '''
        this function creates a GCP BigTable and returns True if the table is created and False otherwise:
        - projectID: GCP project ID
        - bigtableID: GCP BigTable instance ID
        - tableID: GCP BigTable name
    '''
    ### CONNECTION
    projectID = "diagnosticaotr-00"
    bigtableID = "diagnosticaotr-00-bigtable-00"

    client = bigtable.Client(project=projectID, admin=True)
    instance = client.instance(bigtableID)

    ### CREATE the TABLE
    # tableID = "test0"

    print('Creating the {} table.'.format(tableID))
    table = instance.table(tableID)

    print('Creating column family cf1 with Max Version GC rule...')
    # Create a column family with GC policy : most recent N versions
    # Define the GC policy to retain only the most recent 2 versions
    max_versions_rule = column_family.MaxVersionsGCRule(2)
    # column_family_id = 'cf1'
    column_family_id = column_family_ID
    column_families = { column_family_id: max_versions_rule }
    if not table.exists() :
        table.create( column_families = column_families )
        return( True )
    else:
        print( "Table {} already exists.".format( tableID ) )
        return( False )

    return( False )


def cloudBigTable_insert( row_values_dict, column_family_ID ):
    '''
        this insert values passed as DICT: K=row_key : { K=columnID : V=value }
        in columns with given column_family_ID
    '''
    rows = []
    for key, row_dict in row_values_dict.items() :
        row_key = '{}'.format( key ).encode()
        row = table.direct_row( row_key )
        for columnID, value in row_dict.items() :
            column = columnID.encode()
            row.set_cell(column_family_ID,
                         column,
                         '{}'.format( value ),
                         timestamp = datetime.datetime.utcnow() )
            rows.append( row )
    table.mutate_rows(rows)


### insert value to the table
print('Writing some greetings to the table.')
# greetings = ['Hello World!', 'Hello Cloud Bigtable!', 'Hello Python!']
variants = ['1-1000-A-C', '1-2000-A-C', '1-1000-A-G']
variantAFs = ['0.01', '0.001', '0.01']
rows = []
columnAF = 'AF'.encode()      ### I can group values based on similarity: Ex. AF, in-silico prediction
for i, value in enumerate(variants):
    # Note: This example uses sequential numeric IDs for simplicity,
    # but this can result in poor performance in a production
    # application.  Since rows are stored in sorted order by key,
    # sequential keys can result in poor distribution of operations
    # across nodes.
    #
    # For more information about how to design a Bigtable schema for
    # the best performance, see the documentation:
    #
    #     https://cloud.google.com/bigtable/docs/schema-design
    row_key = '{}'.format(value).encode()
    row = table.direct_row(row_key)
    row.set_cell(column_family_id,
                 columnAF,
                 'AF={}'.format(variantAFs[i]),
                 timestamp=datetime.datetime.utcnow())
    rows.append(row)

table.mutate_rows(rows)


### add a in-silico prediction column
variantREVELs = ['0.35', '0.12', '0.98']
rows = []
columnPRED = 'prediction'.encode()      ### I can group values based on similarity: Ex. AF, in-silico prediction
for i, value in enumerate(variants):
    # Note: This example uses sequential numeric IDs for simplicity,
    # but this can result in poor performance in a production
    # application.  Since rows are stored in sorted order by key,
    # sequential keys can result in poor distribution of operations
    # across nodes.
    #
    # For more information about how to design a Bigtable schema for
    # the best performance, see the documentation:
    #
    #     https://cloud.google.com/bigtable/docs/schema-design
    row_key = '{}'.format(value).encode()
    row = table.direct_row(row_key)
    row.set_cell(column_family_id,
                 columnPRED,
                 'REVEL={}'.format(variantREVELs[i]),
                 timestamp=datetime.datetime.utcnow())
    rows.append(row)

table.mutate_rows(rows)




### Before you read the data that you wrote, create a filter using row_filters.CellsColumnLimitFilter() to limit the data that Cloud Bigtable returns. This filter tells Cloud Bigtable to return only the most recent version of each value, even if the table contains older versions that haven't been garbage-collected.
row_filter = row_filters.CellsColumnLimitFilter(1)




### select a row from the table
key = '1-2000-A-C'.encode()

print('Getting AF by row key.')
row = table.read_row(key, row_filter)
cell = row.cells[column_family_id][columnAF][0]
val = cell.value.decode('utf-8')

print('Getting PRED by row key.')
row = table.read_row(key, row_filter)
cell = row.cells[column_family_id][columnPRED][0]
val = cell.value.decode('utf-8')





### append some value to the variant AF characteristics
val_list = val.split(';')
val_list.append( 'PolyPhen=B' )
val_string = ';'.join(map(str, val_list))

rows = []
row = table.direct_row(key)
row.set_cell(column_family_id,
             columnPRED,
             val_string,
             timestamp=datetime.datetime.utcnow())
rows.append( row )
table.mutate_rows(rows)


print('Getting PRED by row key.')
row = table.read_row(key, row_filter)
cell = row.cells[column_family_id][columnPRED][0]
val = cell.value.decode('utf-8')






### DELETE the table
print('Deleting the {} table.'.format(tableID))
table.delete()






### this checks connection credentials for GCP
def implicit():
    from google.cloud import storage
    # If you don't specify credentials when constructing the client, the
    # client library will look for credentials in the environment.
    storage_client = storage.Client()
    # Make an authenticated API request
    buckets = list(storage_client.list_buckets())
    print(buckets)

















########################################################################################################
########################## here to use functions in other python script ################################
########################################################################################################
def stringizeDICT( chars_dict, field_delimiter = ';', key_delimiter = '=' ) :
    '''
        this takes a DICT of K=field : V=value of variant chars and returns it stringized with specified delimiters
    '''
    chars_list = []
    for k,v in chars_dict.items() :
        chars_list.append( '{0}{1}{2}'.format( k, key_delimiter, v ) )
    chars_string = field_delimiter.join( map( str, chars_list ))
    return( chars_string )

#############################################
#############################################
#############################################
from importlib import reload
import cloud_bigtable_functions
reload( cloud_bigtable_functions )

cloud_bigtable_functions.implicit()

cloud_bigtable_functions.cloudBigTable_listCOL( 'diagnosticaotr-00', 'diagnosticaotr-00-bigtable-00', 'test0' )

cloud_bigtable_functions.cloudBigTable_create( 'diagnosticaotr-00', 'diagnosticaotr-00-bigtable-00', 'test0', 'cf1' )


### try to dictionarize and insert variants
var1 = '1-5000-A-C'
var1AF = ({
          'gnomAD_AF' : 0.01,
          'gnomAD_exomes_AFR_AF' : 0.001,
          'gnomAD_genomes_AFR_AF' : 1E-5
})
var1PRED = ({
          'REVEL' : 0.17,
          'CADD' : 7,
          'polyphen2_HDIV_pred' : 'B'
})


var2 = '1-6000-A-T'
var2AF = ({
          'gnomAD_AF' : 0.001,
          'gnomAD_exomes_AFR_AF' : 1.45E-12,
          'gnomAD_genomes_AFR_AF' : 1E-3
})
var2PRED = ({
          'REVEL' : 0.89,
          'CADD' : 19,
          'polyphen2_HDIV_pred' : 'P'
})


var1AF_string = stringizeDICT( var1AF )
var1PRED_string = stringizeDICT( var1PRED )

var2AF_string = stringizeDICT( var2AF )
var2PRED_string = stringizeDICT( var2PRED )

var_rows_dict = ({
              var1 : {
                                'AF' : var1AF,
                                'PRED' : var1PRED
                              },
              var2 : {
                                'AF' : var2AF,
                                'PRED' : var2PRED
                              }
})


cloud_bigtable_functions.cloudBigTable_createCOL( 'diagnosticaotr-00', 'diagnosticaotr-00-bigtable-00', 'test0', 'AF' )

cloud_bigtable_functions.cloudBigTable_KEYinsert( 'diagnosticaotr-00', 'diagnosticaotr-00-bigtable-00', 'test0', var_rows_dict )

cloud_bigtable_functions.cloudBigTable_KEYupdate( 'diagnosticaotr-00', 'diagnosticaotr-00-bigtable-00', 'test0', var_rows_dict )

cloud_bigtable_functions.cloudBigTable_getRow( 'diagnosticaotr-00', 'diagnosticaotr-00-bigtable-00', 'test0', var1 )

cloud_bigtable_functions.cloudBigTable_getCell( 'diagnosticaotr-00', 'diagnosticaotr-00-bigtable-00', 'test0', var1, 'AF', column_family_ID )















### ENDc
