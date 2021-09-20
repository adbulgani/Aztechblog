import pymysql
from werkzeug.utils import secure_filename
from datetime import datetime
from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy
import bleach
from sqlalchemy.orm import backref
from sqlalchemy import desc
import base64,os
 
app = Flask(__name__)
app.config['UPLOAD_FOLDER']='static/posts'
app.config['SECRET_KEY']='b8425158b8a24903ebff91ed'

username = 'bloguser'
password ='Qwerty#1'
userpass = 'mysql+pymysql://' + username + ':' + password + '@'
server ='127.0.0.1:3306'
dbname = '/blog'
socket = '?unix_socket=/var/run/mysqld/mysqld.sock'

app.config['SQLALCHEMY_DATABASE_URI'] =  userpass + server + dbname + socket
app.config['SQLALCHEMY_TRACK_MODIFICATIONS']=True

db = SQLAlchemy(app)

class Post(db.Model):
    post_id = db.Column(db.Integer,primary_key=True)
    post_content = db.Column(db.Text,nullable=False)
    post_category = db.Column(db.String(50),default='general')
    date_posted =db.Column(db.DateTime,nullable=False,default=datetime.utcnow)
    like = db.Column(db.Boolean)
    post_title = db.Column(db.String(100),nullable=False)
    cover_image = db.Column(db.Text)
    comments = db.relationship('Comment',backref='comments',lazy=True)

    def __init__(self,post_title,post_content,post_category,date_posted,cover_image):
        self.cover_image =cover_image
        self.date_posted =date_posted
        self.post_title=post_title
        self.post_category=post_category
        self.post_content=post_content
        
    def __repr__(self):
        return f"Post('{self.post_content}', '{self.post_title}', '{self.date_posted}','{self.cover_image}','{self.like}','{self.post_id}')"

class Comment(db.Model):
    comment_id = db.Column(db.Integer,primary_key=True)
    comment = db.Column(db.Text,nullable=False)
    like = db.Column(db.Boolean)
    date_commented = db.Column(db.DateTime,nullable=False,default=datetime.utcnow)
    comment_post_id = db.Column(db.Integer,db.ForeignKey('post.post_id'),nullable=False)
    replies = db.relationship('Reply',backref='replies',lazy=True)

    def __repr__(self):
        return f"Comment('{self.comment_id}', '{self.comment_post_id}', '{self.date_commented}')"

class Reply(db.Model):
    reply_id = db.Column(db.Integer,primary_key=True)
    reply_text = db.Column(db.Text,nullable=False)
    date_replied = db.Column(db.DateTime,nullable=False,default=datetime.utcnow)
    reply_comment_id = db.Column(db.Integer,db.ForeignKey('comment.comment_id'),nullable=False)

    def __repr__(self):
        return f"Reply('{self.reply_id}', '{self.reply_comment_id}', '{self.date_replied}')"

@app.route("/gani")
def admin():
    return render_template('admin.html')

@app.route("/")
def Home():
    return render_template('index.html',display_post=Post.query.all())

@app.route("/about")
def About():
    return render_template('about.html')

@app.route("/categories")
def categories():
    post_categories=Post.query.with_entities(Post.post_category,Post.cover_image).distinct().all()
    return render_template('categories.html',post_categories=post_categories)

@app.route("/articles")
def articles():
    display_post = Post.query.order_by(desc(Post.post_id)).all()
    return render_template('article.html',display_post=display_post)

@app.route("/<id>")
def showpost(id):
    display_post = Post.query.get(id)
    return render_template('showpost.html',display_post=display_post)


@app.route("/",methods=["POST","GET"])
def post():
    if request.method == "POST":
        title = request.form.get("TITLE")
        content = request.form.get('content')
        content = bleach.clean(content,tags=['img','p','h1','h2','h3','a'],attributes={'img':['src']},protocols=['data']
        )
        category = request.form.get('categories')
        f =request.files['cover_image']
        f.save(os.path.join(app.config['UPLOAD_FOLDER'],secure_filename(f.filename)))
        url = f.filename
        post_data = Post(title, content, category, datetime.now(), url)
        db.session.add(post_data)
        db.session.commit()
        display_post = Post.query.order_by(desc(Post.date_posted)).all()
        return render_template('article.html',display_post=display_post)
if __name__ == '__main__':
    app.run(debug=True)
