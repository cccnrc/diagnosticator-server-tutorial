import json
import sys
import os
import time
from flask import render_template
from rq import get_current_job
from app import create_app, db
from app.models import User, Task, Message
import redis_functions
from asilo_variant_functions import mainCaller, update_var_dict_known
from convert_VCF_REDIS import VCF2REDIS
import time
import sys
from flask_login import current_user
from flask import current_app
import datetime


app = create_app()
app.app_context().push()


def _set_task_progress(progress):
    job = get_current_job()
    if job:
        job.meta['progress'] = progress
        job.save_meta()
        task = Task.query.get(job.get_id())
        user = User.query.get( task.user_id )
        user.add_notification('task_progress', {'task_id': job.get_id(),
                                                     'progress': progress})
        if progress >= 100:
            task.complete = True
        db.session.commit()



def send_message_notification( user_id, body ):
    user = User.query.get(user_id)
    if body:
        msg = Message( recipient_id = user_id, body=body )
        db.session.add(msg)
        user.add_notification('unread_message_count', user.new_messages())
        db.session.commit()
    else:
        print( "Empty Message Notification !!!" )




# app.tasks.analyzeVCF_task( user_id = 1, file_path = 'upload/merged.idter_M.norm.PASS.filtered.head1k.VEPoutput.vcf', known_dict = known_dict, url = current_app.config['REDIS_URL'], database = 3, pwd = None )
def analyzeVCF_ASILO_task( user_id, file_path, known_dict, url = None, database = 2, pwd = None ):
    if not url:
        url = current_app.config['REDIS_URL']
    try:
        user = User.query.get(user_id)
        _set_task_progress(0)
        print("analyzeVCF_task() : 0. check DB connection with redis_functions.redis_connect({})".format( url ))
        sys.stdout.flush()
        if redis_functions.redis_connect( url = url, database = database, pwd = pwd ):
            ### delete the DB if already exists
            redis_functions.redis_deleteDB( url = url, database = database, pwd = pwd )
            ASILO_OUT_DIR = os.path.join( current_app.config['UPLOAD_FOLDER'], 'analisi_result' )
            ASILO_OUT_FLAG = os.path.join( current_app.config['UPLOAD_FOLDER'], 'ASILO.NEW' )
            print("analyzeVCF_task() : 0. connection established, waiting for {0}".format( ASILO_OUT_DIR ))
            sys.stdout.flush()
            ### check for ASILO-DIR to exists
            time.sleep(10)
            while not os.path.exists(ASILO_OUT_DIR):
                print("analyzeVCF_task() : 0p. waiting for ASILO-DIR ...")
                time.sleep(10)
                sys.stdout.flush()
            while not datetime.datetime.fromtimestamp(os.stat(ASILO_OUT_DIR).st_mtime) > (datetime.datetime.now()-datetime.timedelta(seconds=30)):
                print("analyzeVCF_task() : 0p. waiting for ASILO-FLAG NEW...")
                time.sleep(10)
                sys.stdout.flush()
            '''
            ### check for ASILO-FLAG to be created
            while not os.path.exists(ASILO_OUT_FLAG):
                print("analyzeVCF_task() : 0p. waiting for ASILO-FLAG ...")
                time.sleep(10)
                sys.stdout.flush()
            ### check that ASILO_OUT_DIR is NEW (not an OLD one re-used)
            with open ( ASILO_OUT_FLAG, 'r') as F:
                FC = F.readlines()[0].rstrip('\n')
            FC_DT = datetime.datetime.strptime( FC, '%Y/%m/%d %H:%M:%S')
            while not datetime.datetime.fromtimestamp(os.stat(ASILO_OUT_DIR).st_mtime) > datetime.datetime.now()-datetime.timedelta(seconds=30):
                with open ( ASILO_OUT_FLAG, 'r') as F:
                    FC = F.readlines()[0].rstrip('\n')
                FC_DT = datetime.datetime.strptime( FC, '%Y/%m/%d %H:%M:%S')
                print("analyzeVCF_task() : 0p. waiting for ASILO-FLAG NEW...")
                time.sleep(10)
                sys.stdout.flush()
            '''
            _set_task_progress(10)
            print( redis_functions.redis_connect( url = url, database = database, pwd = pwd ) )
            print("analyzeVCF_task() : 1. calling VCF2REDIS() on {0}".format(ASILO_OUT_DIR))
            sys.stdout.flush()
            # var_dict, sample_dict, gene_dict = mainCaller( file_path )
            var_dict, sample_dict, gene_dict = VCF2REDIS( ASILO_OUT_DIR )
            _set_task_progress(50)
            if known_dict:
                print("analyzeVCF_task() : 2. update_var_dict_known() variants (known n. {})".format(len(known_dict)))
                var_dict = update_var_dict_known( var_dict, known_dict )
            else:
                print("analyzeVCF_task() : 2. update_var_dict_known() variants (known n. {})".format(0))
            sys.stdout.flush()
            _set_task_progress(60)
            print("analyzeVCF_task() : 3. insertDICT() variants (n. {})".format(len(var_dict)))
            sys.stdout.flush()
            vi = redis_functions.redis_dict_insert( url = url, database = database, d_dict = var_dict, key_prefix = 'var', pwd = pwd )
            _set_task_progress(70)
            sys.stdout.flush()
            ### insert samples in mongoDB
            print("analyzeVCF_task() : 4. insertDICT() samples (n. {})".format(len(sample_dict)))
            si = redis_functions.redis_dict_insert( url = url, database = database, d_dict = sample_dict, key_prefix = 'sam', pwd = pwd )
            _set_task_progress(85)
            ### insert variants in mongoDB
            print("analyzeVCF_task() : 5. insertDICT() genes (n. {})".format(len(gene_dict)))
            gi = redis_functions.redis_dict_insert( url = url, database = database, d_dict = gene_dict, key_prefix = 'gen', pwd = pwd )
            ### and notify user about work completed
            send_message_notification( user_id, "your VCF is analyzed!" )
            _set_task_progress(100)
        else:
            _set_task_progress(100)
            app.logger.error( '  - !!! ERROR !!! Impossible to create the connection to redis DB. Exiting ...', exc_info = sys.exc_info() )
    except:
        _set_task_progress(100)
        app.logger.error( 'Unhandled exception', exc_info = sys.exc_info() )

