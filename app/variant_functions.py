from flask import current_app, flash
from flask_login import current_user
import redis_functions
import requests
from app.models import User, Message
from app import db
from datetime import datetime
from flask import current_app

def get_report_statuses():
    '''
        this is to return the list with status to be reported to server
    '''
    l = ([
            'AC',
            'SE',
            'RE',
            'US'
        ])
    return(l)


def send_local_var( variant_name, new_status ):
    '''
        this is to send a variant accepted as P/LP
    '''
    variant_dict = redis_functions.redis_dict_return( url = current_app.config['REDIS_URL'], database = 2, key_prefix = 'var', key_value = variant_name )
    variant_dict_ACMG = variant_dict['ACMG']
    data = ({
                'var_accepted' : variant_name,
                'var_accepted_ACMG' : variant_dict_ACMG,
                'var_accepted_status' : new_status,
                'project_name' : current_user.project_name,
                'assembly' : current_user.project_assembly
            })
    location = '/api/post_var'
    res = send_data_to_server( data, location )
    if res:
        if res.json()['insertion'] == 'success':
            return( True )
    return( False )


def report_local_var( VAR_NAME, SAMPLE_STATUS ):
    '''
        this is to send a variant accepted as P/LP
    '''
    variant_dict = redis_functions.redis_dict_return( url = current_app.config['REDIS_URL'], database = 2, key_prefix = 'var', key_value = VAR_NAME )
    if 'ACMG' in variant_dict:
        variant_dict_ACMG = variant_dict['ACMG']
        VAR_ACMG = variant_dict_ACMG['ACMG']
        variant_dict_ACMG.pop('ACMG')
        VAR_ACMG_CLASSES = '+'.join(map(str,variant_dict_ACMG.values()))
    else:
        return( False )
    data = ({
                'var_accepted' : VAR_NAME,
                'var_accepted_ACMG' : VAR_ACMG,
                'var_accepted_ACMG_criterias' : VAR_ACMG_CLASSES,
                'var_accepted_status' : SAMPLE_STATUS,
                'project_name' : current_user.project_name,
                'assembly' : current_user.project_assembly
            })
    location = '/api/report_variant'
    res = send_data_to_server( data, location )
    if res:
        if res.json()['insertion'] == 'success':
            return( True )
    return( False )


def send_local_variants():
    if current_user.project_variant_sent == True or current_app.login_manager._login_disabled or current_app.config['DEVELOPMENT_TESTING'] == True:
        return( True )
    data = get_variants_to_send()
    location = '/api/post_variants'
    res = send_data_to_server( data, location )
    if res:
        if res.json()['vars_added'] == len(data['variants_dict']['var_list']):
            current_user.project_variant_sent = True
            db.session.commit()
            return( True )
    return( False )


def get_variants_to_send() :
    '''
        this returns the json obj to attach to the request
    '''
    project_name = current_user.project_name
    variant_list = redis_functions.redis_keys_return( url = current_app.config['REDIS_URL'], database = 2, key_prefix = 'var', pwd = None )
    assembly = current_user.project_assembly
    data = { 'variants_dict' : { 'var_list' : variant_list }, 'assembly' : assembly, 'project_name' : project_name }
    return( data )


def send_data_to_server( data, location ):
    server_url = current_app.config['SERVER_ADDRESS']
    user = User.query.filter_by( server_username = current_user.server_username ).first()
    token = user.server_token
    headers = { 'Authorization': 'Bearer {0}'.format(token) }
    res = requests.post( '{0}{1}'.format( server_url, location ), headers = headers, json=data )
    if res:
        return( res )
    return None



def get_known_variants():
    '''
        this pulls the dict of known variants from server
    '''
    if current_app.config['DEVELOPMENT_TESTING'] == True:
        fake_dict = {}
        return( fake_dict )
    project_name = current_user.project_name
    assembly = current_user.project_assembly
    data = { 'assembly' : assembly, 'project_name' : project_name }
    location = '/api/get_known_variants'
    res = send_data_to_server( data, location )
    if res:
        if 'known_dict' in res.json():
            return( res.json()['known_dict'] )
    return( None )


def get_all_known_variants():
    '''
        this pulls the dict of known variants from server
    '''
    if current_app.config['DEVELOPMENT_TESTING'] == True:
        fake_dict = {}
        return( fake_dict )
    location = '/api/get_all_known_variants'
    data = {}
    res = send_data_to_server( data, location )
    if res:
        if 'known_dict' in res.json():
            return( res.json()['known_dict'] )
    return( None )



