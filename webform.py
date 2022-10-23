from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField ,IntegerField,EmailField,PasswordField , BooleanField, ValidationError, TextAreaField
from wtforms.validators import DataRequired, EqualTo, Length
from wtforms.widgets import TextArea
from flask_ckeditor import CKEditorField
from flask_wtf.file import FileField

# blog post form
class PostForm(FlaskForm):
    title = StringField("Title",validators=[DataRequired()])
    #content = StringField("Content",validators=[DataRequired()], widget =TextArea())
    content = CKEditorField("Content",validators=[DataRequired()], widget =TextArea())
    slug = StringField("Slug",validators=[DataRequired()])
    submit = SubmitField("Submit")

# login form
class LoginForm(FlaskForm):
    username = StringField("Username",validators=[DataRequired()])
    password_hash = PasswordField("Password",validators=[DataRequired()])
    submit = SubmitField("Submit")

# Create register form
class UserForm(FlaskForm):
    username = StringField("Username",validators=[DataRequired()])
    name = StringField("Name",validators=[DataRequired()])
    email = EmailField("Email",validators=[DataRequired()])
    about_author = TextAreaField("About author")
    password_hash = PasswordField("Password",validators=[DataRequired(), EqualTo("password_hash2", message ="Passwords must Match!")])
    password_hash2 = PasswordField("Confirm Password",validators=[DataRequired()])
    profile_pic = FileField("Profile Pic")
    submit = SubmitField("Submit")

# Create a form class
class NamerForm(FlaskForm):
    name = StringField("What's your name",validators=[DataRequired()])
    submit = SubmitField("Submit")

# Create a form buy stock
class buyForm(FlaskForm):
    shares = IntegerField("Shares",validators=[DataRequired()])
    submit = SubmitField("Submit")

class PasswordForm(FlaskForm):
    email = StringField("Email",validators=[DataRequired()])
    password_hash = StringField("Password",validators=[DataRequired()])
    submit = SubmitField("Submit")

# search form
class SearchForm(FlaskForm):
    searched = StringField("Searched",validators=[DataRequired()])
    submit = SubmitField("Submit")

# quote form
class QuoteForm(FlaskForm):
    symbol = StringField("Symbol",validators=[DataRequired()])
    submit = SubmitField("Submit")

# sell form 
class SellForm(FlaskForm):
    symbol = StringField("Symbol",validators=[DataRequired()])
    shares = IntegerField("Shares",validators=[DataRequired()])
    submit = SubmitField("Submit")