#! /usr/bin/env python3.8

import sys
import weakref


# from memory_profiler import profile
from datetime import datetime, timedelta

IN = "/home/enrico/Dropbox/NY/asilo_variant/inputs/A13661.germline.head2k.VEPoutput.norm.vcf"
IN = "/home/enrico/Dropbox/NY/asilo_variant/inputs/merged.idter_M.norm.PASS.filtered.head100.VEPoutput.norm.vcf"
IN = "/home/enrico/Dropbox/NY/asilo_variant/inputs/merged.idter_M.norm.PASS.filtered.head1k.VEPoutput.norm.vcf"


#####################################################
############# VAR-Samples collection ################
#####################################################
'''
    here take consideration of assumed values
'''
lastNONsampleHcolumnINDEX = 8                   # last column header index non pertaining to a sample
uselessGT = [ "./.", ".|.", "0/0", "0|0" ]      # here exluding HOM REF variants too

class iterator(type):
    def __iter__(self):
        return self.classiter()

class VCFh:
    '''
        this stores VCF header and relative column numbers and chars
    '''
    __metaclass__ = iterator
    by_id = {}

    def __init__(self, id, column_number):
        self.id = id
        self.by_id[id] = self
        # self.by_id[id] = weakref.ref(self)
        self.column_number = column_number

    @classmethod
    def classiter(cls):
        return iter(cls.by_id.values())
        # return (i for i in (i() for i in cls.by_id.values()) if i is not None)

class SAMPLEh:
    '''
        this stores VCF header relative to samples GT
    '''
    __metaclass__ = iterator
    by_id = {}

    def __init__(self, id, column_number):
        self.id = id
        self.by_id[id] = self
        # self.by_id[id] = weakref.ref(self)
        self.column_number = column_number

    @classmethod
    def classiter(cls):
        return iter(cls.by_id.values())
        # return (i for i in (i() for i in cls.by_id.values()) if i is not None)


class VEPh:
    '''
        this stores VEP header and relative column numbers and chars
    '''
    __metaclass__ = iterator
    by_id = {}

    def __init__(self, id, column_number):
        self.id = id
        self.by_id[id] = self
        # self.by_id[id] = weakref.ref(self)
        self.column_number = column_number

    @classmethod
    def classiter(cls):
        return iter(cls.by_id.values())
        # return (i for i in (i() for i in cls.by_id.values()) if i is not None)

class Variant:
    '''
        this stores VEP body and relative chars
    '''
    __metaclass__ = iterator
    by_id = {}

    def __init__( self, id, VARchars_dict ):
        self.id = id
        self.by_id[id] = self
        # self.by_id[id] = weakref.ref(self)
        self.rsID = VARchars_dict['ID']
        self.qual = VARchars_dict['QUAL']
        self.filter = VARchars_dict['FILTER']
        self.info = VARchars_dict['INFO']
        self.GTheader = VARchars_dict['FORMAT']
        ### to populate
        self.info_dict = {}
        self.infoVEP_dict = {}
        self.infoACMGpatho_dict = {}
        self.infoACMGbenign_dict = {}
        self.infoACMGpatho_overall_dict = ({
                    'VS' : 0,
                    'S' : 0,
                    'M' : 0,
                    'P' : 0
        })
        self.infoACMGbenign_overall_dict = ({
                    'A' : 0,
                    'S' : 0,
                    'P' : 0
        })
        self.final_dict = {}
        self.sample_dict = {}

    @classmethod
    def classiter(cls):
        return iter(cls.by_id.values())
        # return (i for i in (i() for i in cls.by_id.values()) if i is not None)

    ### this is to convert INFO string into DICT easly accessible
    def dictionarizeINFO( self ) :
        info_dict = {}
        if ';' in self.info :
            info_splitted = self.info.split(';')
            for f in info_splitted:
                if '=' in f:
                    k,v = f.split('=')
                    info_dict.update({ k : v })
                else :
                    info_dict.update({ k : 'NA' })
        self.info_dict = info_dict

    ### this is to convert VEP string into DICT easly accessible
    def dictionarizeVEP( self ) :
        ### dictionarize VEPh to easier access
        vepH_dict = {}
        for v in VEPh.classiter():
            vepH_dict.update({ v.column_number : v.id })
        ### loop over VEPinfo field of the var
        vep_dict = {}
        if 'CSQ' in self.info_dict :
            if '|' in self.info_dict['CSQ'] :
                vep_info_splitted = self.info_dict['CSQ'].split('|')
                ### check same length than header
                if len( vep_info_splitted ) != len( vepH_dict ) :
                    print('  !!! ATTENTION !!! --> VEP header DICT length is different from VEP info field ' + len( vep_info_splitted ) + ' != ' + len( vepH_dict ) + ' !!! ')
                for i,f in enumerate( vep_info_splitted ):
                    vep_dict.update({ vepH_dict[i] : f })
        self.infoVEP_dict = vep_dict

    ### add a VEP dict entry
    def addVEPdict_entry( self, criteria, value ):
        self.infoVEP_dict.update({ criteria : value })

    ### add a class to ACMG Variant dict
    def addACMGpatho_criteria( self, criteria, value ):
        self.infoACMGpatho_dict.update({ criteria : value })
    def addACMGbenign_criteria( self, criteria, value ):
        self.infoACMGbenign_dict.update({ criteria : value })

    ### this is to collect all valuable variant characteristics in a single DICT in order to pass it to the DB
    def finalVARdict( self ):
        '''
            NB: it is important to run all filtering BEFORE running this function!!!
        '''
        chr,pos,ref,alt = self.id.split('-')
        self.final_dict.update({ 'chr' : chr })
        self.final_dict.update({ 'pos' : pos })
        self.final_dict.update({ 'ref' : ref })
        self.final_dict.update({ 'alt' : alt })
        for k,v in self.infoVEP_dict.items() :
            if k not in self.final_dict:
                self.final_dict.update({ k : v })
        if self.infoACMGpatho_dict:
            for k,v in self.infoACMGpatho_dict.items() :
                if k not in self.final_dict:
                    self.final_dict.update({ k : v })
        if self.infoACMGbenign_dict:
            for k,v in self.infoACMGbenign_dict.items() :
                if k not in self.final_dict:
                    self.final_dict.update({ k : v })
        if self.infoACMGpatho_overall_dict:
            for k,v in self.infoACMGpatho_overall_dict.items() :
                if k not in self.final_dict:
                    self.final_dict.update({ k : v })
        if self.infoACMGbenign_overall_dict:
            for k,v in self.infoACMGbenign_overall_dict.items() :
                if k not in self.final_dict:
                    self.final_dict.update({ k : v })
        if self.sample_dict:
            for k,v in self.sample_dict.items() :
                if k not in self.final_dict:
                    self.final_dict.update({ k : v })

    def addSample( self, sampleID, varZig ):
        '''
            this allows to store samples and relative variant zygosity
        '''
        if sampleID not in self.sample_dict :
            self.sample_dict.update({ sampleID : varZig })
        else:
            self.sample_dict[ sampleID ] = varZig

### adapt and uniform GT field value
def convertGT( gt ):
    if '|' in gt:
        gt = gt.replace('|','/')
    ### convert GT in letters and add to DICT
    if gt == '0/1' or gt == '1/0' :
        newGT = 'het'
    elif gt == '1/1' :
        newGT = 'hom'
    else :
        newGT = 'NA'
    return( newGT )


class Sample:
    '''
        this stores samples GT and relative chars
    '''
    __metaclass__ = iterator
    by_id = {}

    def __init__( self, id ):
        self.id = id
        self.by_id[id] = self
        # self.by_id[id] = weakref.ref(self)
        self.varGT_dict = {}
        self.comphet_dict = {}

    @classmethod
    def classiter(cls):
        return iter(cls.by_id.values())
        # return (i for i in (i() for i in cls.by_id.values()) if i is not None)

    ### this add each VAR and relative GT for each sample
    def addVarGT( self, varID, GTbody ):
        self.varGT_dict.update({ varID : GTbody })

    ### this creates a DICT with GT chars of each patient replacing collapsed varGT_dictGT value with a DICT with each K:V of GT
    def splitGT( self, varID, GTheader_dict ):
        varGT = self.varGT_dict[varID]
        splitted_varGT_dict = {}
        for i,g in enumerate( varGT.split(':') ):
            header = GTheader_dict[i]
            value = g
            splitted_varGT_dict.update({ header : value })
        ### add character GT to DICT
        if 'GT' in splitted_varGT_dict:
            splitted_varGT_dict.update({ 'convGT' : convertGT(splitted_varGT_dict['GT']) })
        self.varGT_dict[ varID ] = splitted_varGT_dict



class Gene:
    '''
        this stores genes and relative variants
    '''
    __metaclass__ = iterator
    by_id = {}

    def __init__( self, id ):
        self.id = id
        self.by_id[id] = self
        # self.by_id[id] = weakref.ref(self)
        self.varSample_dict = {}

    @classmethod
    def classiter(cls):
        return iter(cls.by_id.values())
        # return (i for i in (i() for i in cls.by_id.values()) if i is not None)

    def addGeneVarSample( self, varID, sampleID ):
        '''
            this is intended to store variants harbored by each gene and in which samples
        '''
        if varID not in self.varSample_dict:
            self.varSample_dict.update({ varID : [ sampleID ] })
        else:
            if sampleID not in self.varSample_dict[ varID ]:
                self.varSample_dict[ varID ].append( sampleID )



