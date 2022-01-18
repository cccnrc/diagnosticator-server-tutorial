from datetime import datetime
from flask import render_template, flash, redirect, url_for, request, g, \
    jsonify, current_app, abort, Markup
from app import db
from app.main import bp
from flask_login import login_user, logout_user, current_user, login_required
from app.decorators import server_valid_authentication_required, project_required, send_variants, \
    project_data_required, update_known_variants, update_known_variants_redis_DB
from flask import session
# import mongodb_functions
import redis_functions
import app.main.diagnosticator_rendering_functions as diagnosticator_rendering_functions
from werkzeug.utils import secure_filename
import os
import functools
from app.models import Notification, User, Message, KnownVariants
from app.main.forms import NewProjectForm
import requests
from uuid import getnode as get_mac
from app.variant_functions import send_local_variants, get_known_variants, get_all_known_variants, get_report_statuses, send_local_var, get_server_new_messages_dict
from app.main.forms import SearchForm, FilterForm
import json


######################################################################
########################## PREPROCESSING #############################
######################################################################
@bp.context_processor
def example():
    '''
        this decorator allows to pass a function to all templates
        to access it access the K directly in j2
    '''
    user_dict = ({
        'classes_dict' : diagnosticator_rendering_functions.get_classes_dict(),
        'ACMG_classes_dict' : diagnosticator_rendering_functions.get_ACMG_classes_dict(),
        'ACMG_strength_dict' : diagnosticator_rendering_functions.get_ACMG_strength_dict(),
        'ACMG_subclass_dict' : diagnosticator_rendering_functions.get_ACMG_subclass_dict(),
        'abbreviations_dict' : diagnosticator_rendering_functions.get_variant_page_conversion()
    })
    return( user_dict )

@bp.before_app_request
def before_request():
    '''
        this is executed BEFORE any request
    '''
    if current_user.is_anonymous:
        pass
    else:
        if current_user.is_authenticated:
            current_user.last_seen = datetime.utcnow()
            db.session.commit()
            g.search_form = SearchForm()



@bp.route('/tutorial', methods=['GET'])
def tutorial():
    SERVER_ADDRESS = current_app.config['SERVER_ADDRESS']
    return render_template('tutorial_DXcator.html', title='Tutorial',
                    SERVER_ADDRESS = SERVER_ADDRESS
                    )


@bp.route('/commandVEP', methods=['GET'])
def commandVEP():
    SERVER_ADDRESS = current_app.config['SERVER_ADDRESS']
    return render_template('commandVEP_DXcator.html', title='Tutorial',
                    SERVER_ADDRESS = SERVER_ADDRESS
                    )


######################################################################
############################# HOMEPAGE ###############################
######################################################################
@bp.route('/', methods=['GET', 'POST'])
@bp.route('/index', methods=['GET', 'POST'])
def index():
    SERVER_ADDRESS = current_app.config['SERVER_ADDRESS']
    return render_template('index_tutorial_DXcator.html', SERVER_ADDRESS = SERVER_ADDRESS, title='Home')


@bp.route('/project', methods=['GET', 'POST'])
@server_valid_authentication_required
@login_required
def project():
    '''
        this is the function to create a new project
    '''
    user = User.query.filter_by( server_username = current_user.server_username ).first_or_404()
    form = NewProjectForm(
        projectID = user.project_name or 'Tutorial Project',
        project_description = user.project_description or 'Simply a project for this tutorial',
        project_DX = user.project_diagnosis or 'Tutorial Syndrome',
        project_ICDS10 = user.project_icds_code or 'F0.0',
        project_assembly = user.project_assembly or 'hg38'
    )
    if form.validate_on_submit() :
        ### insert project in DB
        user.project_name = form.projectID.data
        user.project_description = form.project_description.data
        user.project_diagnosis = form.project_DX.data
        user.project_icds_code = form.project_ICDS10.data
        user.project_assembly = form.project_assembly.data
        user.project_created_on = datetime.utcnow()
        db.session.commit()
        flash("Project {0} successfully created!".format( user.project_name ), 'success')
        return( redirect( url_for('main.upload')))
    return( render_template('project_tutorial_DXcator.html',
                                title='Project',
                                form = form
                                ))


##################################################################
##################### MESSAGE-NOTIFICATION  ######################
##################################################################
@bp.route('/messages')
@login_required
@server_valid_authentication_required
def messages():
    SERVER_ADDRESS = current_app.config['SERVER_ADDRESS']
    current_user.last_message_read_time = datetime.utcnow()
    current_user.add_notification('unread_message_count', 0)
    db.session.commit()
    page = request.args.get('page', 1, type=int)
    messages = current_user.messages_received.order_by(
        Message.timestamp.desc()).paginate(
            page, current_app.config['MESSAGE_PER_PAGE'], False)
    next_url = url_for('main.messages', page=messages.next_num) \
        if messages.has_next else None
    prev_url = url_for('main.messages', page=messages.prev_num) \
        if messages.has_prev else None
    return render_template('messages_tutorial_DXcator.html', messages=messages.items,
                            SERVER_ADDRESS = SERVER_ADDRESS,
                            next_url=next_url, prev_url=prev_url)


