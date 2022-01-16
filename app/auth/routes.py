from flask import render_template, redirect, url_for, flash, request, current_app
from werkzeug.urls import url_parse
from app import db
from app.auth import bp
import datetime
from app.auth.forms import InsertPasswordRequestForm
from app.auth.functions import check_server_user, check_server_key, development_check_server_user
from flask_login import login_required, current_user, logout_user
from app.decorators import server_valid_authentication_required
from app.models import User
import requests



####################################################################
############ this is to check central DB authentication ############
####################################################################
import shutil
import os

@bp.route('/authenticate_on_server', methods=['GET', 'POST'])
def authenticate_on_server( ):
    next = request.args.get('next')
    if not next:
        next = url_for('main.index')
    ### if DEVELOPMENT_TESTING create a fake user and a fake token
    if current_app.config['DEVELOPMENT_TESTING'] == True:
        # flash( 'creating fake user: tester-00', 'info' )
        development_check_server_user()
        return redirect( next )
    ### if NOT DEVELOPMENT_TESTING check server authentication
    form = InsertPasswordRequestForm()
    if form.validate_on_submit():
        if check_server_user( form.username.data, form.password.data ):
            ### add the folder for the USER TUTORIAL if not existing yet
            USER_JSON_FOLDER = os.path.join( current_app.config['JSON_FOLDER'], form.username.data )
            if not os.path.exists( USER_JSON_FOLDER ):
                os.mkdir( USER_JSON_FOLDER )
                shutil.copy2( os.path.join(current_app.config['JSON_FOLDER'], 'var_dict.json'), USER_JSON_FOLDER )
                shutil.copy2( os.path.join(current_app.config['JSON_FOLDER'], 'sample_dict.json'), USER_JSON_FOLDER )
                shutil.copy2( os.path.join(current_app.config['JSON_FOLDER'], 'gene_dict.json'), USER_JSON_FOLDER )
                flash( 'copied tutorial files in your folder!', 'success' )
            return redirect( next )
    text_dict = ({
            'title' : 'Authenticate on Central Website',
            'text' : 'Insert your Central Diagnosticator Website credentials:',
            'text_category' : 'warning',
            'link' : current_app.config['SERVER_ADDRESS'],
            'link_text' : 'Diagnosticator Central Website'
    })
    return( render_template('insert_DXcator.html',
                text_dict = text_dict,
                form=form
            ))


@bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('main.index'))

####################################################################
####################################################################
####################################################################
