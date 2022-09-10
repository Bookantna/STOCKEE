from sqlite3 import Timestamp
from flask import Flask,render_template,url_for,request,redirect
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired

app = Flask(__name__)
app.config['SECRET_KEY'] = "1111"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_BINDS'] = {"financial":'sqlite:///financial.db'}
db = SQLAlchemy(app)

class users(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255), nullable=False)
    password = db.Column(db.String(15), nullable=False)

    def __repr__(self):
        return '<Task %r> % self.id'
        
class financial(db.Model):
    _bind_key_ = 'financial' 
    id = db.Column(db.Integer, primary_key=True)
    status = db.Column(db.String(255), nullable=False)
    money = db.Column(db.Integer, nullable=False)
    time = db.Column(db.Time, nullable=False)
    date = db.Column(db.Date, nullable=False)

    def __repr__(self):
        return '<Task %r> % self.id'
        
# Create a form class
class NamerForm(FlaskForm):
    name = StringField("What's your name",validators=[DataRequired()])
    submit = SubmitField("Submit")

@app.route('/', methods= ['POST','GET'])
def index():
    return render_template('index.html')

@app.route('/user/<name>', methods= ['POST','GET'])
def user(name):
    return render_template('user.html',user_name=name)

@app.route('/name', methods = ['GET','POST'])
def name():
    name = None
    form = NamerForm()
    # Validation Form
    if form.validate_on_submit():
        name = form.name.data
        form.name.data = ''
    return render_template('name.html',name = name, form = form)

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def Internal_error(e):
    return render_template('500.html'), 500

if __name__ == '__main__':
    app.run(debug=True)