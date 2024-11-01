import os
from datetime import date
import werkzeug
from flask import Flask, abort, render_template, redirect, url_for, flash
from flask_bootstrap import Bootstrap5
from flask_ckeditor import CKEditor
from flask_gravatar import Gravatar
from flask_login import UserMixin, login_user, LoginManager, current_user, logout_user, login_manager
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship, DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Text, ForeignKey
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
# Import your forms from the forms.py
from forms import CreatePostForm, RegisterForm, LoginForm, CommentForm
from mysql import connector

'''
Make sure the required packages are installed: 
Open the Terminal in PyCharm (bottom left). 

On Windows type:
python -m pip install -r requirements.txt

On MacOS type:
pip3 install -r requirements.txt

This will install the packages from the requirements.txt for this project.
'''
def do_some_before_flask_start():
  print('MyFlaskApp is starting up!')
class MyFlaskApp(Flask):
  def run(self, host=None, port=None, debug=None, load_dotenv=True, **options):
    if not self.debug or os.getenv('WERKZEUG_RUN_MAIN') == 'true':
      with self.app_context():
        do_some_before_flask_start()
    super(MyFlaskApp, self).run(host=host, port=port, debug=debug, load_dotenv=load_dotenv, **options)

app = MyFlaskApp(__name__)
app.config['SECRET_KEY'] = os.environ.get('FLASK_KEY')
ckeditor = CKEditor(app)
Bootstrap5(app)




# TODO: Configure Flask-Login

# CREATE DATABASE
class Base(DeclarativeBase):
    pass
#app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///posts.db'
# To run locally
#app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DB_URI", "sqlite:///posts.db")
# To connect to mysql
#app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:mysql@127.0.0.1:3306/blogdb'
app.config['SQLALCHEMY_DATABASE_URI'] = ('mysql+mysqlconnector://'+ os.environ.get("DB_LOGIN") + ':' + os.environ.get("DB_PASS") + '@'
                                         + os.environ.get("DB_URI") + '/' + os.environ.get("DB_SCHEMA") )
# To conect to mysql within docker compose
#app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:mysql@db/blogdb'

db = SQLAlchemy(model_class=Base)
db.init_app(app)


# CONFIGURE TABLES
class BlogPost(db.Model):
    __tablename__ = "blog_posts"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    subtitle: Mapped[str] = mapped_column(String(250), nullable=False)
    date: Mapped[str] = mapped_column(String(250), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    author: Mapped[str] = mapped_column(String(250), nullable=False)
    img_url: Mapped[str] = mapped_column(String(250), nullable=False)
    # Create Foreign Key, "users.id" the users refers to the tablename of User.
    author_id: Mapped[int] = mapped_column(Integer, db.ForeignKey("users.id"))
    # Create reference to the User object. The "posts" refers to the posts property in the User class.
    author = relationship("User", back_populates="posts")
    # Create reference to the Comment object. The "parent_post" refers to the parent_post property in the Comment class.
    comments = relationship("Comment", back_populates="parent_post")

# TODO: Create a User table for all your registered users.
class User(UserMixin, db.Model):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(100), unique=True)
    password: Mapped[str] = mapped_column(String(100))
    name: Mapped[str] = mapped_column(String(1000))
    #This will act like a List of BlogPost objects attached to each User.  #The "author" refers to the author property in the BlogPost class.
    posts = relationship("BlogPost", back_populates="author")
    # This will act like a List of Comment objects attached to each User.  #The "author" refers to the author property in the Comment class.
    comments = relationship("Comment", back_populates="author")