from app.decorators import get_messages

@bp.route('/notifications')
@login_required
@get_messages
#@send_variants
def notifications():
    since = request.args.get('since', 0.0, type=float)
    if current_user.is_authenticated:
        notifications = current_user.notifications.filter(
                            Notification.timestamp > since).order_by(Notification.timestamp.asc())
        return jsonify([{
            'name': n.name,
            'data': n.get_data(),
            'timestamp': n.timestamp
        } for n in notifications])


#########################################################################
######################## UPDATE LOCAL KNOWN DB  #########################
#########################################################################
### this page merged with the intervalId JS function in base_DXcator.html page allows to update the local DB periodically
from app.variant_functions import update_known_variants_local_DB

@bp.route('/update_known_variants')
# @server_valid_authentication_required
def update_known_variants():
    if current_user.is_anonymous or current_app.login_manager._login_disabled or current_app.config['DEVELOPMENT_TESTING'] == True:
        return jsonify({ 'variants' : 0 })
    else:
        if current_user.is_authenticated:
            NUM_UPDATED = update_known_variants_local_DB()
        return jsonify({ 'variants' : NUM_UPDATED })


##################################################################
######################## UPLOAD-ANALYZE  #########################
##################################################################
@bp.route('/upload')
@project_required
@login_required
@server_valid_authentication_required
def upload():
    # flash(Markup('This must be a VEP annotated file, please read <a href="https://diagnosticator-000.ew.r.appspot.com" class="alert-link">documentation</a> for more info'), 'warning')
    files = os.listdir(current_app.config['UPLOAD_FOLDER'])
    PROJ_ASSEMBLY = current_user.project_assembly
    SERVER_ADDRESS = current_app.config['SERVER_ADDRESS']
    return( render_template('upload_tutorial_DXcator.html',
                                files=files,
                                PROJ_ASSEMBLY = PROJ_ASSEMBLY,
                                SERVER_ADDRESS = SERVER_ADDRESS
                            ) )


@bp.route('/upload_files', methods=['POST', 'GET'])
@project_required
@login_required
@server_valid_authentication_required
def upload_files():
    uploaded_file = request.files[ 'file' ]
    filename = secure_filename(uploaded_file.filename)
    if filename != '':
        file_ext = os.path.splitext(filename)[1]
        if file_ext not in current_app.config['ALLOWED_EXTENSIONS']:
            abort(400)
        uploaded_file.save(os.path.join( current_app.config['UPLOAD_FOLDER'], filename))
    return( redirect( url_for( 'main.upload' ) ) )


@bp.route('/pre_analyzeVCF/<filename>', methods=['POST', 'GET'])
@project_required
@login_required
@server_valid_authentication_required
def pre_analyzeVCF( filename ):
    SERVER_ADDRESS = current_app.config['SERVER_ADDRESS']
    body_dict = ({
        'line1' : {
                    'text' : 'Are you sure you want to analyze this file?',
                    'color' : 'grey',
                    'weight' : 'bold',
                    'size' : '100%'
                   },
        'line2' : {
                    'text' : 'If results were already generated for this project they will be overwritten',
                    'color' : 'red',
                    'weight' : 'bold',
                    'size' : '80%'
                   }
    })
    if 'choice' in request.form:
        choice = request.form['choice']
        if choice == 'Yes':
            current_user.project_variant_sent = False
            db.session.commit()
            return( redirect( url_for('main.analyzeVCF', filename = filename )))
        else:
            return( redirect( url_for('main.upload' )))
    return( render_template( 'yesNo_DXcator.html', body_dict = body_dict, SERVER_ADDRESS = SERVER_ADDRESS ))


from app.variant_functions import get_known_variants_from_DB

@bp.route('/analyzeVCF/<filename>')
@project_required
@login_required
@server_valid_authentication_required
def analyzeVCF( filename ):
    ### pull known variants from server
    # known_dict = get_known_variants()
    ### pull known variants from local DB
    known_dict = get_known_variants_from_DB()
    file_path = os.path.join( current_app.config['UPLOAD_FOLDER'], filename )
    ### this function creates the 3 dictionaries from the input VCF file
    if current_user.get_task_in_progress('analyzeVCF_task'):
        flash('An analyze VCF task is currently in progress. Wait it to finish...', 'warning')
    else:
        current_user.launch_task( 'analyzeVCF_task', 'Analyzing VCF {}...'.format( filename ), file_path, known_dict, url = current_app.config['REDIS_URL'], database = 2 )
        db.session.commit()
    return( redirect( url_for( 'main.upload' ) ) )