def analyzeVCF_task( user_id, file_path, known_dict, url = None, database = 2, pwd = None ):
    if not url:
        url = current_app.config['REDIS_URL']
    try:
        user = User.query.get(user_id)
        _set_task_progress(0)
        print("analyzeVCF_task() : 0. check DB connection with redis_functions.redis_connect({})".format( url ))
        sys.stdout.flush()
        if redis_functions.redis_connect( url = url, database = database, pwd = pwd ):
            ### delete the DB if already exists
            redis_functions.redis_deleteDB( url = url, database = database, pwd = pwd )
            _set_task_progress(10)
            print( redis_functions.redis_connect( url = url, database = database, pwd = pwd ) )
            print("analyzeVCF_task() : 0. connection established")
            ASILO_DIR = os.path.join( current_app.config['UPLOAD_FOLDER'], 'analisi_result' )
            print("analyzeVCF_task() : 1. calling VCF2REDIS() on {0}".format(ASILO_DIR))
            sys.stdout.flush()
            # var_dict, sample_dict, gene_dict = mainCaller( file_path )
            var_dict, sample_dict, gene_dict = VCF2REDIS( ASILO_DIR )
            _set_task_progress(50)
            print("analyzeVCF_task() : 2. update_var_dict_known() variants (known n. {})".format(len(known_dict)))
            sys.stdout.flush()
            _set_task_progress(60)
            var_dict = update_var_dict_known( var_dict, known_dict )
            print("analyzeVCF_task() : 3. insertDICT() variants (n. {})".format(len(var_dict)))
            sys.stdout.flush()
            vi = redis_functions.redis_dict_insert( url = url, database = database, d_dict = var_dict, key_prefix = 'var', pwd = pwd )
            _set_task_progress(70)
            sys.stdout.flush()
            ### insert samples in mongoDB
            print("analyzeVCF_task() : 4. insertDICT() samples (n. {})".format(len(sample_dict)))
            si = redis_functions.redis_dict_insert( url = url, database = database, d_dict = sample_dict, key_prefix = 'sam', pwd = pwd )
            _set_task_progress(85)
            ### insert variants in mongoDB
            print("analyzeVCF_task() : 5. insertDICT() genes (n. {})".format(len(gene_dict)))
            gi = redis_functions.redis_dict_insert( url = url, database = database, d_dict = gene_dict, key_prefix = 'gen', pwd = pwd )
            ### and notify user about work completed
            send_message_notification( user_id, "your VCF is analyzed!" )
            _set_task_progress(100)
        else:
            _set_task_progress(100)
            app.logger.error( '  - !!! ERROR !!! Impossible to create the connection to redis DB. Exiting ...', exc_info = sys.exc_info() )
    except:
        _set_task_progress(100)
        app.logger.error( 'Unhandled exception', exc_info = sys.exc_info() )


def check_redis_worker_message_user( user_id, url, database, pwd = None ):
    try:
        user = User.query.get(user_id)
        _set_task_progress(0)
        print("check_redis_worker() : 0. check DB connection with redis_functions.redis_connect({})".format( url ))
        redis_functions.redis_connect( url = url, database = database, pwd = pwd )
        sys.stdout.flush()
        _set_task_progress(50)
        print("check_redis_worker() : 1. sending message to user ({})".format( user.server_username ))
        send_message_notification( user_id, "your redis worker is working" )
        sys.stdout.flush()
        _set_task_progress(100)
    except:
        _set_task_progress(100)
        app.logger.error( 'Unhandled exception', exc_info = sys.exc_info() )
