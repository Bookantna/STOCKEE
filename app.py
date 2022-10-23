import os
from sqlite3 import Timestamp
from flask import Flask, render_template,url_for, request, redirect, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
from datetime import datetime , date
from werkzeug.security import generate_password_hash, check_password_hash
from flask_migrate import Migrate
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
from flask_ckeditor import CKEditor
from helper import get_file_contents, lookup
from webform import PostForm, LoginForm, UserForm, NamerForm, buyForm, PasswordForm, SearchForm, QuoteForm, SellForm
from werkzeug.utils import secure_filename
import uuid as uuid



app = Flask(__name__)
app.config['SECRET_KEY'] = "1111"
ckeditor = CKEditor(app)

#My old database
#app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
#app.config['SQLALCHEMY_BINDS'] = {"financial":'sqlite:///financial.db'}

#My new database
#heroku database
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://pmlaaarovymdwx:ba29b0b450e6f4e30838479f0030fb266ec75375912b29e85ab02ac687a4d0ab@ec2-52-70-45-163.compute-1.amazonaws.com:5432/deh71f0qqb2083'

#MySql database 
#app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:password123@localhost/our_users'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

UPLOAD_FOLDER = 'static/images/'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

db = SQLAlchemy(app)
migrate = Migrate(app, db) # To migrate use command flask db migrate -m 'Your MM' 
                           # flask db upgrade for changes.... migrate uses for when you want to add something to database 

#Flask_login stuff 
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return users.query.get(int(user_id))

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
            user = users(username=form.username.data, name=form.name.data, email = form.email.data, password_hash = hashed_pw)
            db.session.add(user)
            db.session.commit()
        # send username and email to continue the site
        username = form.username.data
        email = form.email.data
        # clear username, email, favorite color and password_hash
        form.username.data = '' 
        form.name.data = '' 
        form.email.data = ''
        form.password_hash.data = ''
        flash("User Added Successfully")
    our_users = users.query.order_by(users.date_added)
    return render_template('add_user.html',form = form, username = username, email = email, our_users = our_users)

@app.route('/update/<int:id>', methods = ['POST','GET'])
@login_required
def update(id):
    form = UserForm()
    name_to_update = users.query.get_or_404(id)
    if request.method == 'POST':
        name_to_update.name = request.form['name']
        name_to_update.username = request.form['username']
        name_to_update.email = request.form['email']
        try:
            db.session.commit()
            flash('User Updated Successfully')
            return render_template('update.html',form = form, name_to_update = name_to_update, id = id)
        except:
            flash('Error try again')
            return render_template('update.html',form = form,name_to_update = name_to_update)
    else:
        return render_template('update.html',form = form, name_to_update = name_to_update, id = id)

@app.route("/quote", methods = ["GET", "POST"])
@login_required
def quote():
    form = QuoteForm()
    if form.validate_on_submit():
        stocks = lookup(form.symbol.data)
        if stocks == None:
            flash('Please type your symbol properly')
        else: 
            return redirect(url_for('buy',symbol =  stocks['symbol']))
    return render_template('quote.html', form = form) 

@app.route("/buy/<symbol>", methods = ["GET", "POST"])
@login_required
def buy(symbol):
    stocks = lookup(symbol)
    form = buyForm()
    history = financial.query.order_by(financial.date_time)
    if form.validate_on_submit():
        id = current_user.id
        buy = financial(trader_id = id, symbol = symbol, status = 'BUY', cost = float(form.shares.data * stocks['price']), shares = form.shares.data)
        user = users.query.get_or_404(id)
        if user.money < float(form.shares.data * stocks['price']):
            flash("You don't have enough money to process this transaction")
        else:
            user.money = float(user.money) - float(form.shares.data * stocks['price'])
            form.shares.data = ''
            db.session.add(user)
            db.session.add(buy)
            db.session.commit()
            flash("Your transaction has been completed !!")
    return render_template('buy.html', history = history,stocks = stocks,form = form)

@app.route("/transaction", methods = ["GET", "POST"])
@login_required
def transaction():
    trader =  financial.query.filter(financial.trader_id == current_user.id)
    sum_shares_owned = db.session.execute(f"SELECT SUM(shares) as sum_shares ,symbol FROM financial where trader_id = {current_user.id} Group by symbol;")
    return render_template('transaction.html',trader = trader, sum_shares_owned = sum_shares_owned)