from app.main.forms import consequence_choices

@bp.route('/filterVCF/<filename>', methods=['POST', 'GET'])
@project_required
@login_required
@server_valid_authentication_required
def filterVCF( filename ):
    file_path = os.path.join( current_app.config['UPLOAD_FOLDER'], filename )
    SERVER_ADDRESS = current_app.config['SERVER_ADDRESS']
    form = FilterForm()
    CONSEQUENCES = []
    if form.validate_on_submit():
        filter_AF = form.filter_AF.data
        filter_AC = form.filter_AC.data
        filter_consequence = form.filter_consequence.data
        filter_GENELIST = form.filter_GENELIST.data
        filter_GENELIST_NAME = secure_filename( filter_GENELIST.filename )
        if filter_GENELIST:
            filter_GENELIST.save(os.path.join( current_app.config['UPLOAD_FOLDER'], filter_GENELIST_NAME))
        for C in filter_consequence:
            CONSEQUENCES.append( dict(consequence_choices)[C] )
        CONSEQUENCES_STRING = ','.join( map( str, CONSEQUENCES ) )
        INPUT_LIST = [ CONSEQUENCES_STRING, filename, filter_GENELIST_NAME, filter_AF ]
        INPUT_STRING = '\t'.join( map( str, INPUT_LIST ) )
        return( redirect(url_for( 'main.pre_filterVCF', filename=filename, INPUT_STRING = INPUT_STRING )))
    return( render_template( 'filterVCF_tutorial_DXcator.html', form = form, SERVER_ADDRESS = SERVER_ADDRESS ))


@bp.route('/pre_filterVCF/<filename>/<INPUT_STRING>', methods=['POST', 'GET'])
@project_required
@login_required
@server_valid_authentication_required
def pre_filterVCF( filename, INPUT_STRING ):
    SERVER_ADDRESS = current_app.config['SERVER_ADDRESS']
    body_dict = ({
        'line1' : {
                    'text' : 'Are you sure you want to analyze this file?',
                    'color' : 'grey',
                    'weight' : 'bold',
                    'size' : '100%'
                   },
        'line2' : {
                    'text' : 'If results were already generated for this project they will be overwritten',
                    'color' : 'red',
                    'weight' : 'bold',
                    'size' : '80%'
                   }
    })
    if 'choice' in request.form:
        choice = request.form['choice']
        if choice == 'Yes':
            current_user.project_variant_sent = False
            db.session.commit()
            with open( os.path.join( current_app.config['UPLOAD_FOLDER'], 'analisi0.input'), 'w' ) as F:
                F.write( INPUT_STRING )
            return( redirect( url_for('main.analyzeVCF_ASILO', filename = filename )))
        else:
            return( redirect( url_for('main.upload' )))
    return( render_template( 'yesNo_tutorial_DXcator.html', SERVER_ADDRESS = SERVER_ADDRESS, body_dict = body_dict ))




@bp.route('/analyzeVCF_ASILO/<filename>')
@project_required
@login_required
@server_valid_authentication_required
def analyzeVCF_ASILO( filename ):
    ### pull known variants from server
    known_dict = get_known_variants()
    file_path = os.path.join( current_app.config['UPLOAD_FOLDER'], filename )
    ### this function creates the 3 dictionaries from the input VCF file
    if current_user.get_task_in_progress('analyzeVCF_ASILO_task'):
        flash('An analyze VCF task is currently in progress. Wait it to finish...', 'warning')
    else:
        current_user.launch_task( 'analyzeVCF_ASILO_task', 'Analyzing VCF {}...'.format( filename ), file_path, known_dict, url = current_app.config['REDIS_URL'], database = 2 )
        db.session.commit()
    return( redirect( url_for( 'main.index' ) ) )



##################################################################
######################## SAMPLE-specific #########################
##################################################################
from app.variant_functions import load_VAR_SAMPLE_GENE_json_dict

TUTORIAL_ORDER = ([
    "CASE0_page",
    "X_107866056_G_C_page",
    "X_107866056_G_C_status",
    "CASE0_status",
    "CASE1_page",
    "chr5_94833131_G_A_page",
    "CASE2_status",
    "chr5_94833131_G_A_status",
    "chr16_2149869_CAG_C_page",
    "chr16_2149869_CAG_C_ACMG_page",
    "chr16_2149869_CAG_C_status",
    "CASE1_status",
    "CASE3_page",
    "chr13_32971124_CTG_C_page",
    "chr13_32971124_CTG_C_status",
    "CASE3_status",
    "CONTROL0_page",
    "CONTROL0_status",
    "message_seen",
    "tutorial_completed"
])

