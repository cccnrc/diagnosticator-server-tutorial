#!/usr/bin/env python3

'''
    this is the script that allows you to generate the OMIM inheritance DB file (DB/OMIM/genemap2.extracted.tsv)
    starting from the OMIM genemap2.txt file downloaded directly from OMIM (DB/OMIM/genemap2.txt)
    you have to specify the:
        - INPUT file pathway (GENEMAP2)
        - OUTPUT file pathway (OUTPUT_FILE)
        - DEVELOPMENT: set it to 1 if you wanna see different logs (see code below)
'''

GENEMAP2='/home/enrico/columbia/diagnosticator-AWS/diagnosticator-local-simple-ALGORITHM-DEVELOPMENT-02-noMySQL-TUTORIAL-LABMEETING/DB/OMIM/genemap2.txt'
OUTPUT_FILE = '/home/enrico/columbia/diagnosticator-AWS/diagnosticator-local-simple-ALGORITHM-DEVELOPMENT-02-noMySQL-TUTORIAL-LABMEETING/DB/OMIM/genemap2.extracted.tsv'

DEVELOPMENT = 0     ### change this to 1 to activate LOGS


import csv
import re
def read_tsv_file_multiheader( FILE ):
  '''
    TSV file needs to have header
  '''
  # data structures to hold the data
  tsv_labels = []
  tsv_data = []
  with open( FILE, 'r') as tsv_in:
    tsv_reader = csv.reader(tsv_in, delimiter='\t')
    for record in tsv_reader:
      if ( record[0][0] == "#" ):
        tsv_labels.append(record)
      else:
        tsv_data.append(record)
  return( tsv_labels, tsv_data )

tsv_labels, tsv_data = read_tsv_file_multiheader( GENEMAP2 )
genemap2_header = tsv_labels[3]
genemap2_body = tsv_data


### create HEADER dict
HEADER_DICT = dict()
i = 0
for VALUE in genemap2_header:
    HEADER_DICT.update({ VALUE : i })
    i += 1

if DEVELOPMENT == 1:
    for k,v in HEADER_DICT.items():
        print( k + "\t" + str(v) )


'''
    this is the DICT to convert all inheritance possibilities to abbreviations
'''
INH_ABBREVIATION_DICT = ({
    "Autosomal recessive": "AR",
    "Autosomal dominant": "AD",
    "Digenic recessive": "DR",
    "Somatic mutation": "SMU",
    "Isolated cases": "IC",
    "Multifactorial": "MF",
    "Digenic dominant": "DD",
    "?Autosomal dominant": "AD",
    "Somatic mosaicism": "SMO",
    "Mitochondrial": "MT",
    "Pseudoautosomal dominant": "PD",
    "Pseudoautosomal recessive": "PR",
    "X-linked": "XL",
    "X-linked recessive": "XLR",
    "X-linked dominant": "XLD",
    "Y-linked": "YL"
})

PHENO_NAME_INITIAL_DICT = ({
    "[" : "non-disease",
    "{" : "susceptibility",
    "?" : "provisional"
})