# Comments table
class Comment(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    author_id: Mapped[int] = mapped_column(Integer, db.ForeignKey("users.id"))
    post_id: Mapped[int] = mapped_column(Integer, db.ForeignKey("blog_posts.id"))
    #This will act like a List of User object attached to each Comment.
    author = relationship("User", back_populates="comments")
    # This will act like a List of BlogPost object attached to each Comment.
    parent_post = relationship("BlogPost", back_populates="comments")


with app.app_context():
    db.create_all()
    # Check if admin exists and add it.
    admin = db.session.execute(db.select(User).where(User.id == 1))
    #admin = db.session.get(User,1)
    print(admin)
    if not admin.scalar():
        password = werkzeug.security.generate_password_hash(password=os.environ.get('ADMIN_PASSWORD'), method='pbkdf2:sha256', salt_length=8)
        db.session.add(User(id=1, name="Admin", email=os.environ.get('ADMIN_EMAIL'), password=password))
        db.session.commit()

# Configure Flask-Login's Login Manager
login_manager = LoginManager()
login_manager.init_app(app)
# Create a user_loader callback
@login_manager.user_loader
def load_user(user_id):
    return db.get_or_404(User, user_id)

# For adding profile images to the comment section
gravatar = Gravatar(app,
                    size=100,
                    rating='g',
                    default='retro',
                    force_default=False,
                    force_lower=False,
                    use_ssl=False,
                    base_url=None)

def admin_only(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        #Do something before
        if current_user.id == 1:
            return f(*args, **kwargs)
        else:
            abort(403)
    return decorated_function


# TODO: Use Werkzeug to hash the user's password when creating a new user.
@app.route('/register', methods=['GET','POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        # Check if user exist and forward to login page
        user = db.session.execute(db.select(User).where(User.email == form.email.data)).scalar()
        if user:
            flash('User exists, redirecting to login page')
            return redirect(url_for('login'))
        # Save new user
        password = werkzeug.security.generate_password_hash(form.password.data, method='pbkdf2:sha256',salt_length=8)
        new_user = User(name=form.name.data, password=password, email=form.email.data)
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        return redirect(url_for('get_all_posts'))
    return render_template("register.html", form=form, user=current_user)


# TODO: Retrieve a user from the database based on their email. 
@app.route('/login',methods=['GET','POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = db.session.execute(db.select(User).where(User.email == form.email.data)).scalar()
        if user:
            check_user_password = werkzeug.security.check_password_hash(user.password, form.password.data)
            if check_user_password:
                login_user(user)
                print('Login success')
                return redirect(url_for('get_all_posts'))
            else:
                flash('Invalid credentials')
                return redirect(url_for('login'))
        else:
            flash('Invalid credentials')
            return redirect(url_for('login'))
    return render_template("login.html", form=form, user=current_user)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('get_all_posts'))


@app.route('/')
def get_all_posts():
    result = db.session.execute(db.select(BlogPost))
    posts = result.scalars().all()
    return render_template("index.html", all_posts=posts, user=current_user)


# TODO: Allow logged-in users to comment on posts
@app.route("/post/<int:post_id>",methods=['GET','POST'])
def show_post(post_id):
    requested_post = db.get_or_404(BlogPost, post_id)
    #print(requested_post.comments)
    form = CommentForm()

    if form.validate_on_submit():
        if current_user.is_authenticated:
            new_comment = Comment(body=form.body.data, author_id=current_user.id, post_id=post_id)
            db.session.add(new_comment)
            db.session.commit()
            return redirect(url_for('get_all_posts'))
        else:
            flash('log in to make comment')
            return redirect(url_for('login'))
    return render_template("post.html", post=requested_post, user=current_user, form=form)


# TODO: Use a decorator so only an admin user can create a new post
@app.route("/new-post", methods=["GET", "POST"])
@admin_only
def add_new_post():
    form = CreatePostForm()
    if form.validate_on_submit():
        new_post = BlogPost(
            title=form.title.data,
            subtitle=form.subtitle.data,
            body=form.body.data,
            img_url=form.img_url.data,
            author=current_user,
            date=date.today().strftime("%B %d, %Y")
        )
        db.session.add(new_post)
        db.session.commit()
        return redirect(url_for("get_all_posts"))
    return render_template("make-post.html", form=form, user=current_user)


# TODO: Use a decorator so only an admin user can edit a post
@app.route("/edit-post/<int:post_id>", methods=["GET", "POST"])
@admin_only
def edit_post(post_id):
    post = db.get_or_404(BlogPost, post_id)
    edit_form = CreatePostForm(
        title=post.title,
        subtitle=post.subtitle,
        img_url=post.img_url,
        author=post.author,
        body=post.body
    )
    if edit_form.validate_on_submit():
        post.title = edit_form.title.data
        post.subtitle = edit_form.subtitle.data
        post.img_url = edit_form.img_url.data
        post.author = current_user
        post.body = edit_form.body.data
        db.session.commit()
        return redirect(url_for("show_post", post_id=post.id))
    return render_template("make-post.html", form=edit_form, is_edit=True, user=current_user)


# TODO: Use a decorator so only an admin user can delete a post
@app.route("/delete/<int:post_id>")
@admin_only
def delete_post(post_id):
    post_to_delete = db.get_or_404(BlogPost, post_id)
    db.session.delete(post_to_delete)
    db.session.commit()
    return redirect(url_for('get_all_posts'))


@app.route("/about")
def about():
    return render_template("about.html", user=current_user)


@app.route("/contact")
def contact():
    return render_template("contact.html", user=current_user)


if __name__ == "__main__":
    app.run(debug=False, port=5002)



