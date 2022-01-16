from flask import render_template, flash, redirect, url_for, request, g, \
                        jsonify, current_app, abort, Markup

from flask_login import login_user, logout_user, current_user, login_required
import requests
from uuid import getnode as get_mac
from app.development import bp
from app import db
import datetime
import redis_functions


##########################################################################
########################## DEVELOPMENT-specific ##########################
##########################################################################
@bp.route('/development_check_mysql_connection')
def development_check_mysql_connection( ):
    flash( "MySQL URL: {}".format( current_app.config['SQLALCHEMY_DATABASE_URI'] ))
    flash( check_mysql_connection() )
    return( render_template( 'blank_DXcator.html' ) )


@bp.route('/development_check_redis_worker')
def development_check_redis_worker():
    flash( "redis URL: {}".format( current_app.config['REDIS_URL'] ))
    flash( "MySQL URL: {}".format( current_app.config['SQLALCHEMY_DATABASE_URI'] ))
    current_user.launch_task('check_redis_worker_message_user', 'Checking redis worker...', url = current_app.config['REDIS_URL'], database = 2 )
    db.session.commit()
    return( render_template( 'blank_DXcator.html' ) )


@bp.route('/development_check_server_connection')
def development_check_server_connection( ):
    server_ip = current_app.config['SERVER_ADDRESS']
    flash( "server URL: {}".format( server_ip ))
    if check_host( server_ip ):
        send_post_request( server_ip )
    return( render_template( 'blank_DXcator.html' ) )

@bp.route('/development_check_app_codes')
def development_check_app_codes( ):
    runN = current_app.config['RUN']
    flash( "number of initiation of this app: {}".format( runN ))
    return( render_template( 'blank_DXcator.html' ) )


@bp.route('/development_check_redis_connection')
def development_check_redis_connection( ):
    r = redis_functions.redis_connect( current_app.config['REDIS_URL'], 1 )
    if r:
        flash( 'connected to {}'.format(current_app.config['REDIS_URL']), 'success')
    else:
        flash( 'Error connecting to {}'.format(current_app.config['REDIS_URL']), 'danger')
    return( render_template( 'blank_DXcator.html' ) )


@bp.route('/development_check_login_required')
def development_check_login_required( ):
    type = 'danger'
    if current_app.config['LOGIN_DISABLED'] == True:
        type = 'success'
    flash( 'LOGIN_DISABLED set to {}'.format(current_app.config['LOGIN_DISABLED']), type )
    return( render_template( 'blank_DXcator.html' ) )

@bp.route('/development_check_development_testing')
def development_check_development_testing( ):
    type = 'danger'
    if current_app.config['DEVELOPMENT_TESTING'] == True:
        type = 'success'
    flash( 'DEVELOPMENT_TESTING set to {}'.format(current_app.config['DEVELOPMENT_TESTING']), type )
    return( render_template( 'blank_DXcator.html' ) )


@bp.route('/development_check_upload_dir')
def development_check_upload_dir( ):
    flash( 'UPLOAD_FOLDER set to {}'.format(current_app.config['UPLOAD_FOLDER']), 'info' )
    return( render_template( 'blank_DXcator.html' ) )


def check_host( ip_address ):
    '''
        this simply checks wether the host IP is up or not
    '''
    try:
        r = requests.get( ip_address )
        r.raise_for_status()  # Raises a HTTPError if the status is 4xx, 5xxx
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
        flash( "Host {0} is DOWN".format(ip_address) )
    except requests.exceptions.HTTPError:
        flash( "Host {0} is in HTTP error".format(ip_address) )
    else:
        flash( "Host {0} is working well!".format(ip_address) )
        return( True )
    return( False )



def send_post_request( ip_address ):
    #make a POST request
    mac = get_mac()
    dictToSend = {'question':'what is the answer?', 'myIP' : str(request.host), 'mac' : mac }
    flash( "local-app is running on: {0}, and sending request to: {1}".format( request.host, ip_address ) )
    flash( "my MAC address is: {0}".format( mac ))
    res = requests.post( '{0}/receive_data'.format( ip_address ), json=dictToSend )
    flash( "I am sending: {0}".format( dictToSend ) )
    flash ('  - response from server: {}'.format(res.json()))



def check_mysql_connection():
    try:
        db.session.execute('SELECT 1')
        return( True )
    except:
        return( False )



#########################################################
########## update known variants database ###############
#########################################################
from app.variant_functions import get_all_known_variants
from app.models import KnownVariants

@login_required
@bp.route('/update_known_variants')
def update_known_variants():
    known_variants = KnownVariants.query.all()
    flash( 'KNOWN VARIANTS in DB: {}'.format( len( known_variants ) ), 'info' )
    known_server_dict = get_all_known_variants()
    flash( 'KNOWN VARIANTS in SERVER DB: {}'.format( len( known_server_dict ) ), 'info' )
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
    known_variants = KnownVariants.query.all()
    flash( 'VARIANTS added to local DB: {}'.format( len( known_variants ) ), 'success' )
    return( render_template( 'blank_DXcator.html' ) )



#########################################################
##########  update known variants REDIS   ###############
#########################################################
@bp.route('/update_known_variants_redis_entry')
def update_known_variants_redis_entry():
    V = update_var_dict_known_to_redis()
    return( render_template( 'blank_DXcator.html' ) )


from app.main.routes import get_known_variants_from_DB





#########################################################
##########  update known variants REDIS   ###############
#########################################################
@bp.route('/multiple_projects')
def multiple_projects():
    return( render_template( 'multiple_projects_DXcator.html' ) )






















### ENDc
