from flask import Flask, request, redirect, render_template, flash, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.config['DEBUG'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://blogz:enter@localhost:8889/blogz'
app.config['SQLALCHEMY_ECHO'] = True
db = SQLAlchemy(app)

class Blog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(30))
    body = db.Column(db.Text)
    pub_date = db.Column(db.DateTime)
    master_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __init__(self, title, body, master, pub_date=None):
        self.title = title
        self.body = body
        
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(60), unique=True)
    password = db.Column(db.String(60))
    blogs = db.relationship('Blog', backref='master')

    def __init__(self, username, password):
        self.username = username
        self.password = password

@app.before_request
def require_login():
    allowed_routes = ['login', 'signup', 'index', 'blog']
    if request.endpoint not in allowed_routes and 'username' not in session:
        return redirect('/login')
    
@app.route('/')
def index():
    users = User.query.all()
    return render_template('index.html', users=users, header='Blog Users')

@app.route('/blog')
def blog():
    posts = Blog.query.all()
    blog_id = request.args.get('id')
    user_id = request.args.get('user')
    
    if user_id:
        posts = Blog.query.filter_by(master_id=user_id)
        return render_template('user.html', posts=posts, header="User Posts")
    if blog_id:
        post = Blog.query.get(blog_id)
        return render_template('entry.html', post=post )

    return render_template('blog.html', posts=posts, header='All Blog Posts')

@app.route('/newpost', methods=['POST', 'GET'])
def new_post(): 
    master = User.query.filter_by(username=session['username']).first()
    
    if request.method == 'POST':
        blog_title = request.form['blog-title']
        blog_body = request.form['blog-entry']
        title_error = ''
        body_error = ''

        if not blog_title:
            title_error = "Please enter blog title"
        if not blog_body:
            body_error = "Please enter blog entry"

        if not body_error and not title_error:
            new_entry = Blog(blog_title, blog_body, master)     
            db.session.add(new_entry)
            db.session.commit()        
            return redirect('/blog?id={}'.format(new_entry.id)) 
        else:
            return render_template('newpost.html', header='Blog Entry', title_error=title_error, 
                body_error=body_error, blog_title=blog_title, blog_body=blog_body)
    
    return render_template('newpost.html', header='Blog Entry')

@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method =='POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()
        if user and user.password == password:
            session['username'] = username
            flash('Logged in')
            return redirect('/newpost')
        else:
            flash('User password is incorrect, or user does not exist', 'error')
    
    return render_template('login.html', header='Login')

@app.route('/signup', methods=['POST', 'GET'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        verify = request.form['verify']

        existing_user = User.query.filter_by(username=username).first()

        if password != verify:
            flash('Passwords do not match', "error")
        elif len(username) < 2 or len(password) < 2:
            flash('Username and password must be more than 2 characters', 'error')
        elif existing_user:
            flash('User already exists', 'error')
        else:
            new_user = User(username, password)
            db.session.add(new_user)
            db.session.commit()
            session['username'] = username
            return redirect('/newpost')

    return render_template('signup.html', header='Signup')

@app.route('/logout')
def logout():
    del session['username']
    return redirect('/blog') 

if  __name__ == "__main__":
    app.run()