def get_server_new_messages_dict():
    '''
        this pulls new messages from the server
    '''
    data = {}
    location = '/api/get_user_new_messages'
    res = send_data_to_server( data, location )
    if res:
        if 'new_messages_N' in res.json():
            if res.json()['new_messages_N'] > 0:
                add_server_new_messages_dict( res.json()['m_dict'] )
                return( res.json() )
    return( None )


def add_server_new_messages_dict( m_dict ):
    '''
        this adds messages and notifications to the user
    '''
    inserted_bodies = []
    for body, t in m_dict.items():
        if body:
            if body not in inserted_bodies:
                msg = Message( recipient_id = current_user.id, body = body, timestamp =  datetime.strptime( t, '%m/%d/%y %H:%M:%S:%f' ) )
                db.session.add(msg)
                current_user.add_notification( 'unread_message_count', current_user.new_messages() )
                db.session.commit()
                inserted_bodies.append( body )
    return( None )



def check_project_data():
    '''
        this checks that the user has data analyzed in their project
    '''
    if redis_functions.check_data_in_DB( current_app.config['REDIS_URL'], database = 2, pwd = None ):
        return( True )
    return( None )

import datetime
from app.models import KnownVariants


def update_known_variants_local_DB():
    known_server_dict = get_all_known_variants()
    if known_server_dict:
        for ASSEMBLY, VAR_DICT in known_server_dict.items():
            for VAR_NAME, VAR_REPORTS in VAR_DICT.items():
                for VAR_ACMG_CLASS, VAR_ACMG_CLASS_NUM in VAR_REPORTS.items():
                    try :
                        VAR = KnownVariants.query.filter_by(
                                name = VAR_NAME,
                                assembly = ASSEMBLY,
                                acmg_classification = VAR_ACMG_CLASS,
                                acmg_classification_num = VAR_ACMG_CLASS_NUM
                        ).first()
                        VAR.last_update = datetime.datetime.utcnow()
                        db.session.commit()
                    except:
                        VAR = KnownVariants(
                                name = VAR_NAME,
                                assembly = ASSEMBLY,
                                acmg_classification = VAR_ACMG_CLASS,
                                acmg_classification_num = VAR_ACMG_CLASS_NUM
                        )
                        db.session.add(VAR)
                        db.session.commit()
    if known_server_dict:
        RES = len( known_server_dict )
    else:
        RES = 0
    return( RES )



def send_message_notification( user_id, body ):
    user = User.query.get(user_id)
    if body:
        msg = Message( recipient_id = user_id, body=body )
        db.session.add(msg)
        user.add_notification('unread_message_count', user.new_messages())
        db.session.commit()
    else:
        print( "Empty Message Notification !!!" )

def get_known_variants_from_DB():
    known_dict = dict()
    known_variants = KnownVariants.query.all()
    for VAR in known_variants:
        VAR_ASSEMBLY = VAR.assembly
        VAR_NAME = VAR.name
        VAR_ACMG = VAR.acmg_classification
        VAR_ACMG_NUM = VAR.acmg_classification_num
        if VAR_ASSEMBLY in known_dict:
            if VAR_NAME in known_dict[VAR_ASSEMBLY]:
                known_dict[VAR_ASSEMBLY][VAR_NAME].update({ VAR_ACMG : VAR_ACMG_NUM })
            else:
                known_dict[VAR_ASSEMBLY].update({ VAR_NAME : { VAR_ACMG : VAR_ACMG_NUM }})
        else:
            known_dict.update({ VAR_ASSEMBLY : { VAR_NAME : { VAR_ACMG : VAR_ACMG_NUM }}})
    return( known_dict )

