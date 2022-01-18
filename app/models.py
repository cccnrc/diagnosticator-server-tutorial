import base64
from datetime import datetime, timedelta
from hashlib import md5
import json
import os
from time import time
from flask import current_app, url_for
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
import redis
import rq
from app import db, login
from flask_login import UserMixin

@login.user_loader
def load_user(id):
    return User.query.get(id)

class User( UserMixin, db.Model ):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    created_on = db.Column(db.DateTime, default=datetime.utcnow)
    last_seen = db.Column(db.DateTime)
    server_username = db.Column(db.String(140), index=True, unique=True)
    server_token = db.Column(db.String(32), index=True, unique=True)
    server_token_expiration = db.Column(db.DateTime)
    authenticated_on = db.Column(db.DateTime, nullable=True)
    notifications = db.relationship('Notification', backref='user', lazy='dynamic')
    project_name = db.Column(db.String(140))
    project_description = db.Column(db.String(256))
    project_diagnosis = db.Column(db.String(128))
    project_icds_code = db.Column(db.String(128))
    project_assembly = db.Column(db.String(6))
    project_created_on = db.Column(db.DateTime)
    project_vcf_filename = db.Column(db.String(256))
    project_variant_sent = db.Column(db.Boolean, default=False)
    last_message_read_time = db.Column(db.DateTime)
    CASE0_page = db.Column(db.Boolean, default=False)
    CASE1_page = db.Column(db.Boolean, default=False)
    CASE3_page = db.Column(db.Boolean, default=False)
    CONTROL0_page = db.Column(db.Boolean, default=False)
    X_107866056_G_C_page = db.Column(db.Boolean, default=False)
    X_107866056_G_C_status = db.Column(db.Boolean, default=False)
    CASE0_status = db.Column(db.Boolean, default=False)
    CASE1_status = db.Column(db.Boolean, default=False)
    CASE2_status = db.Column(db.Boolean, default=False)
    CASE3_status = db.Column(db.Boolean, default=False)
    CONTROL0_status = db.Column(db.Boolean, default=False)
    chr5_94833131_G_A_page = db.Column(db.Boolean, default=False)
    chr5_94833131_G_A_status = db.Column(db.Boolean, default=False)
    chr16_2149869_CAG_C_page = db.Column(db.Boolean, default=False)
    chr16_2149869_CAG_C_ACMG_page = db.Column(db.Boolean, default=False)
    chr16_2149869_CAG_C_status = db.Column(db.Boolean, default=False)
    chr13_32971124_CTG_C_page = db.Column(db.Boolean, default=False)
    chr13_32971124_CTG_C_status = db.Column(db.Boolean, default=False)
    message_seen =  db.Column(db.Boolean, default=False)
    tutorial_completed =  db.Column(db.Boolean, default=False)
    messages_received = db.relationship('Message',
                                        foreign_keys='Message.recipient_id',
                                        backref='recipient', lazy='dynamic')
    project_samples = db.relationship('Sample',
                                        foreign_keys='Sample.user_id',
                                        backref='user', lazy='dynamic')

    def __repr__(self):
        return '<User {}>'.format(self.server_username)

    def check_server_token(self):
        if self.server_token is None or self.server_token_expiration < datetime.utcnow():
            return False
        return True

    def new_messages(self):
        last_read_time = self.last_message_read_time or datetime(1900, 1, 1)
        return Message.query.filter_by(recipient_id=self.id).filter(
            Message.timestamp > last_read_time).count()

    def add_notification(self, name, data):
        self.notifications.filter_by(name=name).delete()
        n = Notification( name=name, payload_json=json.dumps(data), user_id=self.id)
        db.session.add(n)
        return n

    def launch_task(self, name, description, *args, **kwargs):
        rq_job = current_app.task_queue.enqueue( 'app.tasks.' + name, self.id,
                                                *args, **kwargs)
        task = Task( id=rq_job.get_id(), name=name, description=description,
                    user_id = self.id)
        db.session.add(task)
        return task

    def get_tasks_in_progress(self):
        return Task.query.filter_by(user_id=self.id, complete=False).all()

    def get_task_in_progress(self, name):
        return Task.query.filter_by(name=name, user_id=self.id, complete=False).first()



class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    recipient_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    body = db.Column(db.String(300))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)

    def __repr__(self):
        return '<Message {}>'.format(self.body)


class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    timestamp = db.Column(db.Float, index=True, default=time)
    payload_json = db.Column(db.Text)

    def get_data(self):
        return json.loads(str(self.payload_json))


class Task(db.Model):
    id = db.Column(db.String(36), primary_key=True)
    name = db.Column(db.String(128), index=True)
    description = db.Column(db.String(384))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    complete = db.Column(db.Boolean, default=False)

    def get_rq_job(self):
        try:
            rq_job = rq.job.Job.fetch(self.id, connection=current_app.redis)
        except (redis.exceptions.RedisError, rq.exceptions.NoSuchJobError):
            return None
        return rq_job

    def get_progress(self):
        job = self.get_rq_job()
        return job.meta.get('progress', 0) if job is not None else 100

class KnownVariants(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(400), index=True)
    assembly = db.Column(db.String(12))
    acmg_classification = db.Column(db.String(12))
    acmg_classification_num = db.Column(db.Integer)
    last_update = db.Column(db.DateTime, index=True, default=datetime.utcnow)

class Sample(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(400), index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    variants = db.relationship('Variant',
                                    foreign_keys='Variant.sample_id',
                                    backref='variant', lazy='dynamic')

class Variant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(400), index=True)
    sample_id = db.Column(db.Integer, db.ForeignKey('sample.id'))