@bp.route('/patient_result', methods=['GET', 'POST'])
@server_valid_authentication_required
@login_required
@project_required
# @project_data_required
@update_known_variants_redis_DB
def patient_result():
    '''
        this is the function to display patients results
    '''
    USER_JSON_FOLDER = os.path.join( current_app.config['JSON_FOLDER'], current_user.server_username )
    variant_dict, sample_dict, gene_dict = load_VAR_SAMPLE_GENE_json_dict( USER_JSON_FOLDER )
    ### get number of P/LP variants for each sample
    sampleHTMLdict = diagnosticator_rendering_functions.getSamplesHTMLdict( sample_dict, variant_dict  )
    ### ensure ORDER for tutorial actions
    TODO = "NONE"
    for STEP in TUTORIAL_ORDER:
        if not getattr( current_user, STEP ):
            TODO = STEP
            break
    ### restore: UPDATE USER SET CASE0_page = 0, CASE1_page = 0, CASE3_page = 0, CONTROL0_page = 0, X_107866056_G_C_page = 0, X_107866056_G_C_status = 0, CASE0_status = 0, CASE1_status = 0, CASE3_status = 0, CONTROL0_status = 0, chr5_94833131_G_A_page = 0, chr16_2149869_CAG_C_page = 0, chr16_2149869_CAG_C_ACMG_page = 0, chr16_2149869_CAG_C_status = 0, chr13_32971124_CTG_C_page = 0, chr13_32971124_CTG_C_status = 0, tutorial_completed = 0, message_seen = 0 WHERE id = 1;sqlite> SELECT * from USER;
    return( render_template('patient_result_DXcator_tutorial.html',
                                title='Sample Result',
                                sampleHTMLdict = sampleHTMLdict,
                                TODO = TODO
                                ))

@bp.route('/tutorial_completed', methods=['GET', 'POST'])
@project_required
@login_required
@server_valid_authentication_required
# @project_data_required
@update_known_variants_redis_DB
def tutorial_completed( ):
    '''
        this is the function to close the tutorial final message
    '''
    current_user.tutorial_completed = True
    db.session.commit()
    ### consider communicate it to the server
    return( redirect( url_for( 'main.patient_result' ) ))


@bp.route('/patient_page/<sample_name>', methods=['GET', 'POST'])
@project_required
@login_required
@server_valid_authentication_required
# @project_data_required
@update_known_variants_redis_DB
def patient_page( sample_name ):
    '''
        this is the function to display single patient page
    '''
    USER_JSON_FOLDER = os.path.join( current_app.config['JSON_FOLDER'], current_user.server_username )
    variant_dict, sample_dict, gene_dict = load_VAR_SAMPLE_GENE_json_dict( USER_JSON_FOLDER )
    sample_dict = sample_dict[sample_name]
    # sample_dict = redis_functions.redis_dict_return( url = current_app.config['REDIS_URL'], database = 2, key_prefix = 'sam', key_value = sample_name )
    sample_dict = diagnosticator_rendering_functions.check_status_in_dict( sample_dict )
    sampleVar_dict = diagnosticator_rendering_functions.getSampleVariantsJSON( sample_dict, variant_dict )
    sampleVar_dict = diagnosticator_rendering_functions.orderDictByScore( sampleVar_dict )
    ### for the tutorial I need a single HTML page for each sample
    HTML_PAGE = 'patient_page_DXcator_' + sample_name.replace('-','') + '.html'
    ### record tutorial progress
    if sample_name == 'CASE-0':
        current_user.CASE0_page = True
        db.session.commit()
    if sample_name == 'CASE-1':
        current_user.CASE1_page = True
        db.session.commit()
    if sample_name == 'CASE-3':
        current_user.CASE3_page = True
        db.session.commit()
    if sample_name == 'CONTROL-0':
        current_user.CONTROL0_page = True
        db.session.commit()

    ### ensure tutorial order
    TODO = "NONE"
    for STEP in TUTORIAL_ORDER:
        if not getattr( current_user, STEP ):
            TODO = STEP
            break
    ### return PAGE
    try:
        return( render_template( HTML_PAGE,
                                    title = sample_name,
                                    sample_dict = sample_dict,
                                    sampleVar_dict = sampleVar_dict,
                                    sample_name = sample_name,
                                    TODO = TODO
                                    ))
    except:
        return( render_template( 'patient_page_DXcator.html',
                                    title = sample_name,
                                    sample_dict = sample_dict,
                                    sampleVar_dict = sampleVar_dict,
                                    sample_name = sample_name
                                    ))