### load disease for each gene
PATTERN = re.compile(r"\((\w*)\)")          ### between parenthesis
GENE_DICT = dict()
PARENTHESIS_UNIQUE = dict()
INH_UNIQUE = []
PHENO_NAME_INITIAL_UNIQUE = []
FINAL_FILE_LINES = []
i = 0
for LINE  in genemap2_body:
    i += 1
    if ( DEVELOPMENT == 1 ):
        if ( i > 100 ):
            break
    GENE_SYMBOL = LINE[ HEADER_DICT["Approved Gene Symbol"] ]
    GENE_PHENO = LINE[ HEADER_DICT["Phenotypes"] ]
    if GENE_SYMBOL:
        if GENE_PHENO:
            GENE_PHENO_STRING = GENE_PHENO
            ### if more than one phenotypes get all of them
            if ";" in GENE_PHENO:
                GENE_PHENO_LIST = GENE_PHENO.split(";")
                for PHENO in GENE_PHENO_LIST:
                    PARENTHESIS = PATTERN.findall(PHENO)
                    ### get last single digit indentified
                    for SYMBOL in PARENTHESIS:
                        if SYMBOL.isdigit() and len(SYMBOL) == 1:
                            DELIMITER = str( "(" + str(SYMBOL) + ")" )
                    ### spit PHENO_NAME based on LAST ocurrence of DELIMITER
                    PHENO_FIRST_LIST = PHENO.rsplit(DELIMITER, 1)
                    PHENO_NAME_LIST = PHENO_FIRST_LIST[0].split(",")
                    PHENO_NAME_LIST.pop()
                    PHENO_NAME = ",".join( map( str, PHENO_NAME_LIST )).lstrip().rstrip()
                    if PHENO_NAME:
                        PHENO_NAME_INITIAL = PHENO_NAME[0]
                        ### understand if nondisease, susceptibility etc (PHENO_NAME_INITIAL_DICT)
                        DISEASE_TYPE = "disease"
                        ### no changes to name if not a special case (PHENO_NAME_INITIAL_UNIQUE)
                        PHENO_NAME_CORRECT = PHENO_NAME
                        if PHENO_NAME_INITIAL in PHENO_NAME_INITIAL_DICT:
                            DISEASE_TYPE = PHENO_NAME_INITIAL_DICT[PHENO_NAME_INITIAL]
                            PHENO_NAME_CORRECT = PHENO_NAME.replace('{','').replace('}','').replace('[','').replace(']','').replace('?','')
                        ### collect chances for non-character-starting pheno names (susceptibility, RF, etc.)
                        if DEVELOPMENT == 1:
                            if not PHENO_NAME_INITIAL.isalpha():
                                if PHENO_NAME_INITIAL not in PHENO_NAME_INITIAL_UNIQUE:
                                    PHENO_NAME_INITIAL_UNIQUE.append(PHENO_NAME_INITIAL)
                                    print( PHENO_NAME )
                        PHENO_NUM = PHENO_FIRST_LIST[0].rsplit(",",1)[1].lstrip()
                        PHENO_INH = PHENO_FIRST_LIST[1].split(",")[1:]
                        PHENO_INH_CORR_LIST = []
                        ### convert inheritance to abbreviation
                        for INH in PHENO_INH:
                            INH_CORRECT = INH.lstrip().rstrip()
                            INH_ABBR = "NA"
                            if INH_CORRECT in INH_ABBREVIATION_DICT:
                                INH_ABBR = INH_ABBREVIATION_DICT[ INH_CORRECT ]
                            PHENO_INH_CORR_LIST.append(INH_ABBR)
                            ### print ALL unique chanches for INH
                            if DEVELOPMENT == 1 :
                                if (INH_CORRECT not in INH_UNIQUE):
                                    INH_UNIQUE.append( INH_CORRECT )
                        PHENO_INH_FINAL = ";".join( map( str, PHENO_INH_CORR_LIST )).lstrip().rstrip()
                    FINAL_FILE_LINES.append([GENE_SYMBOL, PHENO_NAME_CORRECT, DISEASE_TYPE, PHENO_NUM, PHENO_INH_FINAL])
            else:
                PHENO = GENE_PHENO
                PARENTHESIS = PATTERN.findall(PHENO)
                ### get last single digit indentified
                for SYMBOL in PARENTHESIS:
                    if SYMBOL.isdigit() and len(SYMBOL) == 1:
                        DELIMITER = str( "(" + str(SYMBOL) + ")" )
                ### spit PHENO_NAME based on LAST ocurrence of DELIMITER
                PHENO_FIRST_LIST = PHENO.rsplit(DELIMITER, 1)
                PHENO_NAME_LIST = PHENO_FIRST_LIST[0].split(",")
                PHENO_NAME_LIST.pop()
                PHENO_NAME = ",".join( map( str, PHENO_NAME_LIST )).lstrip().rstrip()
                if PHENO_NAME:
                    PHENO_NAME_INITIAL = PHENO_NAME[0]
                    ### understand if nondisease, susceptibility etc (PHENO_NAME_INITIAL_DICT)
                    DISEASE_TYPE = "disease"
                    ### no changes to name if not a special case (PHENO_NAME_INITIAL_UNIQUE)
                    PHENO_NAME_CORRECT = PHENO_NAME
                    if PHENO_NAME_INITIAL in PHENO_NAME_INITIAL_DICT:
                        DISEASE_TYPE = PHENO_NAME_INITIAL_DICT[PHENO_NAME_INITIAL]
                        PHENO_NAME_CORRECT = PHENO_NAME.replace('{','').replace('}','').replace('[','').replace(']','').replace('?','')
                    ### collect chances for non-character-starting pheno names (susceptibility, RF, etc.)
                    if DEVELOPMENT == 1:
                        if not PHENO_NAME_INITIAL.isalpha():
                            if PHENO_NAME_INITIAL not in PHENO_NAME_INITIAL_UNIQUE:
                                PHENO_NAME_INITIAL_UNIQUE.append(PHENO_NAME_INITIAL)
                                print( PHENO_NAME )
                    PHENO_NUM = PHENO_FIRST_LIST[0].rsplit(",",1)[1].lstrip()
                    PHENO_INH = PHENO_FIRST_LIST[1].split(",")[1:]
                    PHENO_INH_CORR_LIST = []
                    ### convert inheritance to abbreviation
                    for INH in PHENO_INH:
                        INH_CORRECT = INH.lstrip().rstrip()
                        INH_ABBR = "NA"
                        if INH_CORRECT in INH_ABBREVIATION_DICT:
                            INH_ABBR = INH_ABBREVIATION_DICT[ INH_CORRECT ]
                        PHENO_INH_CORR_LIST.append(INH_ABBR)
                        ### print ALL unique chanches for INH
                        if DEVELOPMENT == 1 :
                            if (INH_CORRECT not in INH_UNIQUE):
                                INH_UNIQUE.append( INH_CORRECT )
                    PHENO_INH_FINAL = ";".join( map( str, PHENO_INH_CORR_LIST )).lstrip().rstrip()
                FINAL_FILE_LINES.append([GENE_SYMBOL, PHENO_NAME_CORRECT, DISEASE_TYPE, PHENO_NUM, PHENO_INH_FINAL])



HEADER = [ "#GENE", "DISEASE", "TYPE", "ID", "INH" ]
with open(OUTPUT_FILE, 'w') as OF:
    OF.write( "\t".join( map( str, HEADER )) )
    OF.write("\n")
    for LINE in FINAL_FILE_LINES:
        OF.write( "\t".join( map( str, LINE )) )
        OF.write("\n")



if DEVELOPMENT == 1:
    for VALUE in PHENO_NAME_INITIAL_UNIQUE:
        print( VALUE )
    '''
    for VALUE in INH_UNIQUE:
        print( "\"" +  VALUE + "\": \"\","  )
    '''
#print(GENE_DICT)
























### ENDc