class Dictionary:
    '''
        this is intended to store the dict in wich each V is a Class object
        in order to have them always disposable with no need to pass the from a function to the other
    '''
    def __init__ (self) :
        self.var_dict = {}
        self.sample_dict = {}
        self.gene_dict = {}
        self.VEPh_dict = {}
        ### this is the ine I will use to pull variants to cloudBigTable
        self.variantClass_dict = {}
        ### and this is necessary to create the varClass_dict one
        self.column_families_dict = {}
        ### this is the Sample DICT I will use to pull samples to cloudBigTable
        self.sampleClass_dict = {}
        ### this is the Gene DICT I will use to pull genes to cloudBigTable
        self.geneClass_dict = {}

    def assignSampleDict( self, sample_dict ):
        '''
            I need this just to be sure to create the column_families_dict AFTER sample_dict is created
        '''
        self.sample_dict = sample_dict
        self.column_families_dict = createColumnFamiliesDict( sample_dict )

### I immediately initialize master_dict object of class Dictionary so I have it for ALL future functions with no nedd to pass it as arg
master_dict = Dictionary()





#######################################################################
##########################   FUNCTIONS   ##############################
#######################################################################
def print_dict( dictionary ):
    '''
        this is just an utility to simplify DICT STDOUT analysis
    '''
    for k,v in dictionary.items() :
        print( "{0}  =  {1}".format( k, v ) )


### convert list to string with a delimiter between elements
def list2string( l, delimiter ):
    s = delimiter.join(map(str, l))
    return( s )




##################################################
################# time LOGS fun ##################
##################################################
class Time:
    def __init__( self ):
        self.start = datetime.now()
    def difference( self ):
        time_elapsed_chunk = datetime.now() - self.start
        return( time_elapsed_chunk )

def startLOGprinter( sentence ):
    print()
    startTime = datetime.now()
    print( "{0}. {1} ...".format( startTime.strftime("%m/%d/%Y %H:%M:%S"), sentence ) )
    return( startTime )

def endLOGprinter( start_time ):
    time_elapsed = datetime.now() - start_time
    print( '  - {}'.format( stringizeTimedelta( formatTimedelta(time_elapsed), 3 ) ) )
    print()