@bp.route('/patient_change_status/<sample_name>/<new_status>', methods=['GET', 'POST'])
@project_required
@login_required
@server_valid_authentication_required
# @project_data_required
@update_known_variants_redis_DB
def patient_change_status( new_status, sample_name ):
    '''
        this is the function to change status to a patient
    '''
    # diagnosticator_rendering_functions.change_status( url = current_app.config['REDIS_URL'], key_prefix = 'sam', key_value = sample_name, new_status = new_status  )
    USER_JSON_FOLDER = os.path.join( current_app.config['JSON_FOLDER'], current_user.server_username )
    JSON_update_dict_element( 'SAMPLE', key_value = sample_name, subdict_name = 'STATUS', element_name = 'status', element_value = new_status, JSON_FOLDER = USER_JSON_FOLDER  )
    ### record tutorial progress
    if sample_name == 'CASE-0' and new_status == "AC":
        current_user.CASE0_status = True
        db.session.commit()
    if sample_name == 'CASE-1' and new_status == "AC":
        current_user.CASE1_status = True
        db.session.commit()
    if sample_name == 'CASE-3' and new_status == "SE":
        current_user.CASE3_status = True
        db.session.commit()
    if sample_name == 'CONTROL-0' and new_status == "RE":
        current_user.CONTROL0_status = True
        db.session.commit()
    flash( "sample {0} status successfully updated to: {1}".format( sample_name, diagnosticator_rendering_functions.get_classes_dict()[new_status]['description'] ), 'success' )
    return( redirect( url_for( 'main.patient_page', sample_name = sample_name )))







##################################################################
######################## VARIANT-specific ########################
##################################################################
@bp.route('/search_variant')
@server_valid_authentication_required
# @project_data_required
@project_required
@login_required
@update_known_variants_redis_DB
def search_variant():
    if not g.search_form.validate():
        return redirect(url_for('main.index'))
    return( redirect( url_for('main.variant_page', variant_name = g.search_form.q.data )))


from app.variant_functions import report_local_var

@bp.route('/variant_page/<variant_name>', methods=['GET', 'POST'])
@server_valid_authentication_required
@project_required
@login_required
# @project_data_required
@update_known_variants_redis_DB
def variant_page( variant_name ):
    '''
        this is the function to display single variant page
    '''
    # variant_dict = redis_functions.redis_dict_return( url = current_app.config['REDIS_URL'], database = 2, key_prefix = 'var', key_value = variant_name )
    USER_JSON_FOLDER = os.path.join( current_app.config['JSON_FOLDER'], current_user.server_username )
    variant_dict, sample_dict, gene_dict = load_VAR_SAMPLE_GENE_json_dict( USER_JSON_FOLDER )
    variant_dict = variant_dict[variant_name]
    sampleVARstatus_dict = diagnosticator_rendering_functions.get_samples_VAR_status_JSON( variant_name = variant_name, variant_dict = variant_dict, samples_dict = sample_dict )
    variant_dict = diagnosticator_rendering_functions.arrangeVARdict( variant_dict )
    ### for OMIM links
    OMIM_DB = os.path.join( current_app.config['BASEDIR'], 'DB', 'OMIM', 'mim2gene.txt' )
    GENE_OMIM_DICT = diagnosticator_rendering_functions.get_gene_omim_dict( OMIM_DB )
    LINKS_DICT = dict()
    if variant_dict['CHARS']['genename']:
        if GENE_OMIM_DICT[variant_dict['CHARS']['genename']]:
            LINKS_DICT.update({ 'OMIM' : "https://www.omim.org/entry/" + GENE_OMIM_DICT[variant_dict['CHARS']['genename']] })
    ### for GNOMAD and FRANKLIN and VARSOME link
    if current_user.project_assembly == 'hg19':
        GNOMAD_LINK = "https://gnomad.broadinstitute.org/variant/" + variant_name + "?dataset=gnomad_r2_1"
        FRANKLIN_LINK = "https://franklin.genoox.com/clinical-db/variant/snp/chr" + variant_name
        VARSOME_LINK = "https://varsome.com/variant/hg19/" + variant_name + "?annotation-mode=germline"
    elif current_user.project_assembly == 'hg38':
        GNOMAD_LINK = "https://gnomad.broadinstitute.org/variant/" + variant_name + "?dataset=gnomad_r3"
        FRANKLIN_LINK = "https://franklin.genoox.com/clinical-db/variant/snp/chr" + variant_name + "-hg38"
        VARSOME_LINK = "https://varsome.com/variant/hg38/" + variant_name + "?annotation-mode=germline"
    LINKS_DICT.update({ 'GNOMAD' : GNOMAD_LINK })
    LINKS_DICT.update({ 'FRANKLIN' : FRANKLIN_LINK })
    LINKS_DICT.update({ 'VARSOME' : VARSOME_LINK })
    if variant_dict['CLINVAR']['clinvar_id']:
        CLINVAR_LINK = "https://www.ncbi.nlm.nih.gov/clinvar/variation/" + variant_dict['CLINVAR']['clinvar_id'] + "/?new_evidence=true"
        LINKS_DICT.update({ 'CLINVAR' : CLINVAR_LINK })
    ### for dbSNP
    DBSNP_LINK = "https://www.ncbi.nlm.nih.gov/snp/?term=" + variant_name
    LINKS_DICT.update({ 'DBSNP' : DBSNP_LINK })
    ### for the tutorial I need a single HTML page for each sample
    HTML_PAGE = 'variant_page_DXcator_' + variant_name.replace('-','_') + '.html'
    ### record tutorial progress
    if variant_name == 'X-107866056-G-C':
        current_user.X_107866056_G_C_page = True
        db.session.commit()
    if variant_name == '5-94833131-G-A':
        current_user.chr5_94833131_G_A_page = True
        db.session.commit()
    if variant_name == '16-2149869-CAG-C':
        current_user.chr16_2149869_CAG_C_page = True
        db.session.commit()
    if variant_name == '13-32971124-CTG-C':
        current_user.chr13_32971124_CTG_C_page = True
        db.session.commit()

    ### ensure tutorial order
    TODO = "NONE"
    for STEP in TUTORIAL_ORDER:
        if not getattr( current_user, STEP ):
            TODO = STEP
            break
    #flash(TODO, 'success')
    try:
        return( render_template( HTML_PAGE,
                                        title = variant_name,
                                        variant_name =variant_name,
                                        variant_dict = variant_dict,
                                        sampleVARstatus_dict = sampleVARstatus_dict,
                                        LINKS_DICT = LINKS_DICT,
                                        TODO = TODO
                                        ))
    except:
        return( render_template('variant_page_DXcator.html',
                                    title = variant_name,
                                    variant_name =variant_name,
                                    variant_dict = variant_dict,
                                    LINKS_DICT = LINKS_DICT,
                                    sampleVARstatus_dict = sampleVARstatus_dict
                                    ))



