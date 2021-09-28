from operator import pos
from flask.scaffold import _matching_loader_thinks_module_is_package
import pymysql
from sqlalchemy.sql.expression import null
from werkzeug.utils import redirect, secure_filename
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

    def __init__(self,comment,date_commented,comment_post_id,like):
        self.comment=comment
        self.date_commented=date_commented
        self.comment_post_id=comment_post_id
        self.like=like

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
    posts = Post.query.all()
    return render_template('admin.html',posts=posts)

@app.route("/")
def Home():
    top_post=Post.query.order_by(desc(Post.date_posted)).limit(2)
    return render_template('index.html',display_post=Post.query.all(),top_post=top_post)

@app.route("/about")
def About():
    return render_template('about.html')

@app.route("/categories")
def categories():
    posts=Post.query.all()
    i = len(posts)
    gen=[]
    iot=[]
    soft=[]
    life=[]
    for post in posts:
        if post.post_category == 'General':
            gen.append(post)
        elif post.post_category == 'IoT':
            iot.append(post)
        elif post.post_category == 'Software':
            soft.append(post)
        else:
            life.append(post)    
    return render_template('categories.html',gen=gen,iot=iot,soft=soft,life=life)

@app.route("/articles")
def articles():
    page=request.args.get('page',1,type=int)
    display_post = Post.query.order_by(desc(Post.date_posted)).paginate(page=page,per_page=4)
    display_comment=Comment.query.all()
    return render_template('article.html',display_post=display_post,display_comment=display_comment)

@app.route("/articles/<int:id>")
def showpost(id):
    display_post = Post.query.get(id)
    display_comment=Comment.query.filter_by(comment_post_id=id).all()
    return render_template('showpost.html',display_post=display_post,display_comment=display_comment)

@app.route("/articles/<string:cat>")
def showcategory(cat):
    cat=bleach.clean(cat)
    display_post = Post.query.filter_by(post_category=cat).all()
    print(display_post)
    return render_template('showcategoryposts.html',display_post=display_post,cat=cat)

@app.route('/',methods=["POST","GET"])
def addcomment():
    if request.method == "POST":
        postkey=request.form.get('postkey')
        comment_text=request.form.get('comment')
        print(comment_text)
       # comment=bleach.clean(comment)
        comment_data=Comment(comment_text,datetime.now(),postkey,True)
        db.session.add(comment_data)
        db.session.commit()
        page=request.args.get('page',1,type=int)
        display_post = Post.query.order_by(desc(Post.post_id)).paginate(page=page,per_page=4)
        display_comment=Comment.query.all()
        return render_template('article.html',display_post=display_post,display_comment=display_comment)
    else:
        return render_template('article.html')

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

@app.route("/delete/<int:id>")
def deletepost(id):
    dp = Post.query.filter_by(post_id=id).all()
    ct = Comment.query.filter_by(comment_post_id=id).all()
    print(ct)
    rp = []
    for com in ct:
        r = Reply.query.filter_by(reply_id=com.comment_id).all().count(Reply.reply_id)
        if r != 0:
            re = Reply.query.filter_by(reply_id=com.comment_id).all()
            rp .append(re)
    print(len(rp))
    if rp != None:
        for r in rp:
            db.session.delete(r)
    if ct != None:
        for com in ct:
            db.session.delete(com)
    if dp != None:
        for d in dp:
            db.session.delete(d)
    db.session.commit()
    posts=Post.query.all()  
    return render_template('admin.html',posts=posts)

@app.route("/update/<int:id>")
def updatepost(id):
    post = Post.query.get(id)
    return render_template('updatepost.html',post=post)

@app.route("/update",methods=["POST"])
def updatepostdetails():
    if request.method == "POST":
        title = request.form.get("TITLE")
        content = request.form.get('content')
        content = bleach.clean(content,tags=['img','p','h1','h2','h3','a'],attributes={'img':['src']},protocols=['data']
        )
        category = request.form.get('categories')
        postid = request.form.get("postid")
        post = Post.query.get(postid)
        post.post_title = title
        post.post_content = content
        post.post_category = category
        post.date_posted = datetime.now()
        db.session.commit()
        page=request.args.get('page',1,type=int)
        display_post = Post.query.order_by(desc(Post.date_posted)).paginate(page=page,per_page=4)
        display_comment=Comment.query.all()
        return render_template('article.html',display_post=display_post,display_comment=display_comment)

if __name__ == '__main__':
    app.run(debug=True)