def formatTimedelta( td ):
    '''
        this takes a timedelta object and converts it in its component (H,M,S,ms)
    '''
    td_dict = {}
    days = td.days
    hours, remainder = divmod(td.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    # If you want to take into account fractions of a second
    seconds += td.microseconds / 1e6
    td_dict.update({
                        'days' : days,
                        'hours' : hours,
                        'minutes' : minutes,
                        'seconds' : seconds
    })
    return( td_dict )

def stringizeTimedelta( td_dict, round_N = 2 ):
    '''
        this convert td_dict of formatTimedelta to a srtring with only present values
    '''
    stringOUT = "took: "
    addCounter = 0
    for k,v in td_dict.items():
        if v > 0:
            if addCounter > 0:
                stringOUT += ', {0} {1}'.format( round(v, round_N), k )
            else:
                stringOUT += '{0} {1}'.format( round(v, round_N), k )
            addCounter += 1
    return( stringOUT )



def chunkLOGprinter( i, variable_name, variableN, time_obj, chunkN = 100 ):
    '''
        this creates a printer that print periodically timestamp for specified chunk N
    '''
    if i > 0 :
        if i % chunkN == 0:
            print( '    - analyzed {0} {1}s'.format( i, variable_name ) )
            time_elapsed_chunk = time_obj.difference()
            print( '      - chunk {}'.format( stringizeTimedelta(formatTimedelta(time_elapsed_chunk)) ) )
            time_obj = Time()
        elif i == variableN-1 :
            print( '    - analyzed {0} {1}s'.format( i+1, variable_name ) )
            time_elapsed_chunk = time_obj.difference()
            print( '      - last chunk {}'.format( stringizeTimedelta( formatTimedelta(time_elapsed_chunk), 5 ) ) )
            time_obj = Time()
    return( time_obj )

def logPrinter( function ):
    '''
        wrapper function to print time logs of the function itself before and after
    '''
    def wrap(*args, **kwargs):
        start = startLOGprinter( function.__name__ )
        result = function(*args, **kwargs)
        endLOGprinter( start )
        return( result )
    return( wrap )


def logPrinterChunk_dict( loop_element, function, variable_name ):
    '''
        wrapper function to print time logs of the function every chunk (whose length is defined through chunkN)
        passing a DICT as arg to loop over
    '''
    loopN  = len( loop_element )
    # print( "looping over {0} ({2}) callig function {1}".format( loop_element, function, loopN ) )
    time_obj = Time()
    for i,v in enumerate( loop_element ):
        # print( "  - iter num {0}: {1}".format( i, v ) )
        time_obj = chunkLOGprinter( i, variable_name, loopN, time_obj, chunkN = 100 )
        function( loop_element[v] )



#######################################################



### take VCF header
# @profile
@logPrinter
def readVCFh( vcf_file ):
    name_dict = {}
    sample_dict = {}
    for line in open( vcf_file ):
        ### take header
        if ( line[0] == "#" ) :
            ### create a header DICT for VEP output
            if ( line[0:14] == "##INFO=<ID=CSQ" ) :
                s1,s2 = line.split(':')
                ss2 = s2.rstrip().lstrip().split('\"')[0]
                for i,s in enumerate(ss2.split('|')) :
                    name_dict.update({ i : s })
                    name_dict[i] = VEPh( s, i )
                    if s not in master_dict.VEPh_dict:
                        master_dict.VEPh_dict.update({ s : name_dict[i] })
                    else:
                        master_dict.VEPh_dict[ s ] = name_dict[i]
            elif ( line[0:6] == "#CHROM" ) :
                line_splitted = line.rstrip('\n').lstrip().split('\t')
                for i,s in enumerate(line_splitted) :
                    name_dict.update({ i : s })
                    if (i > lastNONsampleHcolumnINDEX) :
                        name_dict[i] = SAMPLEh( s, i )
                        name_dict[i] = Sample( s )
                        ### store in a DICT with K=Sample_name : V=SampleClass_object
                        sample_dict.update({ s : name_dict[i] })
                    else :
                        name_dict[i] = VCFh( s, i )
    master_dict.assignSampleDict( sample_dict )

### take VCF body
@logPrinter
def readVCFb( vcf_file ):
    body_dict = {}
    sample_dict = {}
    ### convert VCFh class in DICT easily accessible
    vcfH_dict = {}
    for v in VCFh.classiter():
        vcfH_dict.update({ v.column_number : v.id })
    ### convert SAMPLEh class in DICT easily accessible
    sampleH_dict = {}
    for s in SAMPLEh.classiter():
        sampleH_dict.update({ s.column_number : s.id })

    ### loop over file
    i = 0
    for line in open( vcf_file ):
        VARchars_dict = {}
        ### if NOT header
        if ( line[0] != "#" ) :
            line_splitted = line.rstrip('\n').lstrip().split('\t')
            ### open a loop enumerating each column
            for x,c in enumerate( line_splitted[0:lastNONsampleHcolumnINDEX+1] ) :
                ### if VAR chars
                if x in vcfH_dict :
                    ### add in DICT the column header name : column value
                    VARchars_dict.update({ vcfH_dict[x] : c })
            ### push VAR with its chars in Variant class
            varID = list2string( [ VARchars_dict['#CHROM'], VARchars_dict['POS'], VARchars_dict['REF'], VARchars_dict['ALT'] ], '-' )
            body_dict.update({ varID : i })
            body_dict[varID] = Variant( varID, VARchars_dict )
            ### convert VAR info and VEP info string to DICT
            body_dict[varID].dictionarizeINFO()
            body_dict[varID].dictionarizeVEP()
            ### save format and convert to DICT to pass to Sample class to explode VAR GT correctly
            format = VARchars_dict['FORMAT']
            format_dict = {}
            for y,f in enumerate(format.split(':')):
                format_dict.update({ y : f })
            ### then add variants chars to sample
            for x,c in enumerate( line_splitted[lastNONsampleHcolumnINDEX+1:] ) :
                ### if empty GT skip
                if c[0:3] in uselessGT :
                    continue
                ### start loop over samples --> this may be improved in performance with some direct access to class element
                for s in Sample.classiter():
                    ### add each VAR GT chars to relative Sample object
                    if s.id == sampleH_dict[x + lastNONsampleHcolumnINDEX+1] :
                        s.addVarGT( varID, c )
                        s.splitGT( varID, format_dict )
            i += 1
    master_dict.var_dict = body_dict

### call together
def readVCF( vcf_file, print_time ):
    readVCFh( vcf_file )
    readVCFb( vcf_file )






#####################################################
############## single VAR filtering #################
#####################################################
pvs1_genes_file = "variant_dependencies/PVS1.LOF.genes.hg19"
ba1Exceptions_file = "variant_dependencies/clingen_BA1_exception.list"
clinvarHGVSp = "variant_dependencies/genefile_hgvsp_patho_miss_REV.txt"
#clinvarHGVSp = "/tmp/genefile_hgvsp_patho_miss_REV.FAKE.txt"
hotspotUCSC_file = "variant_dependencies/ucsc.exons.patho_REV.hotspot.txt"
omimInhMode_file = "variant_dependencies/all_omim_genes.inh_mode.tsv"
missenseGenes_file = "variant_dependencies/clinvar_pp2_genes.txt"
genesBS1_file = "variant_dependencies/clinvar_20200203_bs1.tsv"



### this take a one-column file and convert into a list
def file2list( file ):
    l = []
    for line in open( file ):
        l.append( line.rstrip('\n').lstrip() )
    ### remove empty entries
    l = list(filter(None, l))
    return( l )

def file2dict( file, delimiter = "\t", colnames = None ):
    '''
        this takes a TSV file and create a DICT with K=1st_column and V=DICT with K=2nd_colname : V=2nd_col_values etc
          - this assumes that the 1st COL in NOT repeated !!!
    '''
    file_dictionary = {}

    ### if colnames not given are assigned col1, col2, col3, etc.
    if not colnames:
        colnames_list = []
        i=0
        for line in open( file ):
            line_splitted = line.rstrip('\n').lstrip().split( delimiter )
            if i == 0:
                for x,v in enumerate( line_splitted ):
                    colnames_list.append( "col" + str(x) )
            else:
                break
            i += 1
    ### if colnames given are assigned
    else:
        colnames_list = colnames

    ### open actual file
    for line in open( file ):
        line_splitted = line.rstrip('\n').lstrip().split( delimiter )
        for i,v in enumerate( line_splitted ):
            if i == 0:
                k = v
                file_dictionary.update({ k : {} })
            else:
                file_dictionary[k].update({ colnames_list[i] : v })

    return( file_dictionary )


def file2array( file, delimiter = "\t" ):
    '''
        this returns an array of arrays of the file lines
    '''
    l = []
    for line in open( hotspotUCSC_file ):
        line_splitted = line.rstrip('\n').lstrip().split('\t')
        l.append(line_splitted)
    return( l )

def splice_filter( variant ):
    '''
        this function checks if the variant has some splicing noticeablo effect
    '''
    splice_consequences = ([
                              "splice_acceptor_variant",
                              "splice_donor_variant"
    ])
    varConsequence = variant.infoVEP_dict['Consequence']
    if varConsequence in splice_consequences:
        return( True )
    return( False )


def splicePatho_filter( variant ):
    '''
        this function checks if the variant is a predicted splicing altering variant
    '''
    if splice_filter( variant ):
        varADA = extractPredNUM( variant, 'ada_score', 0.59 )
        if ( varADA ) == 'P':
            return( True )
        varRF = extractPredNUM( variant, 'rf_score', 0.59 )
        if ( varRF ) == 'P':
            return( True )
    return( False )


def lof_strong_filter( variant ) :
    '''
        check LOF STRONG Consequence
    '''
    pvs1_genes = file2list( pvs1_genes_file )   ### load LOF genes from file
    lof_strong_consequences = ([
                          "frameshift_variant",
                          "stop_gained"
                        ])
    var_consequence = variant.infoVEP_dict['Consequence']
    var_gene = variant.infoVEP_dict['SYMBOL']
    if var_gene in pvs1_genes :
        if splicePatho_filter( variant ):
            return( True )
        ### split possible multi-Consequences in a list
        if '&' in var_consequence :
            var_consequence_list = var_consequence.split('&')
            for v in var_consequence_list :
                if v in lof_strong_consequences:
                    return( True )
        ### if mono-Consequence check if equal
        else :
            if var_consequence in lof_strong_consequences :
                return( True )
    ### if None found return False
    return( False )



def lof_moderate_filter( variant ) :
    '''
        check LOF MODERATE Consequence
    '''
    pvs1_genes = file2list( pvs1_genes_file )   ### load LOF genes from file
    lof_moderate_consequences = ([
                          "stop_lost",
                          "start_lost"
                        ])
    var_consequence = variant.infoVEP_dict['Consequence']
    var_gene = variant.infoVEP_dict['SYMBOL']
    if var_gene in pvs1_genes :
        ### split possible multi-Consequences in a list
        if '&' in var_consequence :
            var_consequence_list = var_consequence.split('&')
            for v in var_consequence_list :
                if v in lof_moderate_consequences :
                    return( True )
        ### if mono-Consequence check if equal
        else :
            if var_consequence in lof_moderate_consequences :
                return( True )
    ### if None found return False
    return( False )


def lastExon_filter( variant ) :
    '''
        check last exon harbored variant
    '''
    var_exon = variant.infoVEP_dict['EXON']
    if var_exon :
        if '/' in var_exon:
            exon, total_exons = var_exon.split('/')
            if exon == total_exons :
                return( True )
    return( False )


def coding_filter( variant ) :
    '''
        check coding region
    '''
    var_biotype = variant.infoVEP_dict['BIOTYPE']
    if var_biotype == 'protein_coding' :
        return( True )
    return( False )


def NMD_filter( variant ) :
    '''
        check NMD Consequence
    '''
    var_consequence = variant.infoVEP_dict['Consequence']
    ### split possible multi-Consequences in a list
    if '&' in var_consequence :
        var_consequence_list = var_consequence.split('&')
        for v in var_consequence_list :
            if v == 'NMD_transcript_variant' :
                return( True )
    ### if mono-Consequence check if equal
    else :
        if var_consequence == 'NMD_transcript_variant' :
            return( True )
    ### if None found return False
    return( False )


def ba1Exceptions_filter( variant ):
    '''
        check if one of the variant in the clingen BA1 exception list
    '''
    ba1Exceptions_list = file2list( ba1Exceptions_file )
    varID = variant.id
    if varID in ba1Exceptions_list :
        return( True )
    return( False )


def clinvarPatho_filter( variant ):
    '''
        check if P/LP and NOT Conflicting in CLINVAR
    '''
    varClinsig = variant.infoVEP_dict['ClinVar_CLNSIG']
    if varClinsig:
        if 'athogenic' in varClinsig:
            if not 'onflict' in varClinsig:
                return( True )
    return( False )


def clinvarBenign_filter( variant ):
    '''
        check if B/LB in CLINVAR
    '''
    varClinsig = variant.infoVEP_dict['ClinVar_CLNSIG']
    if varClinsig:
        if 'enign' in varClinsig:
            return( True )
    return( False )


def convertClinvarClinRevStat( variant ):
    '''
        convert ClinVar_CLNREVSTAT into numeric STAR
    '''
    clinRevStar_dict = ({
                            "no_assertion_provided" : 0,
                            "no_assertion_criteria_provided" : 0,
                            "no_assertion_for_the_individual_variant" : 0,
                            "criteria_provided&_single_submitter" : 1,
                            "criteria_provided&_conflicting_interpretations" : 1,
                            "criteria_provided&_multiple_submitters&_no_conflicts" : 2,
                            "reviewed_by_expert_panel" : 3,
                            "practice_guideline" : 4
    })
    varClinRevStat = variant.infoVEP_dict['ClinVar_CLNREVSTAT']
    if varClinRevStat:
        if varClinRevStat in clinRevStar_dict:
            variant.infoVEP_dict.update({ 'ClinVar_CLNREVSTAR' : clinRevStar_dict[ varClinRevStat ] })
            return( clinRevStar_dict[ varClinRevStat ] )
    return( False )

import re

def convertHGVSp( HGVSp ):
    '''
        this converts ClinVar HGVSp to the format for file clinvarHGVSp recognition
    '''
    p_dict = {}
    specialCharsToRemove = [ '%' ]
    ### split transcript from HGVSp if present
    if ':' in HGVSp:
        p = HGVSp.split(':')[-1]
    else:
        p = HGVSp
    ### remove p. at beginnning
    if p[0:2] == 'p.':
        p = p.replace('p.', '')
    ### split letters and digits
    p_splitted = re.split('(\d+)',p)
    ### remove empty values
    p_splitted = list( filter(None, p_splitted) )
    ### remove 3D
    if '3D' in p_splitted:
        p_splitted.remove('3D')
    ### remove D
    if 'D' in p_splitted:
        p_splitted.remove('D')
    for v in p_splitted:
        ### remove
        for s in specialCharsToRemove:
            if s in v:
                v = v.replace(s, '')
        ### populate DICT with AA and POS
        if v.isalpha():
            if 'aa1' not in p_dict:
                p_dict['aa1'] = v
            else:
                if 'aa2' not in p_dict:
                    p_dict['aa2'] = v
        if 'pos1' not in p_dict:
            if v.isdigit():
                p_dict['pos1'] = v
    return( p_dict )


def string2list( s, delimiter ):
    '''
        return a LIST of elements extracted from a string by a given delimiter
    '''
    l = []
    if delimiter in s:
        for v in s.split(delimiter):
            l.append(v)
    v = list(filter(None, l))
    return(v)

def ba1Exceptions_addDict( variant ):
    '''
        this add BA1 exception flag to VEP variant dict in order to avoid screen everytime
    '''
    if ba1Exceptions_filter( variant ):
        varBA1exception = 1
    else:
        varBA1exception = 0
    variant.addVEPdict_entry( 'BA1exception', varBA1exception )
    return( varBA1exception )


def sameHGVSpDict( p1, p2 ):
    '''
        check if same HGVSp converted DICT
    '''
    if 'aa1' in p1 and 'aa1' in p2:
        if p1['aa1'] == p2['aa1']:
            if 'pos1' in p1 and 'pos1' in p2:
                if p1['pos1'] == p2['pos1']:
                    if 'aa2' in p1 and 'aa2' in p2:
                        if p1['aa2'] == p2['aa2']:
                            return( True )
                    ### if BOTH without aa2 return True
                    else:
                        if 'aa2' not in p1 and 'aa2' not in p2:
                            return( True )
    return( False )



def HGVSpPathoClinvar( variant ):
    '''
        check if the variant HGVSp is the same of a known Clinvar P/LP
    '''
    pos = 0
    aa = 0
    clinvarHGVSp_dict = file2dict( clinvarHGVSp, colnames = [ 'gene', 'HGVSp', 'HGVSp_pos' ] )
    varGene = variant.infoVEP_dict['SYMBOL']
    HGVSp = variant.infoVEP_dict['HGVSp']
    varP = convertHGVSp( HGVSp )
    if varGene in clinvarHGVSp_dict:
        clinvarGenePos_string = clinvarHGVSp_dict[ varGene ]['HGVSp_pos']
        clinvarGenePos_list = string2list( clinvarGenePos_string, ',' )
        if 'pos1' in varP:
            if varP[ 'pos1' ] in clinvarGenePos_list:
                pos = 1
                clinvarGeneHGVSp_string = clinvarHGVSp_dict[ varGene ]['HGVSp']
                clinvarGeneHGVSp_list = string2list( clinvarGeneHGVSp_string, ',' )
                for v in clinvarGeneHGVSp_list:
                    vP = convertHGVSp( v )
                    if sameHGVSpDict( varP, vP ):
                        aa = 1
    if aa == 1:
        return( 'aa' )
    else:
        if pos == 1:
            return( 'pos' )
        else:
            return( False )



def hotspotRegion_filter( variant ):
    '''
        this check if a variant falls into one of the UCSC-derived hotspot regions
    '''
    ### extract gene_list and range_list (chr:start-stop) from UCSC hotspot file
    l = file2array( hotspotUCSC_file )
    ### to speed up the analysis create a DICT with K=gene : V=[ ranges ]
    hotspot_dict = {}
    for line in l:
        if line[0] not in hotspot_dict:
            hotspot_dict.update({ line[0] : [ line[2] ] })
        else :
            if line[2] not in hotspot_dict[ line[0] ]:
                hotspot_dict[ line[0] ].append(line[2])
    ### extract variant characteristics
    varGene = variant.infoVEP_dict['SYMBOL']
    varID = variant.id
    chr, pos, ref, alt = varID.split('-')
    ### check if in range after check if in one gene (for performance)
    if varGene in hotspot_dict:
        for r in hotspot_dict[ varGene ]:
            hotspotCHR, hotspotPOS = r.split(':')
            if chr == hotspotCHR:
                hotspotSTART, hotspotEND = hotspotPOS.split('-')
                if pos>=hotspotSTART and pos<=hotspotEND:
                    return( True )
    return( False )


def getInhMode( variant ):
    '''
        this function takes inh modes from OMIM genes with a related phenotype
        - REC only if ONLY recessive modes
    '''
    inh = 'NA'
    dom_modes = ([
                    'AD',
                    'XLD'
    ])
    rec_modes = ([
                    'AR',
                    'XLR',
                    'XL'
    ])
    omimInhMode_dict = file2dict( omimInhMode_file, delimiter = "\t", colnames = [ 'gene', 'inh_mode' ] )
    varGene = variant.infoVEP_dict['SYMBOL']
    if varGene in omimInhMode_dict:
        inhMode_string = omimInhMode_dict[ varGene ]['inh_mode']
        if ',' in inhMode_string:
            inhMode_list = inhMode_string.split(',')
            for inx in inhMode_list:
                if inx in dom_modes:
                    inh = 'dom'
                    break
                elif inx in rec_modes:
                    inh = 'rec'
        else:
            if inhMode_string in dom_modes:
                inh = 'dom'
            elif inhMode_string in rec_modes:
                inh = 'rec'
    return( inh )



def collectVARchars( variant, field_list ):
    '''
        this function returns a DICT of VAR values based on a given list of fields requested
    '''
    ### collect all chars of the VAR in a DICT K=field : V=value
    varC_dict = {}
    for f in field_list:
        if f not in varC_dict:
            varC_dict.update({ f : variant.infoVEP_dict[ f ] })
    return( varC_dict )


def screenNumeric( value_list ):
    '''
        this function goes through a list of values and check that are all INT/FLOAT and convert them in case are not
        - it REMOVES from the list whatever it cannot convert to INT/FLOAT
    '''
    value_list = list(filter(None, value_list))
    varV_list = []
    if value_list:
        for varV in value_list:
            try:
                varV = int(varV)
            except:
                try:
                    varV = float(varV)
                except:
                    continue
            if isinstance(varV, int) or isinstance(varV, float):
                varV_list.append( varV )
    return( varV_list )

def getHeader( variant ):
    '''
        this function extracts all the header from a variant VEP dictionary
    '''
    header_list = list(variant.infoVEP_dict.keys())
    return( header_list )

def getHeaderAF( variant ):
    '''
        this function extracts all the header related to AF from a variant VEP dictionary
    '''
    return( extractAF( getHeader( variant ) ) )

def getHeaderAC( variant ):
    '''
        this function extracts all the header related to AC from a variant VEP dictionary
    '''
    return( extractAC( getHeader( variant ) ) )

def getHeaderAN( variant ):
    '''
        this function extracts all the header related to AN from a variant VEP dictionary
    '''
    return( extractAN( getHeader( variant ) ) )


def extractAF( header_list ):
    '''
        this function extracts all the header related to AF from a list
    '''
    headerAF_list = [ x for x in header_list if (( len(x)>2 and x[-3:] == '_AF' ) or x == 'AF' ) ]
    return( headerAF_list )

def extractAC( header_list ):
    '''
        this function extracts all the header related to AC from a list
    '''
    headerAC_list = [ x for x in header_list if ( len(x)>2 and x[-3:] == '_AC' ) ]
    return( headerAC_list )

def extractAN( header_list ):
    '''
        this function extracts all the header related to AN from a list
    '''
    headerAN_list = [ x for x in header_list if ( len(x)>2 and x[-3:] == '_AN' ) ]
    return( headerAN_list )






thresholdRARE = 1E-4

def populationAF( variant, thresholdRARE ):
    '''
        this function screens ALL AF-related fields and return RARE or ABSENT based on MAX value found
        - it returns ABSENT/RARE and None if frequent
    '''
    ### collect all AF of the variant
    headerAF_list = getHeaderAF( variant )
    varAF_dict = collectVARchars( variant, headerAF_list )
    varAF_list = list( varAF_dict.values() )
    varAF_list = screenNumeric( varAF_list )
    ### extract the MAX value
    if varAF_list:
        varAFmax = max( varAF_list )
    else:
        varAFmax = 0
    ### if frequent return 'freq'
    if varAFmax >= 0.05:
        return( 'freq' )
    ### compare with threshold
    if varAFmax == 0:
        return( 'absent' )
    else:
        if varAFmax < thresholdRARE:
            return( 'rare' )
        else:
            return( 'thres' )




def controlsAF( variant ):
    '''
        this is to check if the variant is RARE in controls
        - it returns ABSENT/RARE and None if frequent
    '''
    headerAF_list = getHeaderAF( variant )
    controlsAF = [ x for x in headerAF_list if '_controls_' in x ]
    headerAC_list = getHeaderAC( variant )
    controlsAC = [ x for x in headerAC_list if '_controls_' in x ]
    ### collect all controls fields of the variant
    varAF_dict = collectVARchars( variant, controlsAF )
    varAF_list = list( varAF_dict.values() )
    varAF_list = screenNumeric( varAF_list )
    ### collect all controls fields of the variant
    varAC_dict = collectVARchars( variant, controlsAC )
    varAC_list = list( varAC_dict.values() )
    varAC_list = screenNumeric( varAC_list )
    ### extract the MAX AF value
    if varAF_list:
        varAFmax = max( varAF_list )
    else:
        varAFmax = 0
    ### extract the MAX AC value
    if varAC_list:
        varACmax = max( varAC_list )
    else:
        varACmax = 0
    ### compare with threshold
    if varAFmax == 0 and varACmax == 0:
        return( 'absent' )
    else:
        if varAFmax < thresholdRARE:
            return( 'rare' )
        else:
            ### if frequent return 'freq'
            if varAFmax >= 0.05:
                return( 'freq' )


def checkSNV( variant ):
    '''
        this function checks if a variant is a SNV or other based on VARIANT_CLASS
    '''
    if variant.infoVEP_dict['VARIANT_CLASS'] == 'SNV':
        return( True )
    return( False )


def controlsAF_filter( variant ):
    '''
        this is basically PM2 but needs to be added of the VAR class (SNV)
        PM2: Absent from controls (or at extremely low frequency if recessive)
    '''
    popAF = populationAF( variant, thresholdRARE )
    ctrlAF = controlsAF( variant )
    ### if ABSENT it is automatically TRUE regardless of inh_mode
    if popAF == 'absent':
        if ctrlAF == 'absent':
            return( True )
    elif popAF == 'rare':
        if getInhMode( variant ) == 'rec':
            ### if ctrlAF not None is absent or rare in controls
            if ctrlAF:
                return( True )
    return( False )


def proteinLengthConsequence( variant ):
    '''
        check if the VAR Consequence is able to alter protein length
    '''
    proteinLengthConsequence_list = ([
                          "frameshift_variant",
                          "stop_gained",
                          "splice_acceptor_variant",
                          "splice_donor_variant",
                          "stop_lost",
                          "start_lost",
                          "disruptive_inframe_deletion"
                        ])
    var_consequence = variant.infoVEP_dict['Consequence']
    ### split possible multi-Consequences in a list
    if '&' in var_consequence :
        var_consequence_list = var_consequence.split('&')
        for v in var_consequence_list :
            if v in proteinLengthConsequence_list :
                return( True )
    ### if mono-Consequence check if equal
    else :
        if var_consequence in proteinLengthConsequence_list :
            return( True )
    return( False )


def synonymous_filter( variant ):
    '''
        this considers only COMPLETELY synonymous variants (NOT if synonymous and something else)
    '''
    var_consequence = variant.infoVEP_dict['Consequence']
    if var_consequence == "synonymous_variant":
        return( True )
    return( False )

def intron_filter( variant ):
    '''
        this considers only COMPLETELY intronic variants (NOT if intronic and something else)
    '''
    var_consequence = variant.infoVEP_dict['Consequence']
    if var_consequence == "intron_variant":
        return( True )
    return( False )


def extractPolyphen( variant, field ):
    '''
        this is to extract and adapt polyphen score for a VAR (as it is often reported for multiple transcripts)
    '''
    p_list = []
    p = variant.infoVEP_dict[ field ]
    if p:
        if '&' in p:
            for v in p.split('&'):
                if v != '.':
                    if v not in p_list:
                        p_list.append( v )
        else:
            if p != '.':
                p_list.append( p )
    p_list = list( filter( None, p_list ) )
    ### consider Patho only if only D and P
    new_name = '{}_corrected'.format( field )
    if 'D' in p_list or 'P' in p_list:
        if 'B' not in p_list:
            variant.infoVEP_dict.update({ new_name : 'P' })
            return( 'P' )
        else:
            variant.infoVEP_dict.update({ new_name : 'U' })
            return( 'U' )
    else:
        if 'B' in p_list:
            variant.infoVEP_dict.update({ new_name : 'B' })
            return( 'B' )
    return( 'NA' )


def extractSIFT( variant ):
    '''
        this is to extract and adapt SIFT score for a VAR
    '''
    s = variant.infoVEP_dict[ 'SIFT' ]
    new_name = 'SIFT_corrected'
    if s:
        if '(' in s:
            s_pred = s.split('(')[0]
            if 'deleterious' in s_pred:
                variant.infoVEP_dict.update({ new_name : 'P' })
                return( 'P' )
            else:
                variant.infoVEP_dict.update({ new_name : 'B' })
                return( 'B' )
    return( 'NA' )


def extractLRT( variant ):
    '''
        this is to extract and adapt LRT score for a VAR
    '''
    s = variant.infoVEP_dict[ 'LRT_pred' ]
    new_name = 'LRT_pred_corrected'
    if s:
        if '&' in s:
            s_pred = s.split('&')[0]
        else:
            s_pred = s
        if s_pred :
            if 'D' in s_pred:
                variant.infoVEP_dict.update({ new_name : 'P' })
                return( 'P' )
            elif 'N' in s_pred:
                variant.infoVEP_dict.update({ new_name : 'N' })
                return( 'B' )
            elif 'U' in s_pred:
                variant.infoVEP_dict.update({ new_name : 'U' })
                return( 'NA' )
    return( 'NA' )


def extractMutationTaster( variant ):
    '''
        this is to extract and adapt MutationTaster score for a VAR
    '''
    s = variant.infoVEP_dict[ 'MutationTaster_pred' ]
    new_name = 'MutationTaster_pred_corrected'
    if s:
        if '&' in s:
            s_pred = s.split('&')[0]
        else:
            s_pred = s
        if s_pred:
            variant.infoVEP_dict.update({ new_name : s_pred })
        if 'A' in s_pred or 'D' in s_pred or 'P' in s_pred or 'N' in s_pred:
            return( 'P' )
        else:
            variant.infoVEP_dict.update({ new_name : 'NA' })
            return( 'B' )
    return( 'NA' )

def extractFATHMM( variant ):
    '''
        this is to extract and adapt FATHMM score for a VAR
    '''
    s = variant.infoVEP_dict[ 'FATHMM_pred' ]
    new_name = 'FATHMM_pred_corrected'
    if s:
        if '&' in s:
            s_pred = s.split('&')[0]
        else:
            s_pred = s
        if s_pred:
            variant.infoVEP_dict.update({ new_name : s_pred })
        if 'D' in s_pred:
            return( 'P' )
        elif 'T' in s_pred:
            return( 'B' )
        else:
            return( 'NA' )
            variant.infoVEP_dict.update({ new_name : 'NA' })
    return( 'NA' )



def extractPredNUM( variant, field, threshold ):
    '''
        this returns P/B based for the given field based on the threshold passed
        - NB: the value MUST be a single one (NOT list of values)
    '''
    value = variant.infoVEP_dict[ field ]
    new_name = '{}_corrected'.format( field )
    if value:
        r = screenNumeric( [value] )[0]
        variant.infoVEP_dict.update({ new_name : r })
        if r > threshold:
            f = 'P'
        else:
            f = 'B'
    else:
        f = 'NA'
    return( f )


def prediciton_filter( variant ):
    '''
        this function checks if the VAR is predicted to be Pathogenic by in-silico algorithms
    '''
    polyphen2_HDIV_pred = extractPolyphen( variant, 'Polyphen2_HDIV_pred' )
    polyphen2_HVAR_pred = extractPolyphen( variant, 'Polyphen2_HVAR_pred' )
    sift = extractSIFT( variant )
    revel = extractPredNUM( variant, 'REVEL_score', 0.5 )
    cadd = extractPredNUM( variant, 'CADD_PHRED', 15 )
    cadd22 = extractPredNUM( variant, 'CADD_PHRED', 22 )
    gerp = extractPredNUM( variant, 'GERP++_RS', 2 )
    lrt = extractLRT( variant )
    mt = extractMutationTaster( variant )
    fathmm = extractFATHMM( variant )
    pred_list = [ polyphen2_HDIV_pred, polyphen2_HVAR_pred, sift, revel, cadd, gerp, lrt, mt, fathmm ]
    listN = len( pred_list )
    ### if the only non-NA is CADD and is >22 is P
    if pred_list.count('NA') > (listN - 1) and cadd22 == 'P':
        return( True )
    ### if 2/3 P consider P regardless of the other
    fraction = listN * 2 / 3
    if pred_list.count('P') > fraction:
        return( True )
    ### if P < 2/3
    else:
        ### if P>1 and 0B consider P
        if pred_list.count('P') > 1 and pred_list.count('B') == 0:
            return( True )
    return( False )


def predicitonBenign_filter( variant ):
    '''
        this function checks if the VAR is predicted to be Benign by in-silico algorithms
    '''
    polyphen2_HDIV_pred = extractPolyphen( variant, 'Polyphen2_HDIV_pred' )
    polyphen2_HVAR_pred = extractPolyphen( variant, 'Polyphen2_HVAR_pred' )
    sift = extractSIFT( variant )
    revel = extractPredNUM( variant, 'REVEL_score', 0.5 )
    cadd = extractPredNUM( variant, 'CADD_PHRED', 15 )
    cadd22 = extractPredNUM( variant, 'CADD_PHRED', 22 )
    gerp = extractPredNUM( variant, 'GERP++_RS', 2 )
    gerp = extractPredNUM( variant, 'GERP++_RS', 2 )
    lrt = extractLRT( variant )
    mt = extractMutationTaster( variant )
    fathmm = extractFATHMM( variant )
    pred_list = [ polyphen2_HDIV_pred, polyphen2_HVAR_pred, sift, revel, cadd, gerp, lrt, mt, fathmm ]
    listN = len( pred_list )
    ### if 2/3 B consider B regardless of the other 2
    fraction = listN * 2 / 3
    if pred_list.count('B') > fraction:
        return( True )
    ### if B<4
    else:
        ### if B>1 and 0P consider B
        if pred_list.count('B') > 1 and pred_list.count('P') == 0:
            return( True )
    return( False )

def checkBA1exception_VEPdict( variant ):
    '''
        this function checks if the var has the BA1exception flag in its VEP dict otherwise checks it
    '''
    ### discard BA1 exception variants
    if not 'BA1exception' in variant.infoVEP_dict:
        ba1Exceptions_addDict( variant )
    if variant.infoVEP_dict[ 'BA1exception' ] == 1 :
        return( True )
    else:
        return( False )
    return( False )





################################################################
##################### consider if implement ####################
################################################################
'''
    if implemented I need to create a function to screen for every variant flanking region in CV created file P - LP- B
'''
# clinvarPM1base_file = "/home/enrico/Dropbox/NY/clinvar/db_nov2020/clinvar_nov2020_pm1.vcf"
def calculateClinvarHotspot( variant ):
    clinvarPM1base_array = file2array( clinvarPM1base_file )
    ### extract variant characteristics
    varID = variant.id
    chr, pos, ref, alt = varID.split('-')
################################################################
################################################################
################################################################





################################################################
##################### ACMG CRITERIA filter #####################
################################################################

def pvs1_filter( variant ):
    '''
        PVS1 filtering
    '''
    if coding_filter( variant ):
        if lof_strong_filter( variant ):
            if not NMD_filter( variant ):
                if not lastExon_filter( variant ):
                    return( "S" )
                else:
                    return( "M" )
            else:
                return( "VS" )
        elif lof_moderate_filter( variant ):
            if not lastExon_filter( variant ):
                return( "M" )
            else:
                return( "P" )
    return( False )



def ps1_filter( variant ):
    '''
        PS1 filtering
    '''
    ### discard BA1 exception variants
    if checkBA1exception_VEPdict( variant ):
        return( False )
    ### if Clinvar P/LP VAR
    if clinvarPatho_filter( variant ):
        if convertClinvarClinRevStat( variant ):
            if convertClinvarClinRevStat( variant ) > 0:
                return( True )
    ### if not Clinvar P/LP but same AA change
    else:
        if HGVSpPathoClinvar( variant ):
            if HGVSpPathoClinvar( variant ) == 'aa':
                return( True )
    return( False )


def ps3_filter( variant ):
    '''
        PS3: Well-established in vitro or in vivo functional studies supportive of a damaging effect on the gene or gene product
        - mutually exclusive with PS1
        - this is implemented as known in ClinVar but not automated the functional/in-vivo part
    '''
    ### if already added PS1 to variant dict exit
    if 'ps1' in variant.infoACMGpatho_dict:
        if variant.infoACMGpatho_dict[ 'ps1' ] == 'S':
            return( False )
    ### if Clinvar P/LP VAR
    if clinvarPatho_filter( variant ):
        if convertClinvarClinRevStat( variant ):
            if convertClinvarClinRevStat( variant ) > 0:
                return( True )
    return( False )


def pm1_filter( variant ):
    '''
        PM1: Located in a mutational hot spot and/or critical and well-established functional domain (e.g., active site of an enzyme) without benign variation
        - this is implemented as known in ClinVar but not automated the functional/in-vivo part
    '''
    ### if Clinvar P/LP VAR
    if hotspotRegion_filter( variant ):
        return( True )
    return( False )

def pm2_filter( variant ):
    '''
        PM2: Absent from controls (or at extremely low frequency if recessive)
        - if SNV downgraded to supporting
    '''
    if controlsAF_filter( variant ):
        if checkSNV( variant ):
            return('P')
        else:
            return('M')
    return( False )

def pm4_filter( variant ):
    '''
        PM4: Protein length changes as a result of in-frame deletions/insertions in a non-repeat region or stop-loss variants
        - mutually exclusive with PVS1
        - !!! TO IMPLEMENT a REPEATED-REGIONS filter !!!! --> https://www.biostars.org/p/473172
    '''
    ### if already added PVS1 to variant dict exit
    if 'pvs1' in variant.infoACMGpatho_dict:
        return( False )
    if proteinLengthConsequence( variant ):
        return( True )
    return( False )

def pm5_filter( variant ):
    '''
        PM5: Novel missense change at an amino acid residue where a different missense change determined to be pathogenic has been seen before
    '''
    if HGVSpPathoClinvar( variant ) == 'pos':
        return( True )
    return( False )

def pp2_filter( variant ):
    '''
        PP2: Missense variant in a gene that has a low rate of benign missense variation and in which missense variants are a common mechanism of disease
    '''
    missenseGenes_list = file2list( missenseGenes_file )
    varGene = variant.infoVEP_dict['SYMBOL']
    varConsequence = variant.infoVEP_dict['Consequence']
    if varGene in missenseGenes_list:
        if checkSNV( variant ):
            if not proteinLengthConsequence( variant ):
                if not synonymous_filter( variant ):
                    if not intron_filter( variant ):
                        if variant.infoVEP_dict['Consequence'] != "conservative_inframe_deletion":
                            return( True )
    return( False )

def pp3_filter( variant ):
    '''
        PP3: Multiple lines of computational evidence support a deleterious effect on the gene or gene product (conservation, evolutionary, splicing impact, etc.)
    '''
    if prediciton_filter( variant ):
        return( True )
    return( False )


def pp5_filter( variant ):
    '''
        PP5: Reputable source recently reports variant as pathogenic, but the evidence is not available to the laboratory to perform an independent evaluation
        - mutually exclusive with PS1 and PS3
    '''
    ### if already added PS1 to variant dict exit
    if 'ps1' in variant.infoACMGpatho_dict:
        if variant.infoACMGpatho_dict[ 'ps1' ] == 'S':
            return( False )
    ### if already added PS3 to variant dict exit
    if 'ps3' in variant.infoACMGpatho_dict:
        if variant.infoACMGpatho_dict[ 'ps3' ] == 'S':
            return( False )
    if clinvarPatho_filter( variant ):
        if not convertClinvarClinRevStat( variant ) or convertClinvarClinRevStat( variant ) == 0:
                return( True )
    return( False )


################################################################
######################### BENIGN filter ########################
################################################################

def ba1_filter( variant ):
    '''
        Allele frequency is >5%
        - mutually exclusive with PM2
        - consider BA1 exception list
    '''
    ### discard BA1 exception variants
    if checkBA1exception_VEPdict( variant ):
        return( False )
    if populationAF( variant, thresholdRARE ) == 'freq':
        return( True )
    return( False )

def bs1_filter( variant ):
    '''
        Allele frequency is greater than expected for disorder
    '''
    genesBS1_dict = file2dict( genesBS1_file, delimiter = "\t", colnames = [ "gene", "AF_threshold" ] )
    varGene = variant.infoVEP_dict['SYMBOL']

    ### discard BA1 exception variants
    if checkBA1exception_VEPdict( variant ):
        return( False )
    ### if already added BA1 to variant dict exit
    if 'ba1' in variant.infoACMGbenign_dict:
        return( False )
    if varGene in genesBS1_dict:
        geneAFthreshold = screenNumeric(genesBS1_dict[ varGene ]['AF_threshold'])[0]
        if populationAF( variant, geneAFthreshold ) == 'thres':
            return( True )
    return( False )


def bs3_filter( variant ):
    '''
        BS3: Well-established in vitro or in vivo functional studies show no damaging effect on protein function or splicing
    '''
    if clinvarBenign_filter( variant ):
        if convertClinvarClinRevStat( variant ):
            if convertClinvarClinRevStat( variant ) > 0:
                return( True )
    return( False )

def bp1_filter( variant ):
    '''
        Missense variant in a gene for which primarily truncating variants are known to cause disease
        - mutually exclusive with PP2
    '''
    if checkBA1exception_VEPdict( variant ):
        return( False )
    pvs1_genes = file2list( pvs1_genes_file )   ### load LOF genes from file
    var_gene = variant.infoVEP_dict['SYMBOL']
    ### if already added BA1 to variant dict exit
    if 'pp1' in variant.infoACMGpatho_dict:
        return( False )
    if var_gene in pvs1_genes :
        if checkSNV( variant ):
            if not proteinLengthConsequence( variant ):
                if not synonymous_filter( variant ):
                    if not intron_filter( variant ):
                        if variant.infoVEP_dict['Consequence'] != "conservative_inframe_deletion":
                            return( True )
    return( False )

def bp4_filter( variant ):
    '''
        Multiple lines of computational evidence suggest no impact on gene or gene product (conservation, evolutionary, splicing impact, etc.)
        - mutually exclusive with PP3
    '''
    if checkBA1exception_VEPdict( variant ):
        return( False )
    ### if already added PP3 to variant dict exit
    if 'pp3' in variant.infoACMGbenign_dict:
        return( False )
    if not prediciton_filter( variant ):
        if predicitonBenign_filter( variant ):
            return( True )
    return( False )


def bp6_filter( variant ):
    '''
        Reputable source recently reports variant as benign, but the evidence is not available to the laboratory to perform an independent evaluatio
    '''
    if checkBA1exception_VEPdict( variant ):
        return( False )
    if clinvarBenign_filter( variant ):
        if convertClinvarClinRevStat( variant ):
            if convertClinvarClinRevStat( variant ) == 0:
                return( True )
    return( False )

def bp7_filter( variant ):
    '''
        A synonymous (silent) variant for which splicing prediction algorithms predict no impact to the splice consensus sequence nor the creation of a new splice site AND the nucleotide is not highly conserved
    '''
    if checkBA1exception_VEPdict( variant ):
        return( False )
    if synonymous_filter( variant ):
        if not splicePatho_filter( variant ):
            return( True )
    return( False )




################################################################
################################################################
################################################################


'''
    UNIMPLEMENTED rules:
        - PS2: De novo (both maternity and paternity confirmed) in a patient with the disease and no family history
        - PS4: The prevalence of the variant in affected individuals is significantly increased compared with the prevalence in controls
        - PM6: Assumed de novo, but without confirmation of paternity and maternity
        - PP1: Cosegregation with disease in multiple affected family members in a gene definitively known to cause the disease
        - PP4: Patient’s phenotype or family history is highly specific for a disease with a single genetic etiology
        - BS2: Observed in a healthy adult individual for a recessive (homozygous), dominant (heterozygous), or X-linked (hemizygous) disorder
        - BS4: Lack of segregation in affected members of a family

        - BP2: Observed in trans with a pathogenic variant for a fully penetrant dominant gene/disorder or observed in cis with a pathogenic variant in any inheritance pattern
        - BP3: In-frame deletions/insertions in a repetitive region without a known function
        - BP5: Variant found in a case with an alternate molecular basis for disease

    TO IMPLEMENT later:
        - PM3: For recessive disorders, detected in trans with a pathogenic variant
'''


#####################################################
################### ACMG class ######################
#####################################################

def acmgClassAssign( variant ):
    '''
        this function assigns the overall ACMG class for each variant and record in variant DICT the fullfilled criterias
    '''
    if pvs1_filter( variant ):
        ### collect result of PVS1 filter (possible: VS, S, M, P)
        varPVS1 = pvs1_filter( variant )
        variant.addACMGpatho_criteria( 'pvs1', varPVS1 )
        ### add to overall AMG patho dict of the variant
        variant.infoACMGpatho_overall_dict[ varPVS1 ] += 1
    if ps1_filter( variant ):
        variant.addACMGpatho_criteria( 'ps1', 'S' )
        variant.infoACMGpatho_overall_dict[ 'S' ] += 1
    if ps3_filter( variant ):
        variant.addACMGpatho_criteria( 'ps3', 'S' )
        variant.infoACMGpatho_overall_dict[ 'S' ] += 1
    if pm1_filter( variant ):
        variant.addACMGpatho_criteria( 'pm1', 'M' )
        variant.infoACMGpatho_overall_dict[ 'M' ] += 1
    if pm2_filter( variant ):
        varPM2 = pm2_filter( variant )
        variant.addACMGpatho_criteria( 'pm2', varPM2 )
        variant.infoACMGpatho_overall_dict[ varPM2 ] += 1
    if pm4_filter( variant ):
        variant.addACMGpatho_criteria( 'pm4', 'M' )
        variant.infoACMGpatho_overall_dict[ 'M' ] += 1
    if pm5_filter( variant ):
        variant.addACMGpatho_criteria( 'pm5', 'M' )
        variant.infoACMGpatho_overall_dict[ 'M' ] += 1
    if pp2_filter( variant ):
        variant.addACMGpatho_criteria( 'pp2', 'P' )
        variant.infoACMGpatho_overall_dict[ 'P' ] += 1
    if pp3_filter( variant ):
        variant.addACMGpatho_criteria( 'pp3', 'P' )
        variant.infoACMGpatho_overall_dict[ 'P' ] += 1
    if pp5_filter( variant ):
        variant.addACMGpatho_criteria( 'pp5', 'P' )
        variant.infoACMGpatho_overall_dict[ 'P' ] += 1
    ### BENIGN
    if ba1_filter( variant ):
        variant.addACMGbenign_criteria( 'ba1', 'BA' )
        variant.infoACMGbenign_overall_dict[ 'A' ] += 1
    if bs1_filter( variant ):
        variant.addACMGbenign_criteria( 'bs1', 'BS' )
        variant.infoACMGbenign_overall_dict[ 'S' ] += 1
    if bs3_filter( variant ):
        variant.addACMGbenign_criteria( 'bs3', 'BS' )
        variant.infoACMGbenign_overall_dict[ 'S' ] += 1
    if bp1_filter( variant ):
        variant.addACMGbenign_criteria( 'bp1', 'BP' )
        variant.infoACMGbenign_overall_dict[ 'P' ] += 1
    if bp4_filter( variant ):
        variant.addACMGbenign_criteria( 'bp4', 'BP' )
        variant.infoACMGbenign_overall_dict[ 'P' ] += 1
    if bp6_filter( variant ):
        variant.addACMGbenign_criteria( 'bp6', 'BP' )
        variant.infoACMGbenign_overall_dict[ 'P' ] += 1
    if bp7_filter( variant ):
        variant.addACMGbenign_criteria( 'bp7', 'BP' )
        variant.infoACMGbenign_overall_dict[ 'P' ] += 1
    ### calculate overall ACMG classification
    overallACMG = 'US'
    overallACMGbenign = 0
    overallACMGpatho = 0
    # BENIGN
    if variant.infoACMGbenign_overall_dict[ 'A' ] > 0 or variant.infoACMGbenign_overall_dict[ 'S' ] > 1:
        overallACMG = 'B'
    elif variant.infoACMGbenign_overall_dict[ 'S' ] > 0 and variant.infoACMGbenign_overall_dict[ 'P' ] > 0:
        overallACMG = 'LB'

    if overallACMG == 'B' or overallACMG == 'LB' :
        overallACMGbenign += 1

    # PATHO
    if variant.infoACMGbenign_overall_dict[ 'S' ] < 2:
        if variant.infoACMGpatho_overall_dict[ 'VS' ] > 0 and variant.infoACMGpatho_overall_dict[ 'S' ] > 0 :
            overallACMG = 'P'
        elif variant.infoACMGpatho_overall_dict[ 'VS' ] > 0 and variant.infoACMGpatho_overall_dict[ 'M' ] > 1 :
            overallACMG = 'P'
        elif variant.infoACMGpatho_overall_dict[ 'VS' ] > 0 and variant.infoACMGpatho_overall_dict[ 'M' ] > 0 and variant.infoACMGpatho_overall_dict[ 'P' ] > 0 :
            overallACMG = 'P'
        elif variant.infoACMGpatho_overall_dict[ 'VS' ] > 0 and variant.infoACMGpatho_overall_dict[ 'P' ] > 1 :
            overallACMG = 'P'
        ### this is the new one added
        elif variant.infoACMGpatho_overall_dict[ 'VS' ] > 0 and variant.infoACMGpatho_overall_dict[ 'P' ] > 0 :
            overallACMG = 'P'
        elif variant.infoACMGpatho_overall_dict[ 'S' ] > 1 :
            overallACMG = 'P'
        elif variant.infoACMGpatho_overall_dict[ 'S' ] > 1 and variant.infoACMGpatho_overall_dict[ 'M' ] > 2 :
            overallACMG = 'P'
        elif variant.infoACMGpatho_overall_dict[ 'S' ] > 0 and variant.infoACMGpatho_overall_dict[ 'M' ] > 1 and variant.infoACMGpatho_overall_dict[ 'P' ] > 2 :
            overallACMG = 'P'
        elif variant.infoACMGpatho_overall_dict[ 'S' ] > 0 and variant.infoACMGpatho_overall_dict[ 'M' ] > 0 and variant.infoACMGpatho_overall_dict[ 'P' ] > 3 :
            overallACMG = 'P'
        elif variant.infoACMGpatho_overall_dict[ 'VS' ] > 0 and variant.infoACMGpatho_overall_dict[ 'M' ] > 0 :
            overallACMG = 'LP'
        elif variant.infoACMGpatho_overall_dict[ 'S' ] > 0 and variant.infoACMGpatho_overall_dict[ 'M' ] > 0 and variant.infoACMGpatho_overall_dict[ 'M' ] < 3 :
            overallACMG = 'P'
        elif variant.infoACMGpatho_overall_dict[ 'S' ] > 0 and variant.infoACMGpatho_overall_dict[ 'P' ] > 1 :
            overallACMG = 'LP'
        elif variant.infoACMGpatho_overall_dict[ 'M' ] > 2 :
            overallACMG = 'LP'
        elif variant.infoACMGpatho_overall_dict[ 'M' ] > 1 and variant.infoACMGpatho_overall_dict[ 'P' ] > 1 :
            overallACMG = 'LP'
        elif variant.infoACMGpatho_overall_dict[ 'M' ] > 0 and variant.infoACMGpatho_overall_dict[ 'P' ] > 3 :
            overallACMG = 'LP'

    if overallACMG == 'P' or overallACMG == 'LP' :
        overallACMGpatho += 1

    ### if both P and B then US
    if overallACMGpatho > 0 and overallACMGbenign > 0 :
        overallACMG = 'US'

    return( overallACMG )



#####################################################
################# DB connections ####################
#####################################################
#import sqlite3
#import create_DB
def sqlDBinsert( table_name, column_names, values ):

    ### create connection to DB
    conn = sqlite3.connect('/home/enrico/Dropbox/NY/asilo_variant/test0.db')

    ### create values to insert
    sql_command = 'INSERT INTO ' + table_name + ' {0} values {1}'.format(tuple(column_names), tuple(values))

    try:
        # insert into Variant
        conn.execute(sql_command)
        conn.commit()
    except:
        print( "ERROR in SQL row insertion !" )
        print( "  - table: " + str(table_name) )
        print( "  - columns: " + str(column_names) )
        print( "  - values: " + str(values) )
        print( "ERROR in row insertion !" )


def getSQLvarID( variant ):
    '''
        this function takes the generated_id of the variant to assign to relative sample external column
    '''
    id = create_DB.getSQLrow( 'generated_id', 'Variant', 'name', variant )
    return( id )

def getSQLsampleID( name ):
    '''
        this function takes the generated_id of the Sample
    '''
    id = create_DB.getSQLrow( 'generated_id', 'Sample', 'name', name )
    return( id )


#####################################################
################ cloudBigTable DB ###################
#####################################################
# import cloud_bigtable_functions

def createColumnFamiliesDict( sample_dict ):
    '''
        this creates a dictionary to add variants to cloudBigTable
    '''
    column_families_dict = ({
        'CHARS' : [
                    'chr',
                    'pos',
                    'ref',
                    'alt',
                    'Allele',
                    'SYMBOL',
                    'Gene',
                    'Feature_type',
                    'Feature',
                    'BIOTYPE',
                    'INTRON',
                    'EXON',
                    'HGVSc',
                    'HGVSp',
                    'cDNA_position',
                    'CDS_position',
                    'Protein_position',
                    'Amino_acids',
                    'Codons',
                    'Existing_variation',
                    'DISTANCE',
                    'STRAND',
                    'FLAGS',
                    'VARIANT_CLASS',
                    'SYMBOL_SOURCE',
                    'HGNC_ID',
                    'CANONICAL',
                    'MANE',
                    'TSL',
                    'APPRIS',
                    'CCDS',
                    'ENSP',
                    'SWISSPROT',
                    'TREMBL',
                    'UNIPARC',
                    'SOURCE',
                    'GENE_PHENO',
                    'DOMAINS',
                    'miRNA',
                    'HGVS_OFFSET',
                    'SOMATIC',
                    'PHENO',
                    'PUBMED',
                    'VAR_SYNONYMS',
                    'MOTIF_NAME',
                    'MOTIF_POS',
                    'HIGH_INF_POS',
                    'MOTIF_SCORE_CHANGE',
                    'TRANSCRIPTION_FACTORS',
                    'GTEx_V8_gene',
                    'GTEx_V8_tissue',
                    'Geuvadis_eQTL_target_gene',
                    'MutationAssessor_pred',
                    'MutationAssessor_score',
                    'genename'
                ],
        'ACMG' : [
                    'ACMG',
                    'pvs1',
                    'ps1',
                    'ps2',
                    'ps3',
                    'ps4',
                    'pm1',
                    'pm2',
                    'pm3',
                    'pm4',
                    'pm5',
                    'pm6',
                    'pp1',
                    'pp2',
                    'pp3',
                    'pp4',
                    'pp5',
                    'ba1',
                    'bs1',
                    'bs2',
                    'bs3',
                    'bs4',
                    'bp1',
                    'bp2',
                    'bp3',
                    'bp4',
                    'bp5',
                    'bp6',
                    'bp7'
                 ],
        'PRED' : [
                    'Consequence',
                    'IMPACT',
                    'Polyphen2_HDIV_pred_corrected',
                    'Polyphen2_HVAR_pred_corrected',
                    'SIFT_corrected',
                    'REVEL_score_corrected',
                    'CADD_PHRED_corrected',
                    'GERP++_RS_corrected',
                    'LRT_pred_corrected',
                    'FATHMM_pred_corrected',
                    'MutationTaster_pred_corrected',
                    'ada_score_corrected',
                    'rf_score_corrected',
                    'SIFT',
                    'PolyPhen',
                    'ada_score',
                    'rf_score',
                    'CADD_PHRED',
                    'CADD_RAW',
                    'CADD_phred',
                    'FATHMM_pred',
                    'FATHMM_score',
                    'GERP++_RS',
                    'LRT_pred',
                    'LRT_score',
                    'MutationTaster_pred',
                    'MutationTaster_score',
                    'Polyphen2_HDIV_pred',
                    'Polyphen2_HDIV_score',
                    'Polyphen2_HVAR_pred',
                    'Polyphen2_HVAR_score',
                    'REVEL_rankscore',
                    'REVEL_score'
            ],
        'CLINVAR' : [
                        'ClinVar',
                        'ClinVar_CLNSIG',
                        'ClinVar_CLNREVSTAT',
                        'ClinVar_CLNDN',
                        'ClinVar_CLNDISDB',
                        'ClinVar_CLNREVSTAR'
        ],
        'OTHER' : [
                        'other'
        ]
    })

    headerAF_list = extractAF( list(master_dict.VEPh_dict.keys()) )
    column_families_dict.update({ 'AF' : headerAF_list })
    headerAC_list = extractAC( list(master_dict.VEPh_dict.keys()) )
    column_families_dict.update({ 'AC' : headerAC_list })
    headerAN_list = extractAN( list(master_dict.VEPh_dict.keys()) )
    column_families_dict.update({ 'AN' : headerAN_list })
    sample_list = list( master_dict.sample_dict.keys() )
    column_families_dict.update({ 'SAMPLES' : sample_list })
    return( column_families_dict )



def dictionarizeVariantCalledFunctions( variant, empty = 0 ) :
    '''
        this function stores all the functions necessary to dictionarizeVariant to be called for each Variant
    '''
    ### create Variant final_dict after populating samples
    variant.finalVARdict()

    if variant.id not in master_dict.variantClass_dict:
        master_dict.variantClass_dict.update({ variant.id : {} })
        for column_family_ID, column_list in master_dict.column_families_dict.items() :
            ### start a counter to REMOVE column_family_ID with NO values inside
            column_family_ID_counter = 0
            if column_family_ID not in master_dict.variantClass_dict[ variant.id ]:
                master_dict.variantClass_dict[ variant.id ].update({ column_family_ID : {} })
            for c in column_list :
                if c in variant.final_dict :
                    ### if asked to IGNORE EMPTY values
                    if empty == 0:
                        if variant.final_dict[c]:
                            master_dict.variantClass_dict[variant.id][column_family_ID].update({ c : variant.final_dict[c] })
                            column_family_ID_counter += 1
                    else:
                        master_dict.variantClass_dict[variant.id][column_family_ID].update({ c : variant.final_dict[c] })
                        column_family_ID_counter += 1
            ### if NO value inserted for the column_family_ID then removes it
            if column_family_ID_counter == 0:
                master_dict.variantClass_dict[ variant.id ].pop( column_family_ID )



@logPrinter
def dictionarizeVariant( empty = 0, print_time = 0 ):
    '''
        this insert variants in the dictionary to cloudBigTable
        - NB: you can choose to add empty values or not through empty arg
    '''
    logPrinterChunk_dict( master_dict.var_dict, dictionarizeVariantCalledFunctions, 'variant' )



def analyzeVariantsCalledFunctions( variant ):
    '''
        this stores all functions called for each variant in analyzeVariants
    '''
    ### check if a BA1 exception and add to Variant VEP dict
    ba1Exceptions_addDict( variant )
    varACMG = acmgClassAssign( variant )
    variant.infoVEP_dict.update({ 'ACMG' : varACMG })


@logPrinter
def analyzeVariants( print_time = 0 ):
    '''
        this functions screen for each Variant ACMG classification and create the final dictionaries necessary to cloudBigTable pull
    '''
    logPrinterChunk_dict( master_dict.var_dict, analyzeVariantsCalledFunctions, 'variant' )


@logPrinter
def pullVariantsToCloudBigTable( variantClass_dict, print_time = 0 ) :
    '''
        this function actually pull the variants to cloudBigTable
    '''
    ### insert in cloudBigTable DB
    projectID = "diagnosticaotr-00"
    bigtableID = "diagnosticaotr-00-bigtable-00"
    tableID = 'test0'
    try:
        cloud_bigtable_functions.cloudBigTable_KEYinsert( projectID, bigtableID, tableID, variantClass_dict, print_time = print_time )
        return( True )
    except:
        return( False )



#######################################################
#################### SAMPLE functions #################
#######################################################
def getInhModeGenes_dict():
    '''
        this function returns all genes in OMIM with at least a REC inh mode listed
    '''
    dom_modes = ([
                    'AD',
                    'XLD'
    ])
    rec_modes = ([
                    'AR',
                    'XLR',
                    'XL'
    ])
    omimInhMode_dict = file2dict( omimInhMode_file, delimiter = "\t", colnames = [ 'gene', 'inh_mode' ] )
    results_dict = {}
    for varGene, inh_mode in omimInhMode_dict.items() :
        inh = 'NA'
        if varGene in omimInhMode_dict:
            inhMode_string = omimInhMode_dict[ varGene ]['inh_mode']
            if ',' in inhMode_string:
                inhMode_list = inhMode_string.split(',')
                for inx in inhMode_list:
                    if inx in dom_modes:
                        inh = 'dom'
                        break
                    elif inx in rec_modes:
                        inh = 'rec'
            else:
                if inhMode_string in dom_modes:
                    inh = 'dom'
                elif inhMode_string in rec_modes:
                    inh = 'rec'
        results_dict.update({ varGene : inh })
    return( results_dict )



def checkSampleComphet( sample ):
    '''
        this screen for possible comphet in each sample
        - it also populates Gene Class
    '''
    omimInhModes_dict = getInhModeGenes_dict()
    gene_dict = {}
    i = 0
    for var, gt in sample.varGT_dict.items() :
        ### take Variant Class object
        variant = master_dict.var_dict[ var ]
        ### if gene is REC
        varID = variant.id
        varGene = variant.infoVEP_dict[ 'SYMBOL' ]
        varZig = sample.varGT_dict[ var ][ 'convGT' ]

        ### populates geneClass
        if varGene not in master_dict.gene_dict:
            master_dict.gene_dict.update({ varGene : i })
            master_dict.gene_dict[ varGene ] = Gene( varGene )
        ### and add Variant and relative Sample to Gene Class DICT
        master_dict.gene_dict[ varGene ].addGeneVarSample( var, sample.id )

        ### store samples in Variant class
        variant.addSample( sample.id, varZig )

        if varGene in omimInhModes_dict :
            if omimInhModes_dict[ varGene ] == 'rec' :
                varACMG = variant.infoVEP_dict[ 'ACMG' ]
                ### only if variant is a COMPHET
                if varZig == 'het':
                    # print( '  --> {0} ({2}={4}) : {1}. ACMG {3}'.format( var, varZig, varGene, varACMG, omimInhModes_dict[ varGene ] ) )
                    ### collect variants on the same gene
                    if varGene not in gene_dict:
                        gene_dict.update({ varGene : {} })
                    if varACMG == 'P' or varACMG == 'LP' or varACMG == 'US' :
                        gene_dict[ varGene ].update({ varID : varACMG })
        i += 1
    ### write DICT to Sample class object only if at least 2 var in same gene survived (ACMG: P/LP)
    for gene, gene_vars_dict in gene_dict.items():
        if len( gene_vars_dict ) > 1 :
            sample.comphet_dict.update({ gene : gene_vars_dict })
    #if sample.comphet_dict:
    #    print()
    #    print( "---------------------------------" )
    #    print( 'Sample: {0}. Comphet: {1}'.format( sample.id, sample.comphet_dict ) )



def analyzeSamplesCalledFunctions( sample ) :
    '''
        this stores all the functions called for each sample (as analyzeVariantsCalledFunctions() for Variants)
    '''
    checkSampleComphet( sample )


@logPrinter
def analyzeSamples( print_time = 0 ) :
    '''
        this creates the loop and calls the necessary functions to analyze all Samples
    '''
    logPrinterChunk_dict( master_dict.sample_dict, analyzeSamplesCalledFunctions, 'sample' )


def dictionarizeSampleCalledFunctions( sample ) :
    master_dict.sampleClass_dict.update({ sample.id : { 'varGT' : sample.varGT_dict } })
    master_dict.sampleClass_dict[ sample.id ].update( { 'comphet' : sample.comphet_dict } )

@logPrinter
def dictionarizeSample( print_time = 0 ) :
    '''
        this creates the loop and calls the necessary functions to dictionarize all Samples
    '''
    logPrinterChunk_dict( master_dict.sample_dict, dictionarizeSampleCalledFunctions, 'sample' )




#######################################################
#################### GENE functions ###################
#######################################################
def dictionarizeGeneCalledFunctions( gene ) :
    master_dict.geneClass_dict.update({ gene.id : { 'var' :  gene.varSample_dict } })

@logPrinter
def dictionarizeGene( print_time = 0 ) :
    '''
        this creates the loop and calls the necessary functions to dictionarize all Genes
    '''
    logPrinterChunk_dict( master_dict.gene_dict, dictionarizeGeneCalledFunctions, 'gene' )



#####################################################
################# script calling ####################
#####################################################
def mainCaller( IN ) :
    ### decide if print LOGS
    print_logs = 1

    ### read Variants and Samples from VCF
    readVCF( IN, print_time = print_logs )

    ### analyze Variants ACMG and create final_dict
    analyzeVariants( print_time =  print_logs )
    ###### Sample analysis and Gene class population

    analyzeSamples( print_time = print_logs )

    ### get variants DICT for cloudBigTable
    dictionarizeVariant( print_time = print_logs )

    ### get samples DICT
    dictionarizeSample( print_time = print_logs )

    ### get genes DICT
    dictionarizeGene( print_time = print_logs )

    ### return the 3 classes DICT
    return( master_dict.variantClass_dict, master_dict.sampleClass_dict, master_dict.geneClass_dict )







##################################################################################
######################## UPDATE with server known P/LP ###########################
##################################################################################
def update_var_dict_known( var_dict, known_dict ):
    '''
        this is to update VAR dict with known P/LP variants pulled from server
    '''
    d = var_dict
    for var_name, v_dict in var_dict.items():
        if var_name in known_dict:
            d[var_name].update({ 'KNOWN' : known_dict[var_name] })
    return( d )










### ENDc
