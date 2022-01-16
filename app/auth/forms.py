from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo

class InsertPasswordRequestForm(FlaskForm):
    username = StringField('Server Username', validators=[DataRequired()])
    password = PasswordField('Server Password', validators=[DataRequired()])
    submit = SubmitField('Submit')
