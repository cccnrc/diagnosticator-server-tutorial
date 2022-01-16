from app.models import User
from app import db
from flask_login import login_user, logout_user, current_user, login_required
from flask import flash, request, redirect
from flask import current_app, url_for
import requests
from datetime import datetime, timedelta



def check_create_local_user( username ):
    '''
        this checks existence of local user and adds it otherwise
    '''
    user = User.query.filter_by( server_username = username ).first()
    if not user:
        user = User( server_username = username )
        db.session.add(user)
        db.session.commit()
    login_user(user)

def check_server_authenticate_user():
    user = User.query.filter_by( server_username = current_user.server_username ).first()
    ### check token saved in DB active
    if user.check_server_token() :
        return( True )
        ### confirm that the token is identical to server one
        # if check_server_token_expiration() :
        #    return( True )
    return( False )



def check_server_token_expiration():
    user = User.query.filter_by( server_username = current_user.server_username ).first()
    server_url = current_app.config['SERVER_ADDRESS']
    token = user.server_token
    # flash( user.server_token_expiration, 'info')
    headers = { 'Authorization': 'Bearer {0}'.format(token) }
    r = requests.post( '{0}/api/check_token_exp'.format(server_url), headers = headers )
    if r:
        # flash(datetime.strptime(r.json()['exp'], '%m/%d/%y %H:%M:%S:%f'), 'warning' )
        if datetime.strptime(r.json()['exp'], '%m/%d/%y %H:%M:%S:%f') == user.server_token_expiration:
            return( True )
        else:
            flash( 'Wrong exp local token. Logging out ...', 'success' )
            logout_user()
            return( False )
    else:
        flash( 'Wrong request. Logging out ...', 'success' )
        logout_user()
        return( False )
    return( False )




def check_server_user( username, password ):
    '''
        this is to confirm with central server that exists an user
        is to envoke only if tokens auth fails
    '''
    next = request.args.get('next')
    if not next:
        next = url_for('main.index')
    ### check existence in local DB and otherwise insert it
    check_create_local_user( username )
    user = User.query.filter_by( server_username = username ).first()
    ### send token request to backend
    auth = requests.auth.HTTPBasicAuth( username, password )
    server_url = current_app.config['SERVER_ADDRESS']
    r = requests.post( '{0}/api/tokens'.format(server_url), auth = auth )
    if r:
        if 'token' in r.json() and 'exp' in r.json():
            if r.json()['token']:
                user.server_token = r.json()['token']
                user.server_token_expiration = datetime.strptime(r.json()['exp'], '%m/%d/%y %H:%M:%S:%f')
                db.session.commit()
                # flash( 'Stored token: {0}, exp: {1}, for user: {2}'.format(r.json()['token'], datetime.utcnow() + timedelta(seconds = token_expiration_server), username), 'success')
                return redirect( next )
    flash( "ERROR, be sure you typed your SERVER password correctly", 'danger')
    # flash( "server response: {}".format( r.text ), 'danger')
    return( False )


import base64
import os

def development_check_server_user( ):
    '''
        this serves to mimic a real user existence on server
    '''
    username = 'tester-00'
    password = 'tester-00'
    next = request.args.get('next')
    if not next:
        next = url_for('main.index')
    ### check existence in local DB and otherwise insert it
    check_create_local_user( username )
    user = User.query.filter_by( server_username = username ).first()
    ### define token expiration
    token = base64.b64encode(os.urandom(24)).decode('utf-8')
    expires_in = 3600
    ### mimic token allowed
    user.server_token = token
    user.server_token_expiration = datetime.utcnow() + timedelta(seconds=expires_in)
    db.session.commit()
    # flash( 'Stored token: {0}, exp: {1}, for user: {2}'.format( token, datetime.utcnow() + timedelta(seconds = expires_in), username), 'success')
    return redirect( next )


from flask import session

def check_server_key():
    if 'user_key' in session:
        # flash( 'Key already stored for user: {}'.format( current_user.server_username ), 'success' )
        return( True )
    # flash( 'requesting key for: {}'.format( current_user.server_username ), 'info' )
    user = User.query.filter_by( server_username = current_user.server_username ).first()
    server_url = current_app.config['SERVER_ADDRESS']
    headers = { 'Authorization': 'Bearer {0}'.format(current_user.server_token) }
    r = requests.post( '{0}/api/get_key'.format(server_url), headers = headers )
    if r:
        if 'user_key' in r.json():
            # flash( 'Key stored for user: {}'.format( current_user.server_username ), 'success' )
            # flash(r.json())
            session['user_key'] = r.json()['user_key']
            return( True )
        else:
            # flash( "Problem getting the key from server: {}".format( r.json()['error'] ), 'danger' )
            return( False )
    flash( "Problem getting the key from server", 'danger' )
    return( False )
