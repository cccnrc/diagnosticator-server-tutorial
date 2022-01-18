from flask import request
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField, RadioField, SelectField, SelectMultipleField, FloatField, IntegerField, FileField
from wtforms.validators import ValidationError, DataRequired, Length
from flask_wtf.file import FileField, FileAllowed, FileRequired


class UploadForm(FlaskForm):
    file = FileField('File')
    submit = SubmitField('Submit')