@app.route("/sell", methods = ["GET", "POST"])
@login_required
def sell():
    form = SellForm()
    sum_shares_owned = db.session.execute(f"SELECT SUM(shares) as sum_shares ,symbol FROM financial where trader_id = {current_user.id} Group by symbol;")
    if form.validate_on_submit():
        stocks = lookup(form.symbol.data)
        id = current_user.id
        sell = financial(trader_id = id, symbol = form.symbol.data, status = 'SELL', cost = float(form.shares.data * stocks['price']), shares = int(-form.shares.data))
        user = users.query.get_or_404(id)
        user.money = float(user.money) + float(form.shares.data * stocks['price'])
        db.session.add(sell)
        db.session.add(user)
        db.session.commit()
    return render_template('sell.html',form = form, sum_shares_owned = sum_shares_owned)

@app.route("/delete/<int:id>", methods = ["GET", "POST"])
@login_required
def delete(id):
    if id == current_user.id:
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
    else:
        flash("Sorry you can't delete other user")
        return redirect(url_for('dashboard'))

@app.route("/add_post", methods = ["POST","GET"])
@login_required
def add_post():
    form = PostForm()

    if form.validate_on_submit():
        poster = current_user.id
        post = Posts(title = form.title.data, content = form.content.data, poster_id = poster, slug = form.slug.data)

        # clear form
        form.title.data = ''
        form.content.data = ''
        form.slug.data = ''

        # add post data to database
        db.session.add(post)
        db.session.commit()
        flash("Blog post Submitted Successfully")
    return render_template('add_post.html', form = form)

@app.route("/posts", methods = ["POST","GET"])
@login_required
def posts():
    #Grab all the posts from database
    posts = Posts.query.order_by(Posts.date)
    return render_template('posts.html',posts = posts)

@app.route("/posts/<int:id>", methods = ["POST","GET"])
def post(id):
    post = Posts.query.get_or_404(id)
    return render_template('post.html', post = post)

@app.route("/post/edit/<int:id>", methods = ["POST","GET"])
@login_required
def edit_post(id):
    post = Posts.query.get_or_404(id)
    form = PostForm()
    if form.validate_on_submit():
        post.title = form.title.data
        post.content = form.content.data
        post.slug = form.slug.data
        #update database 
        db.session.add(post)
        db.session.commit()
        flash("Post has been updated successfully")
        return redirect(url_for('posts', post = post, form = form))

    if current_user.id == post.poster.id:
        form.slug.data = post.slug
        form.content.data = post.content
        form.title.data = post.title
        return render_template('edit_post.html',form = form)

    else: 
        flash("You aren't authorized to edit this post")
        posts = Posts.query.order_by(Posts.date)
        return render_template('posts.html', posts = posts)

@app.route('/posts/delete/<int:id>' , methods = ['POST','GET'])
@login_required
def delete_post(id):
    post_to_delete = Posts.query.get_or_404(id)
    id = current_user.id
    form = PostForm()
    if id == post_to_delete.poster.id:
        try:
            db.session.delete(post_to_delete)
            db.session.commit()

            #return message 
            posts = Posts.query.order_by(Posts.date)
            flash("Blog Post was deleted")
            return render_template('posts.html', posts = posts)
        except:
            flash("There was an error deleting Blog Post")

            return redirect(url_for('posts', post = post, form = form))
    else:
        flash("You aren't authorized to delete this post")
        posts = Posts.query.order_by(Posts.date)
        return render_template('posts.html',posts = posts)