from app.variant_functions import report_local_var, JSON_update_dict_element

@bp.route('/change_variant_sample_status/<sample_name>/<variant_name>/<new_status>', methods=['GET', 'POST'])
@project_required
@login_required
@server_valid_authentication_required
# @project_data_required
def change_variant_sample_status( sample_name, variant_name, new_status ):
    '''
        this is the function to update a variant status inside a sample
    '''
    report_statuses = get_report_statuses()
    # diagnosticator_rendering_functions.update_sampleVAR_status( variant_name, sample_name, new_status )
    if variant_name == "X-107866056-G-C" and sample_name == "CASE-0" and new_status == "AC" :
        current_user.X_107866056_G_C_status = True
        db.session.commit()
    if variant_name == "5-94833131-G-A" and sample_name == "CASE-1" and new_status == "RE" :
        current_user.chr5_94833131_G_A_status = True
        db.session.commit()
    if variant_name == "5-94833131-G-A" and sample_name == "CASE-2" and new_status == "AR" :
        current_user.CASE2_status = True
        db.session.commit()
    if variant_name == "16-2149869-CAG-C" and sample_name == "CASE-1" and new_status == "AC" :
        current_user.chr16_2149869_CAG_C_status = True
        db.session.commit()
    if variant_name == "13-32971124-CTG-C" and sample_name == "CASE-3" and new_status == "SE" :
        current_user.chr13_32971124_CTG_C_status = True
        db.session.commit()
    USER_JSON_FOLDER = os.path.join( current_app.config['JSON_FOLDER'], current_user.server_username )
    JSON_update_dict_element( 'SAMPLE', key_value = sample_name, subdict_name = 'STATUS', element_name = variant_name, element_value = new_status, JSON_FOLDER = USER_JSON_FOLDER )
    if new_status in report_statuses:
        flash("successfully updated variant: {0} status to {1}, for sample: {2}".format( variant_name, diagnosticator_rendering_functions.get_classes_dict()[new_status]['description'], sample_name ), 'success' )
        flash("this above is the message you will see, nothing is really reported in the tutorial :)", 'warning' )
    return( redirect( url_for( 'main.variant_page', variant_name = variant_name ) ))