def update_var_dict_known_to_redis( ):
    '''
        this is to ADD the KNOWN flag to an existing VAR
    '''
    known_dict = get_known_variants_from_DB()
    user_var = redis_functions.redis_dict_return( url = current_app.config['REDIS_URL'], database = 2, key_prefix = 'var' )
    ASSEMBLY = current_user.project_assembly
    if ASSEMBLY in known_dict:
        try:
            known_dict_ASSEMBLY = known_dict[ASSEMBLY]
            ### get DICT intersection
            intersection = user_var.keys() & known_dict_ASSEMBLY.keys()
            for VAR_U in intersection:
                if 'KNOWN' in user_var[VAR_U]:
                    ### if KNOWN and USER agree then do nothing
                    if user_var[VAR_U]['KNOWN'] == known_dict_ASSEMBLY[VAR_U]:
                        pass
                        #flash( "VAR: {} --> {} agreed".format( VAR_U, user_var[VAR_U]['KNOWN'] ), 'success' )
                    else:
                        MSG_BODY = "Hi {0}, your variants: {1} has a new report in SERVER DB, check it out!".format( current_user.server_username, VAR_U )
                        send_message_notification( current_user.id, MSG_BODY )
                        # flash( "VAR: {} --> {} disagreed: {}".format( VAR_U, user_var[VAR_U]['KNOWN'], known_dict_ASSEMBLY[VAR_U] ), 'error' )
                        for VAR_ACMG_CLASS, VAR_ACMG_CLASS_NUM in known_dict_ASSEMBLY[VAR_U].items():
                            #flash( "VAR: {}, CRITERIA: {}, NUM {}".format( VAR_U, VAR_ACMG_CLASS, VAR_ACMG_CLASS_NUM ), 'info' )
                            #flash( " -- USER: {}".format( user_var[VAR_U]['KNOWN'] ), 'warning' )
                            ### if criteria present but with a different number of reports updates it
                            if VAR_ACMG_CLASS in user_var[VAR_U]['KNOWN']:
                                if user_var[VAR_U]['KNOWN'][VAR_ACMG_CLASS] != VAR_ACMG_CLASS_NUM:
                                    ### update REDIS
                                    redis_functions.redis_update_dict_element( url = current_app.config['REDIS_URL'], database = 2, key_prefix = 'var', key_value = VAR_U, subdict_name = 'KNOWN', element_name = VAR_ACMG_CLASS, element_value = VAR_ACMG_CLASS_NUM )
                            ### if criteria absent adds it
                            else:
                                redis_functions.redis_add_dict_element( url = current_app.config['REDIS_URL'], database = 2, key_prefix = 'var', key_value = VAR_U, subdict_name = 'KNOWN', element_name = VAR_ACMG_CLASS, element_value = VAR_ACMG_CLASS_NUM )
            return( True )
        except:
            return( False )




import json
import os

def load_json_dict( FILE ):
    with open( FILE,"r") as f:
      data = f.read()
    dict = json.loads(data)
    return( dict )

def load_VAR_SAMPLE_GENE_json_dict( JSON_FOLDER ):
    VAR_JSON_FILE = os.path.join( JSON_FOLDER, 'var_dict.json' )
    SAMPLE_JSON_FILE = os.path.join( JSON_FOLDER, 'sample_dict.json' )
    GENE_JSON_FILE = os.path.join( JSON_FOLDER, 'gene_dict.json' )
    variant_dict = load_json_dict( VAR_JSON_FILE )
    sample_dict = load_json_dict( SAMPLE_JSON_FILE )
    gene_dict = load_json_dict( GENE_JSON_FILE )
    return( variant_dict, sample_dict, gene_dict )

def write_json_dict( DICT, KEY, JSON_FOLDER ):
    JSON_FOLDER = JSON_FOLDER
    VAR_JSON_FILE = os.path.join( JSON_FOLDER, 'var_dict.json' )
    SAMPLE_JSON_FILE = os.path.join( JSON_FOLDER, 'sample_dict.json' )
    GENE_JSON_FILE = os.path.join( JSON_FOLDER, 'gene_dict.json' )
    if KEY == 'VAR':
        FILE = VAR_JSON_FILE
    elif KEY == 'SAMPLE':
        FILE = SAMPLE_JSON_FILE
    elif KEY == 'GENE':
        FILE = GENE_JSON_FILE
    with open( FILE, 'w') as fp:
        json.dump(DICT, fp)
    return( True )

def JSON_update_dict_element( key_prefix, key_value, subdict_name, element_name, element_value, JSON_FOLDER ):
    variant_dict, sample_dict, gene_dict = load_VAR_SAMPLE_GENE_json_dict( JSON_FOLDER )
    if key_prefix == 'VAR':
        DICT = variant_dict
    elif key_prefix == 'SAMPLE':
        DICT = sample_dict
    elif key_prefix == 'GENE':
        DICT = gene_dict
    ### check
    if not key_value in DICT:
        return( False )
    if subdict_name in DICT[key_value]:
        if element_name in DICT[key_value][subdict_name]:
            DICT[key_value][subdict_name][element_name] = element_value
        else:
            DICT[key_value][subdict_name].update({ element_name : element_value })
    else:
        DICT[key_value].update({ subdict_name : { element_name : element_value } })
    write_json_dict( DICT, key_prefix, JSON_FOLDER = JSON_FOLDER )
    return( True )




### ENDc