@app.route('/login', methods = ['POST','GET'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = users.query.filter_by(username=form.username.data).first()
        if user:
            #check hash
            if check_password_hash(user.password_hash, form.password_hash.data):
                login_user(user)
                flash("Login Succesfull")
                return redirect(url_for('dashboard'))
            else:
                flash("Wrong password Try again!!")
        else:
            flash("User doesn't exist!!")

    return render_template('login.html', form = form)

@app.route('/logout', methods = ['POST','GET'])
@login_required
def logout():
    logout_user()
    flash("You have been logged out")
    return redirect(url_for('login'))
    

@app.route('/dashboard', methods = ['POST','GET'])
@login_required
def dashboard():
    form = UserForm()
    id = current_user.id
    name_to_update = users.query.get_or_404(id)
    if request.method == 'POST':
        name_to_update.name = request.form['name'] # form.name.data
        name_to_update.username = request.form['username']
        name_to_update.email = request.form['email']
        name_to_update.profile_pic = request.files['profile_pic']
        name_to_update.about_author = request.form['about_author']

        # grab image name 
        pic_filename = secure_filename(name_to_update.profile_pic.filename)

        # set uuid 
        pic_name = str(uuid.uuid1()) + '_' + pic_filename

        #save image
        #name_to_update.profile_pic.save(os.path.join(app.config['UPLOAD_FOLDER'], pic_name))

        # save pic_name to the database 
        name_to_update.profile_pic = pic_name

        try:
            db.session.commit()
            flash('User Updated Successfully')
            return render_template('dashboard.html',form = form, name_to_update = name_to_update, id = id)
        except:
            flash('Error try again')
            return render_template('dashboard.html',form = form,name_to_update = name_to_update)
    else:
        return render_template('dashboard.html',form = form, name_to_update = name_to_update, id = id)
    #return render_template('dashboard.html')

#pass stuff to navbar
@app.context_processor
def base_file():
    form = SearchForm()
    return dict(form = form)

@app.route('/search', methods = ['POST'])
def search():
    form = SearchForm()
    if form.validate_on_submit():
        post_searched = form.searched.data
        if post_searched == None:
            return render_template('search.html',form = form, searced = post_searched, posts = posts)
        posts = Posts.query.filter(Posts.content.like('%' + post_searched + '%'))
        posts = posts.order_by(Posts.title).all()
        return render_template('search.html',form = form, searced = post_searched, posts = posts)

@app.route('/admin')
@login_required
def admin():
    id = current_user.id
    if id == 1:
         return render_template('admin.html')
    else:
        flash("You are not allowed to access this page !!")
        return redirect(url_for('dashboard'))
# Json Api 
@app.route('/date')
def get_current_date():
    favorite_pizza = {
        "John" : "Pepperoni",
        "Mary" : "Cheese",
        "Lace" : "PineApple"
    }
    return favorite_pizza

@app.route('/git_command', methods = ['POST','GET'])
def git_command():
    return render_template('git_command.html')

#error pages
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def Internal_error(e):
    return render_template('500.html'), 500

#database model

# Blog post model 
class Posts(db.Model):
    id = db.Column(db.Integer, primary_key = True, nullable=False)
    title = db.Column(db.String(255))
    content = db.Column(db.Text())
    #author = db.Column(db.String(255))
    date = db.Column(db.DateTime, default = datetime.utcnow)
    slug = db.Column(db.String(255))
    #foreign key to link users (refer to primary key)
    poster_id = db.Column(db.Integer, db.ForeignKey('users.id'))


class users(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255), nullable=False, unique=True)
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), nullable=False, unique=True)
    about_author = db.Column(db.Text(), nullable=True)
    password_hash = db.Column(db.String(259), nullable=False)
    money = db.Column(db.Integer, nullable=False, default = 10000)
    profile_pic = db.Column(db.String(), nullable=True)
    favorite_color = db.Column(db.String(255)) # Delete later
    date_added = db.Column(db.DateTime,default=datetime.utcnow, nullable=False)
    # user can have many posts
    posts = db.relationship('Posts', backref = 'poster')  
    # user trade 
    trade = db.relationship('financial', backref = 'trader')   

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
    id = db.Column(db.Integer, primary_key=True, nullable=False) # transaction id 
    shares = db.Column(db.Integer, nullable = False)
    symbol = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(255), nullable=False)
    cost = db.Column(db.Float(), nullable=False)
    date_time = db.Column(db.DateTime,default=datetime.utcnow, nullable=False)
    #foreign key to link users (refer to primary key)
    trader_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    
if __name__ == '__main__':
    app.run(debug=True)


# tell heroku we have a database 
# heroku addons:create heroku-postgresql:hobby-dev --app stockeesite