@bp.route('/change_variant_sample_status_local/<sample_name>/<variant_name>/<new_status>', methods=['GET', 'POST'])
@project_required
@login_required
@server_valid_authentication_required
# @project_data_required
def change_variant_sample_status_local( sample_name, variant_name, new_status ):
    '''
        this is the function to update a variant status inside a sample
    '''
    if variant_name == "X-107866056-G-C" and sample_name == "CASE-0" and new_status == "AC" :
        current_user.X_107866056_G_C_status = True
        db.session.commit()
    if variant_name == "16-2149869-CAG-C" and sample_name == "CASE-1" and new_status == "AC" :
        current_user.X_107866056_G_C_status = True
        db.session.commit()
    if variant_name == "13-32971124-CTG-C" and sample_name == "CASE-3" and new_status == "SE" :
        current_user.X_107866056_G_C_status = True
        db.session.commit()
    try:
        USER_JSON_FOLDER = os.path.join( current_app.config['JSON_FOLDER'], current_user.server_username )
        JSON_update_dict_element( 'SAMPLE', key_value = sample_name, subdict_name = 'STATUS', element_name = variant_name, element_value = new_status, JSON_FOLDER = USER_JSON_FOLDER )
        # diagnosticator_rendering_functions.update_sampleVAR_status( variant_name, sample_name, new_status )
        flash("successfully updated variant: {0} status to {1}, for sample: {2}".format( variant_name, diagnosticator_rendering_functions.get_classes_dict()[new_status]['description'], sample_name ), 'success' )
        flash("this above is the message you will see, nothing is really reported in the tutorial :)", 'warning' )
    except:
        pass
    return( redirect( url_for( 'main.variant_page', variant_name = variant_name ) ))



##################################################################
######################### ACMG-specific ##########################
##################################################################
@bp.route('/acmg_page/<variant_name>', methods=['GET', 'POST'])
# @project_required
@login_required
@server_valid_authentication_required
# @project_data_required
@update_known_variants_redis_DB
def acmg_page( variant_name ):
    '''
        this is the function to display single variant ACMG page
    '''
    # variant_dict = redis_functions.redis_dict_return( url = current_app.config['REDIS_URL'], database = 2, key_prefix = 'var', key_value = variant_name )
    USER_JSON_FOLDER = os.path.join( current_app.config['JSON_FOLDER'], current_user.server_username )
    variant_dict, sample_dict, gene_dict = load_VAR_SAMPLE_GENE_json_dict( USER_JSON_FOLDER )
    variant_dict = variant_dict[variant_name]
    variant_dict = diagnosticator_rendering_functions.arrangeVARdict( variant_dict )
    varACMG = diagnosticator_rendering_functions.calculateACMG( variant_dict['ACMG'] )
    # redis_functions.redis_add_dict_element( url = current_app.config['REDIS_URL'], database = 2, key_prefix = 'var', key_value = variant_name, subdict_name = 'ACMG', element_name = 'ACMG', element_value = varACMG )
    variant_dict[ 'ACMG' ] = diagnosticator_rendering_functions.addACMGkeys( variant_dict['ACMG'] )
    HTML_PAGE = 'variantACMG_page_DXcator_' + variant_name.replace('-', '_') + '.html'
    if variant_name == "16-2149869-CAG-C":
        current_user.chr16_2149869_CAG_C_ACMG_page = True
        db.session.commit()
    try:
        return( render_template( HTML_PAGE,
                                    title = "ACMG: ".format( variant_name ),
                                    variant_dict = variant_dict,
                                    variant_name = variant_name,
                                    varACMG = varACMG,
                                    chr16_2149869_CAG_C_ACMG_page = 0
                                    ))
    except:
        return( render_template('variantACMG_page_DXcator.html',
                                    title = "ACMG: ".format( variant_name ),
                                    variant_dict = variant_dict,
                                    variant_name = variant_name,
                                    varACMG = varACMG
                                    ))



