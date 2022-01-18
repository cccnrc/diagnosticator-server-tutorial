from flask import render_template, redirect, url_for, flash, request, \
                    current_app, make_response, jsonify, abort, send_from_directory
from flask_login import login_required, current_user, logout_user
from werkzeug.urls import url_parse
from werkzeug.utils import secure_filename
from app import db
from app.analysis import bp
import datetime
import os
from app.decorators import server_valid_authentication_required, project_required, send_variants, \
    project_data_required, update_known_variants, update_known_variants_redis_DB
from app.analysis.forms import UploadForm

@bp.route('/index')
def index():
    flash('INDEX','success')
    return( render_template( 'analysis/index.html' ))

@bp.errorhandler(413)
def too_large(e):
    return "File is too large", 413

@bp.route('/uploaded', methods=["GET", "POST"])
@login_required
@project_required
@server_valid_authentication_required
def uploaded():
    USER_UPLOAD_FOLDER = os.path.join( current_app.config['UPLOAD_FOLDER'], 'VCF-ANALYSIS', current_user.server_username )
    files = os.listdir( USER_UPLOAD_FOLDER )
    NOW = datetime.datetime.now()
    FILE_CHARS_DICT = dict()
    for item in os.scandir( USER_UPLOAD_FOLDER ):
        ### get name
        if item.name not in FILE_CHARS_DICT:
            FILE_CHARS_DICT.update({ item.name : dict() })
        ### get size
        SIZE_KB = str(round(item.stat().st_size / (1024), 3))
        SIZE_MB = str(round(item.stat().st_size / (1024 * 1024), 3))
        SIZE_GB = str(round(item.stat().st_size / (1024 * 1024 * 1024), 3))
        if SIZE_GB[0] == "0":
            if SIZE_MB[0] == "0":
                SIZE_APPEND = SIZE_KB
                SIZE_FORMAT = 'KB'
            else:
                SIZE_APPEND = SIZE_MB
                SIZE_FORMAT = 'MB'
        else:
            SIZE_APPEND = SIZE_GB
            SIZE_FORMAT = 'GB'
        FILE_CHARS_DICT[ item.name ].update({ 'size_value': SIZE_APPEND, 'size_format': SIZE_FORMAT })
        EXP = datetime.datetime.fromtimestamp( item.stat().st_ctime ) + datetime.timedelta(days=1)
        DIFF = EXP - NOW
        FILE_CHARS_DICT[ item.name ].update({ 'expiration': str(DIFF).split('.', 2)[0] })
    return render_template('analysis/upload.html', FILE_CHARS_DICT = FILE_CHARS_DICT )


@bp.route('/', methods=["GET", "POST"])
@login_required
@project_required
@server_valid_authentication_required
def upload():
    USER_UPLOAD_FOLDER = os.path.join( current_app.config['UPLOAD_FOLDER'], 'VCF-ANALYSIS', current_user.server_username )
    uploaded_file = request.files["file"]
    filename = secure_filename(uploaded_file.filename)
    if filename != '':
        file_ext = os.path.splitext(filename)[1]
        if file_ext not in current_app.config['ALLOWED_EXTENSIONS']:
            return "Invalid File Type", 400
        uploaded_file.save(os.path.join(USER_UPLOAD_FOLDER, filename))
    #return '', 204
    return( redirect(url_for('analysis.uploaded')) )



@bp.route('/uploads/<filename>')
def uploads(filename):
    USER_UPLOAD_FOLDER = os.path.join( current_app.config['UPLOAD_FOLDER'], 'VCF-ANALYSIS', current_user.server_username )
    return send_from_directory( USER_UPLOAD_FOLDER, filename )
