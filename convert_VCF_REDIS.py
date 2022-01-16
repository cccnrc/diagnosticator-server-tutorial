#!/usr/bin/env python3

import os
import gc

# ASILO_DIR = '/var/lib/docker/volumes/DX-ASILO-VOLUME/_data/analisi_result'


def VCF2REDIS( ASILO_DIR ) :

    ### merge VAR files
    VIN_FILES = os.listdir( os.path.join( ASILO_DIR, 'var_results' ) )
    VIN_F_CONCATENATED = []
    for VIN_FILE in VIN_FILES:
        with open( os.path.join( ASILO_DIR, 'var_results', VIN_FILE ), 'r') as VIN_F:
            for LINE in VIN_F:
                VIN_F_CONCATENATED.append(LINE)

    ### merge SAMPLE files
    VPIN_FILES = os.listdir( os.path.join( ASILO_DIR, 'var_pz_results' ) )
    VPIN_F_CONCATENATED = []
    for VPIN_FILE in VPIN_FILES:
        with open( os.path.join( ASILO_DIR, 'var_pz_results', VPIN_FILE ), 'r') as VPIN_F:
            for LINE in VPIN_F:
                VPIN_F_CONCATENATED.append(LINE)

    ### GENE file
    VGIN = os.path.join( ASILO_DIR, 'prova.gene' )

    VAR_SUBDICT = ({
        "chr" : "CHARS",
        "pos" : "CHARS",
        "ref" : "CHARS",
        "alt" : "CHARS",
        "Allele" : "CHARS",
        "SYMBOL" : "CHARS",
        "Gene" : "CHARS",
        "Feature_type" : "CHARS",
        "Feature" : "CHARS",
        "BIOTYPE" : "CHARS",
        "EXON" : "CHARS",
        "HGVSc" : "CHARS",
        "HGVSp" : "CHARS",
        "cDNA_position" : "CHARS",
        "CDS_position" : "CHARS",
        "Protein_position" : "CHARS",
        "Amino_acids" : "CHARS",
        "Codons" : "CHARS",
        "Existing_variation" : "CHARS",
        "STRAND" : "CHARS",
        "VARIANT_CLASS" : "CHARS",
        "SYMBOL_SOURCE" : "CHARS",
        "HGNC_ID" : "CHARS",
        "CANONICAL" : "CHARS",
        "CCDS" : "CHARS",
        "ENSP" : "CHARS",
        "SWISSPROT" : "CHARS",
        "TREMBL" : "CHARS",
        "UNIPARC" : "CHARS",
        "GENE_PHENO" : "CHARS",
        "DOMAINS" : "CHARS",
        "MutationAssessor_pred" : "CHARS",
        "MutationAssessor_score" : "CHARS",
        "genename" : "CHARS",
        "Consequence" : "PRED",
        "IMPACT" : "PRED",
        "Polyphen2_HDIV_pred_corrected" : "PRED",
        "Polyphen2_HVAR_pred_corrected" : "PRED",
        "SIFT_corrected" : "PRED",
        "REVEL_score_corrected" : "PRED",
        "CADD_PHRED_corrected" : "PRED",
        "GERP++_RS_corrected" : "PRED",
        "LRT_pred_corrected" : "PRED",
        "FATHMM_pred_corrected" : "PRED",
        "MutationTaster_pred_corrected" : "PRED",
        "SIFT" : "PRED",
        "PolyPhen" : "PRED",
        "CADD_PHRED" : "PRED",
        "CADD_RAW" : "PRED",
        "CADD_phred" : "PRED",
        "FATHMM_pred" : "PRED",
        "FATHMM_score" : "PRED",
        "GERP++_RS" : "PRED",
        "LRT_pred" : "PRED",
        "LRT_score" : "PRED",
        "MutationTaster_pred" : "PRED",
        "MutationTaster_score" : "PRED",
        "ACMG" : "ACMG",
        "pvs1" : "ACMG",
        "ps1" : "ACMG",
        "ps2" : "ACMG",
        "ps3" : "ACMG",
        "ps4" : "ACMG",
        "pm1" : "ACMG",
        "pm2" : "ACMG",
        "pm3" : "ACMG",
        "pm4" : "ACMG",
        "pm5" : "ACMG",
        "pm6" : "ACMG",
        "pp1" : "ACMG",
        "pp2" : "ACMG",
        "pp3" : "ACMG",
        "pp4" : "ACMG",
        "pp5" : "ACMG",
        "ba1" : "ACMG",
        "bp1" : "ACMG",
        "bp2" : "ACMG",
        "bp3" : "ACMG",
        "bp4" : "ACMG",
        "bp5" : "ACMG",
        "bp6" : "ACMG",
        "bp7" : "ACMG",
        "bs1" : "ACMG",
        "bs2" : "ACMG",
        "bs3" : "ACMG",
        "bs4" : "ACMG"
    })

    SUBDICT_AF_PREFIX = ([
        'uk10k',
        '1000gp3',
        'exac',
        'gnomad'
    ])

    SUBDICT_CLINVAR_PREFIX = ([
        'clinvar'
    ])

    VAR_FIELD_CONVERSION = ({
        'gene_name_correct' : 'genename',
        'hgvs_c' : 'HGVSc',
        'hgvs_p' : 'HGVSp',
        'rs_name' : 'Existing_variation',
        'var_type' : 'VARIANT_CLASS'
    })

    ACMG_SUBCLASS_STRENGTH_DICT = ({
        'pvs' : 'VS',
        'ps' : 'S',
        'pm' : 'M',
        'pp' : 'P',
        'ba' : 'BA',
        'bs' : 'BS',
        'bp' : 'BP',
        'NA' : 'NA'
    })


    VARIANTS_DICT = dict()
    LINE_COUNT = 0

    for LINE in VIN_F_CONCATENATED:
        VAR_DICT = dict()
        INFO = LINE.split('\t')[7].rstrip('\n').split(';')
        for F in INFO:
            if (F != "") :
                FK, FV = F.split('=', 1)
                if ( FK not in VAR_DICT ):
                    ### convert name if in apposite VAR_FIELD_CONVERSION dictionary
                    if ( FK in VAR_FIELD_CONVERSION ):
                        VAR_DICT.update({ VAR_FIELD_CONVERSION[FK] : FV })
                    else:
                        VAR_DICT.update({ FK : FV })
                else:
                    VAR_DICT[FK] = FV
        ### arrange VAR DICT to convert names
        VAR_CHR, VAR_POS, VAR_REF, VAR_ALT = VAR_DICT['var_name'].split('-')
        VAR_DICT.update({ 'chr' : VAR_CHR })
        VAR_DICT.update({ 'pos' : VAR_POS })
        VAR_DICT.update({ 'ref' : VAR_REF })
        VAR_DICT.update({ 'alt' : VAR_ALT })
        ### extract SAMPLE dict
        SAMPLES_DICT = dict()
        SINGLE_HET_LIST = []
        SINGLE_HET = VAR_DICT['pz_single_het']
        if SINGLE_HET != "NA" and SINGLE_HET != "":
            if ',' in SINGLE_HET:
              SINGLE_HET_LIST = SINGLE_HET.split(',')
            else:
              SINGLE_HET_LIST = [ SINGLE_HET ]
        COMP_HET = VAR_DICT['pz_comp_het']
        COMP_HET_LIST = []
        if COMP_HET != "NA" and COMP_HET != "":
            if '>' in COMP_HET:
                if '!' in COMP_HET:
                    COMP_HET_LIST = [ x.split('>',1)[0] for x in COMP_HET.split('!') ]
                else:
                    COMP_HET_LIST = [ COMP_HET.split('>',1)[0] ]
            elif ',' in COMP_HET:
              COMP_HET_LIST = COMP_HET.split(',')
            else:
              COMP_HET_LIST = [ COMP_HET ]
        HOM_LIST = []
        HOM = VAR_DICT['pz_hom']
        if HOM != "NA" and HOM != "":
            if ',' in HOM:
              HOM_LIST = HOM.split(',')
            else:
              HOM_LIST = [ HOM ]
        for SAMPLE in SINGLE_HET_LIST+COMP_HET_LIST:
            if SAMPLE not in SAMPLES_DICT:
                SAMPLES_DICT.update({ SAMPLE : 'het' })
        for SAMPLE in HOM_LIST:
            if SAMPLE not in SAMPLES_DICT:
                SAMPLES_DICT.update({ SAMPLE : 'hom' })
        ### divide VAR_DICT in subdicts
        VAR_DICT_FINAL = { 'SAMPLES' : SAMPLES_DICT }
        ### extract ACMG dict
        if 'ACMG_categories' in VAR_DICT:
            if VAR_DICT['ACMG_categories'] != "NA" :
                CATEGORIES_LIST = VAR_DICT['ACMG_categories'].split(',')
                for ACMG_CAT in CATEGORIES_LIST:
                    CAT_MODIFIED = ACMG_CAT.lower().split('_',1)[0]
                    for KC,KV in ACMG_SUBCLASS_STRENGTH_DICT.items():
                        if CAT_MODIFIED.startswith(KC) :
                            CAT_MODIFIED_STRENGTH = ACMG_SUBCLASS_STRENGTH_DICT[KC]
                    if CAT_MODIFIED in VAR_SUBDICT:
                        if ( VAR_SUBDICT[CAT_MODIFIED] in VAR_DICT_FINAL ):
                            VAR_DICT_FINAL[VAR_SUBDICT[CAT_MODIFIED]].update({ CAT_MODIFIED : CAT_MODIFIED_STRENGTH })
                        else:
                            VAR_DICT_FINAL.update({ VAR_SUBDICT[CAT_MODIFIED] : { CAT_MODIFIED : CAT_MODIFIED_STRENGTH }})
        ### insert the rest in VAR_DICT_FINAL
        for VDK, VDV in VAR_DICT.items() :
            if ( VDK in VAR_SUBDICT ):
                if ( VAR_SUBDICT[VDK] in VAR_DICT_FINAL ):
                    VAR_DICT_FINAL[VAR_SUBDICT[VDK]].update({ VDK : VDV })
                else:
                    VAR_DICT_FINAL.update({ VAR_SUBDICT[VDK] : { VDK : VDV }})
            else:
                for PREFIX in SUBDICT_AF_PREFIX :
                    if ( VDK.startswith( PREFIX ) ) :
                        if ( 'AF' in VAR_DICT_FINAL ):
                            VAR_DICT_FINAL['AF'].update({ VDK : VDV })
                        else:
                            VAR_DICT_FINAL.update({ 'AF' : { VDK : VDV }})
                for PREFIX in SUBDICT_CLINVAR_PREFIX :
                    if ( VDK.startswith( PREFIX ) ) :
                        if ( 'CLINVAR' in VAR_DICT_FINAL ):
                            VAR_DICT_FINAL['CLINVAR'].update({ VDK : VDV })
                        else:
                            VAR_DICT_FINAL.update({ 'CLINVAR' : { VDK : VDV }})
        ### add the final dict in the variants one
        VARIANTS_DICT.update({ VAR_DICT['var_name'] : VAR_DICT_FINAL })
        LINE_COUNT += 1

    del VIN_F_CONCATENATED
    gc.collect()

    SAMPLE_FIELD_CONVERSION = ({
        'ad_alt' : 'AD_ALT',
        'ad_ref' : 'AD_REF',
        'dp_bin' : 'DP',
        'filter' : 'FILTER',
        'gq' : 'GQ',
        'gt' : 'convGT',
        'qual' : 'QUAL'
    })

    ### obtain SAMPLE DICT
    LINE_COUNT = 0
    SAMPLES_OVERALL_DICT = dict()
    for LINE in VPIN_F_CONCATENATED:
        SAMPLE_OVERALL_DICT = dict()
        LINE_SPLITTED = LINE.rstrip('\n').split('\t')
        VAR_NAME = "{0}-{1}-{2}-{3}".format( LINE_SPLITTED[0], LINE_SPLITTED[1], LINE_SPLITTED[3], LINE_SPLITTED[4] )
        INFO = LINE_SPLITTED[7].rstrip('\n').split(';')
        for F in INFO:
            if F != "" :
                if '=' in F:
                    FK,FV = F.split('=')
                    SAMPLE_OVERALL_DICT.update({ FK : FV })
        SAMPLE_NAME = SAMPLE_OVERALL_DICT['pz_name']
        if SAMPLE_NAME in SAMPLES_OVERALL_DICT:
            if 'varGT' in SAMPLES_OVERALL_DICT[SAMPLE_NAME]:
                SAMPLES_OVERALL_DICT[SAMPLE_NAME]['varGT'].update({ VAR_NAME : SAMPLE_OVERALL_DICT})
            else:
                SAMPLES_OVERALL_DICT[SAMPLE_NAME].update({ 'varGT' : { VAR_NAME : SAMPLE_OVERALL_DICT }})
        else:
            SAMPLES_OVERALL_DICT.update({ SAMPLE_NAME : { 'varGT' : { VAR_NAME : SAMPLE_OVERALL_DICT }}})
        LINE_COUNT += 1


    del VPIN_F_CONCATENATED
    gc.collect()




    ### obtain GENE DICT
    LINE_COUNT = 0
    GENES_DICT = dict()
    with open( VGIN, 'r' ) as IFILE:
        if ( 0 == 0 ) :
            for LINE in IFILE:
                GENE_DICT = dict()
                GENE_LINE = LINE.split('\t')
                GENE_NAME = GENE_LINE[0]
                GENE_INFO = GENE_LINE[1].split(';')
                GENE_VARS_PATHO = []
                for G in GENE_INFO:
                    if G != "":
                        if '=' in G:
                            GK, GV = G.split('=')
                            if GK == 'gene_var_patho':
                                for VAR in GV.split(','):
                                    GENE_VARS_PATHO.append( VAR )
                                    if VAR in VARIANTS_DICT:
                                        VAR_SAMPLES = list(VARIANTS_DICT[ VAR ][ 'SAMPLES' ].keys())
                                    else:
                                        VAR_SAMPLES = []
                                    if 'var' in GENE_DICT:
                                        GENE_DICT['var'].update({ VAR : list(VAR_SAMPLES) })
                                    else:
                                        GENE_DICT.update({ 'var' : { VAR : list(VAR_SAMPLES) }})
                GENES_DICT.update({ GENE_NAME : GENE_DICT })
                LINE_COUNT += 1


    return( VARIANTS_DICT, SAMPLES_OVERALL_DICT, GENES_DICT )





































###ENDc
