from functools import wraps

from flask import flash, redirect, url_for, current_app
from app.models import User
from app.auth.functions import check_server_authenticate_user, check_server_key
from flask import request
from flask import url_for
from flask_login import logout_user, current_user
from datetime import datetime
from app import db
from app.variant_functions import send_local_variants, get_server_new_messages_dict, check_project_data, update_known_variants_local_DB, update_var_dict_known_to_redis

def server_valid_authentication_required(func):
    @wraps(func)
    def decorated_function(*args, **kwargs):
        ### if login disabled ignores it
        if current_app.login_manager._login_disabled or current_app.config['DEVELOPMENT_TESTING'] == True:
            pass
        else:
            if current_user.is_anonymous:
                flash('Please authenticate on server first', 'warning')
                logout_user()
                return redirect(url_for('auth.authenticate_on_server', next = request.url))
            else:
                if check_server_authenticate_user():
                    if check_server_key():
                        current_user.authenticated_on = datetime.utcnow()
                        db.session.commit()
                else:
                    flash('Please authenticate on server first', 'warning')
                    logout_user()
                    return redirect(url_for('auth.authenticate_on_server', next = request.url))
        return func(*args, **kwargs)

    return decorated_function


def project_required(func):
    @wraps(func)
    def decorated_function(*args, **kwargs):
        if not current_user.project_name:
            flash('Please create a project first', 'warning')
            return redirect(url_for('main.project', next = request.url))
        return func(*args, **kwargs)
    return decorated_function

def send_variants(func):
    @wraps(func)
    def decorated_function(*args, **kwargs):
        ### if login disabled ignores it
        if current_app.login_manager._login_disabled or current_app.config['DEVELOPMENT_TESTING'] == True:
            return func(*args, **kwargs)
        NUM_UPDATED = update_known_variants_local_DB()
        # flash("updated {} variants".format(NUM_UPDATED), 'info')
        return func(*args, **kwargs)
    return decorated_function

def update_known_variants(func):
    @wraps(func)
    def decorated_function(*args, **kwargs):
        ### if login disabled ignores it
        if current_user.is_anonymous or current_app.login_manager._login_disabled or current_app.config['DEVELOPMENT_TESTING'] == True:
            pass
        else:
            if send_local_variants() == False:
                # flash('Please ensure server connection first', 'warning')
                return redirect(url_for('auth.authenticate_on_server', next = request.url))
        return func(*args, **kwargs)
    return decorated_function


def update_known_variants_redis_DB(func):
    @wraps(func)
    def decorated_function(*args, **kwargs):
        ### if login disabled ignores it
        if current_app.login_manager._login_disabled or current_app.config['DEVELOPMENT_TESTING'] == True:
            return func(*args, **kwargs)
        if update_var_dict_known_to_redis() == False:
            flash('Problems updating variants REDIS DB, contact administrators', 'warning')
            # return redirect(url_for('auth.authenticate_on_server', next = request.url))
        return func(*args, **kwargs)
    return decorated_function


def get_messages(func):
    @wraps(func)
    def decorated_function(*args, **kwargs):
        if current_app.login_manager._login_disabled or current_app.config['DEVELOPMENT_TESTING'] == True:
            pass
        else:
            get_server_new_messages_dict()
        return func(*args, **kwargs)
    return decorated_function


def project_data_required(func):
    @wraps(func)
    def decorated_function(*args, **kwargs):
        if not check_project_data():
            flash('Please analyze your VCF first', 'warning')
            return redirect(url_for('main.upload', next = request.url))
        return func(*args, **kwargs)
    return decorated_function
