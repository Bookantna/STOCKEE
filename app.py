from sqlite3 import Timestamp
from flask import Flask,render_template,url_for,request,redirect,flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField ,IntegerField,EmailField,PasswordField , BooleanField, ValidationError
from wtforms.validators import DataRequired, EqualTo, Length
from flask_migrate import Migrate
import os
from helper import get_file_contents, lookup

app = Flask(__name__)
app.config['SECRET_KEY'] = "1111"

if not get_file_contents('Api_key.txt'): # IEX api_key I stored my key in txt file if it is not found raise exception 
    raise Exception("Missing API_KEY")
    
#My old database
#app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
#My new database
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:password123@localhost/our_users'
app.config['SQLALCHEMY_BINDS'] = {"financial":'sqlite:///financial.db'}
db = SQLAlchemy(app)
migrate = Migrate(app, db) # To migrate use command flask db migrate -m 'Your MM' 
                           # flask db upgrade for changes.... migrate uses for when you want to add something to database 


class users(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), nullable=False, unique=True)
    password_hash = db.Column(db.String(259), nullable=False)
    favorite_color = db.Column(db.String(255))
    date_added = db.Column(db.DateTime,default=datetime.utcnow, nullable=False)
    #password hash
    @property
    def password(self):
        raise AttributeError("Password is not a readable Attribute")

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def verify_password(self, password):
        return check_password_hash(self.password_hash,password)

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
# Create register form
class UserForm(FlaskForm):
    username = StringField("Username",validators=[DataRequired()])
    email = EmailField("Email",validators=[DataRequired()])
    favorite_color = StringField("Favorite Color",validators=[DataRequired()])
    password_hash = PasswordField("Password",validators=[DataRequired(), EqualTo("password_hash2", message ="Passwords must Match!")])
    password_hash2 = PasswordField("Confirm Password",validators=[DataRequired()])
    submit = SubmitField("Submit")

# Create a form class
class NamerForm(FlaskForm):
    name = StringField("What's your name",validators=[DataRequired()])
    submit = SubmitField("Submit")
# Create a form buy stock
class buy(FlaskForm):
    symbol = StringField("Symbol",validators=[DataRequired()])
    shares = IntegerField("Shares",validators=[DataRequired()])
    submit = SubmitField("Submit")

class PasswordForm(FlaskForm):
    email = StringField("Email",validators=[DataRequired()])
    password_hash = StringField("Password",validators=[DataRequired()])
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
        flash("Form Summitted Successfully")
    return render_template('name.html',name = name, form = form)

@app.route('/test_pw', methods = ['GET','POST'])
def test_pw():
    email = None
    password = None
    pw_to_check = None
    passed = None
    form = PasswordForm()
    # Validation Form
    if form.validate_on_submit():
        email = form.email.data
        password = form.password_hash.data
        form.email.data = ''
        form.password_hash.data = ''
        pw_to_check = users.query.filter_by(email=email).first()
        #flash("Form Summitted Successfully")
        passed = check_password_hash(pw_to_check.password_hash, password)

    return render_template('test_pw.html',email = email, form = form, password = password, pw_to_check = pw_to_check, passed = passed)

@app.route('/user/add',methods=['POST','GET'])
def add_user():
    username = None
    email = None
    form = UserForm()
    if form.validate_on_submit():
        user = users.query.filter_by(email=form.email.data).first()
        if user is None:
            #Hash password 
            hashed_pw = generate_password_hash(form.password_hash.data, 'sha256')
            #user add to database
            user = users(username=form.username.data, email = form.email.data, favorite_color= form.favorite_color.data, password_hash = hashed_pw)
            db.session.add(user)
            db.session.commit()
        # send username and email to continue the site
        username = form.username.data
        email = form.email.data
        form.username.data = '' # clear username, email, favorite color and password_hash
        form.email.data = ''
        form.favorite_color.data = ''
        form.favorite_color.data = ''
        form.password_hash.data = ''
        flash("User Added Successfully")
    our_users = users.query.order_by(users.date_added)
    return render_template('add_user.html',form = form, username = username, email = email, our_users = our_users)

@app.route('/update/<int:id>', methods = ['POST','GET'])
def update(id):
    form = UserForm()
    name_to_update = users.query.get_or_404(id)
    if request.method == 'POST':
        name_to_update.username = request.form['username']
        name_to_update.email = request.form['email']
        name_to_update.favorite_color = request.form['favorite_color']
        try:
            db.session.commit()
            flash('User Updated Successfully')
            return render_template('update.html',form = form,name_to_update = name_to_update, id = id)
        except:
            flash('Error try again')
            return render_template('update.html',form = form,name_to_update = name_to_update)
    else:
        return render_template('update.html',form = form,name_to_update = name_to_update, id = id)

@app.route("/quote", methods = ["GET", "POST"])
def quote():
    if request.method == 'POST':
        stocks = lookup(request.form.get('symbol'))
        if stocks == None:
            flash('Please type your quote properly')
        return render_template('quote.html',stocks = stocks)  
    else:
       return render_template('quote.html')   

@app.route("/delete/<int:id>", methods = ["GET", "POST"])
def delete(id):
    username = None
    email = None
    form = UserForm()
    user_to_delete = users.query.get_or_404(id)
    try:
        db.session.delete(user_to_delete)
        db.session.commit()
        flash("User Deleted Successfully")
        our_users = users.query.order_by(users.date_added)
        return render_template('add_user.html',form = form, username = username, email = email, our_users = our_users)

    except:
        flash("Oops there was an error deleting")

#error pages
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def Internal_error(e):
    return render_template('500.html'), 500

if __name__ == '__main__':
    app.run(debug=True)