@bp.route('/acmg_criteria_modify/<variant_name>/<criteria>/<value>', methods=['GET', 'POST'])
@project_required
@login_required
@server_valid_authentication_required
# @project_data_required
def acmg_criteria_modify( variant_name, criteria, value ):
    '''
        this is the function to display single variant ACMG page
    '''
    # variant_dict = redis_functions.redis_dict_return( url = current_app.config['REDIS_URL'], database = 2, key_prefix = 'var', key_value = variant_name )
    USER_JSON_FOLDER = os.path.join( current_app.config['JSON_FOLDER'], current_user.server_username )
    variant_dict, sample_dict, gene_dict = load_VAR_SAMPLE_GENE_json_dict( USER_JSON_FOLDER )
    var_dict = variant_dict[variant_name]
    # redis_functions.redis_add_dict_element( url = current_app.config['REDIS_URL'], database = 2, key_prefix = 'var', key_value = variant_name, subdict_name = 'ACMG', element_name = criteria, element_value = value )
    JSON_update_dict_element( key_prefix = 'VAR', key_value = variant_name, subdict_name = 'ACMG', element_name = criteria, element_value = value, JSON_FOLDER = USER_JSON_FOLDER )
    ### recalculate overall ACMG classification
    # redis_functions.redis_add_dict_element( url = current_app.config['REDIS_URL'], database = 2, key_prefix = 'var', key_value = variant_name, subdict_name = 'ACMG', element_name = 'ACMG', element_value = diagnosticator_rendering_functions.calculateACMG( variant_dict['ACMG'] ) )
    JSON_update_dict_element( key_prefix = 'VAR', key_value = variant_name, subdict_name = 'ACMG', element_name = 'ACMG', element_value = diagnosticator_rendering_functions.calculateACMG( var_dict['ACMG'] ), JSON_FOLDER = USER_JSON_FOLDER )
    return( redirect( url_for( 'main.acmg_page',variant_name = variant_name ) ))



##################################################################
########################## GENE-specific #########################
##################################################################
@bp.route('/gene_page/<gene_name>', methods=['GET', 'POST'])
@project_required
@login_required
@server_valid_authentication_required
# @project_data_required
@update_known_variants_redis_DB
def gene_page( gene_name ):
    '''
        this is the function to display single gene variants
    '''
    # gene_dict = redis_functions.redis_dict_return( url = current_app.config['REDIS_URL'], database = 2, key_prefix = 'gen', key_value = gene_name )
    USER_JSON_FOLDER = os.path.join( current_app.config['JSON_FOLDER'], current_user.server_username )
    variant_dict, sample_dict, gene_dict = load_VAR_SAMPLE_GENE_json_dict( USER_JSON_FOLDER )
    gene_dict = gene_dict[gene_name]
    return( render_template( 'gene_page_DXcator.html',
                                gene_name = gene_name,
                                gene_dict = gene_dict
                ))


@bp.route('/gene_result', methods=['GET', 'POST'])
@project_required
@login_required
@server_valid_authentication_required
# @project_data_required
@update_known_variants_redis_DB
def gene_result( ):
    '''
        this is the function to display all gene results
    '''
    USER_JSON_FOLDER = os.path.join( current_app.config['JSON_FOLDER'], current_user.server_username )
    variant_dict, sample_dict, gene_dict = load_VAR_SAMPLE_GENE_json_dict( USER_JSON_FOLDER )
    geneHTMLdict = diagnosticator_rendering_functions.get_all_genes_dict_JSON( gene_dict, variant_dict )
    return( render_template( 'gene_result_DXcator.html',
                                geneHTMLdict = geneHTMLdict
                ))



@bp.route('/fake_message', methods=['GET', 'POST'])
@project_required
@login_required
@server_valid_authentication_required
# @project_data_required
@update_known_variants_redis_DB
def fake_message( ):
    '''
        this is the function to display a fake message in the tutorial
    '''
    current_user.message_seen = True
    db.session.commit()
    return( render_template( 'fake_message_DXcator.html',
                                variant_name = 'X-107866056-G-C'
                ))




@bp.route('/status_explanation', methods=['GET', 'POST'])
@project_required
@login_required
@server_valid_authentication_required
# @project_data_required
@update_known_variants_redis_DB
def status_explanation( ):
    return( render_template( 'status_explanation_DXcator.html'
                ))


@bp.route('/expected_results', methods=['GET', 'POST'])
@project_required
@login_required
@server_valid_authentication_required
# @project_data_required
@update_known_variants_redis_DB
def expected_results( ):
    return( render_template( 'expected_results_DXcator.html'
                ))

















##########################################################################
########################## API-server-specific ###########################
##########################################################################
@bp.route('/get_known_variants_from_server')
@project_required
@login_required
@server_valid_authentication_required
@project_data_required
def get_known_variants_from_server():
    known_dict = get_known_variants()
    if known_dict:
        flash(known_dict, 'info')
        flash("OK", 'success')
    else:
        flash("FAIL", 'danger')
    return( render_template('blank_DXcator.html'))



@bp.route('/send_variants_to_server')
@project_required
@login_required
@server_valid_authentication_required
@project_data_required
def send_variants_to_server():
    if send_local_variants() :
        flash("OK", 'success')
    else:
        flash("FAIL", 'danger')
    return( render_template('blank_DXcator.html'))



@bp.route('/get_server_messages')
@project_required
@login_required
@server_valid_authentication_required
@project_data_required
def get_server_messages():
    if get_server_new_messages_dict():
        flash("OK", 'success')
    else:
        flash("FAIL", 'danger')
    return( render_template('blank_DXcator.html'))









### ENDc
