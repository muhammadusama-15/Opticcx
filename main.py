import os
#from dotenv import load_dotenv
from flask import Flask, abort, render_template, redirect, url_for, flash, request
from flask_bootstrap import Bootstrap5
from flask_ckeditor import CKEditor
from flask_gravatar import Gravatar
from flask_login import UserMixin, login_user, LoginManager, current_user, logout_user, login_required
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship, DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Text
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
import smtplib

# Import your forms from the forms.py
from forms import CreatePostForm, RegisterForm, LoginForm, CommentForm, PaymentForm
from typing import List

#load_dotenv("secrets.env")
MY_EMAIL = os.environ.get("MY_EMAIL")
MY_PASSWORD = os.environ.get("MY_PASSWORD")

'''
Make sure the required packages are installed: 
Open the Terminal in PyCharm (bottom left). 

On Windows type:
python -m pip install -r requirements.txt

On MacOS type:
pip3 install -r requirements.txt

This will install the packages from the requirements.txt for this project.
'''



def admin_only(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        #If id is not 1 then return abort with 403 error
        if current_user.id != 1:
            return abort(403)
        #Otherwise continue with the route function
        return f(*args, **kwargs)        
    return decorated_function

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('FLASK_KEY')
ckeditor = CKEditor(app)
Bootstrap5(app)

# For adding profile images to the comment section
gravatar = Gravatar(app,
                    size=100,
                    rating='g',
                    default='retro',
                    force_default=False,
                    force_lower=False,
                    use_ssl=False,
                    base_url=None)

# TODO: Configure Flask-Login
login_manager = LoginManager()
login_manager.init_app(app=app)

# Create a user_loader callback
@login_manager.user_loader
def load_user(user_id):
    return db.get_or_404(User, user_id)


# CREATE DATABASE
class Base(DeclarativeBase):
    pass
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DB_URI", "sqlite:///opticcx.db")
db = SQLAlchemy(model_class=Base)
db.init_app(app)


# CONFIGURE TABLES
class Product(db.Model):
    __tablename__ = "products"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    # Create Foreign Key, "users.id" the users refers to the tablename of User.
    #author_id: Mapped[int] = mapped_column(Integer, db.ForeignKey("users.id"))
    # Create reference to the User object. The "posts" refers to the posts property in the User class.
    #author = relationship("User", back_populates="posts")

    title: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    price: Mapped[float] = mapped_column(Integer(250), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    img_url: Mapped[str] = mapped_column(String(250), nullable=False)
    
    #***************Parent Relationship*************#
    comments = relationship("Comment", back_populates="parent_post")


# TODO: Create a User table for all your registered users.
class User(db.Model, UserMixin):
    __tablename__= "users"
    id:Mapped[int] = mapped_column(Integer,primary_key=True)
    name:Mapped[str] = mapped_column(String,nullable=False)
    email:Mapped[str] = mapped_column(String,nullable=False)
    password:Mapped[str] = mapped_column(String, nullable=False)
    #posts = relationship("Product", back_populates="author")
     #*******Add parent relationship*******#
    #"comment_author" refers to the comment_author property in the Comment class.
    comments = relationship("Comment", back_populates="comment_author")

class Comment(db.Model):
    __tablename__ = "comments"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    author_id: Mapped[int] = mapped_column(Integer, db.ForeignKey("users.id"))
    comment_author = relationship("User", back_populates="comments")
    
    #***************Child Relationship*************#
    post_id: Mapped[str] = mapped_column(Integer, db.ForeignKey("products.id"))
    parent_post = relationship("Product", back_populates="comments")
    text: Mapped[str] = mapped_column(Text, nullable=False)

with app.app_context():
    db.create_all()


# TODO: Use Werkzeug to hash the user's password when creating a new user.
@app.route('/register',methods=["POST","GET"])
def register():
    register_form = RegisterForm()
    if register_form.validate_on_submit():
        result = db.session.execute(db.select(User).where(User.email == register_form.email.data))
        user = result.scalar()
        if user:
            flash(message="This email already exists. Try logging in instead!")
            return redirect(url_for('login'))
        else:
            hashed_and_salted_password = generate_password_hash(password=register_form.password.data, method="pbkdf2:sha256", salt_length=8)
            new_user = User(
                name=register_form.name.data,
                email=register_form.email.data,
                password = hashed_and_salted_password
                )
            db.session.add(new_user)
            db.session.commit()

            login_user(new_user)
            return redirect(url_for("get_all_posts"))

    return render_template("register.html", form=register_form, current_user = current_user)


# TODO: Retrieve a user from the database based on their email. 
@app.route('/login', methods=["POST","GET"])
def login():
    login_form = LoginForm()
    if login_form.validate_on_submit():
        result = db.session.execute(db.select(User).where(User.email==login_form.email.data))
        user = result.scalar()
        if not user:
            flash(message="This email does not exist. Try registering with us instead...")
        elif not check_password_hash(user.password,login_form.password.data):
            flash(message="Kindly insert the correct password!")
        else:
            login_user(user=user)
            return redirect(url_for("get_all_posts"))
        
    return render_template("login.html", form=login_form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('get_all_posts'))


@app.route('/')
def get_all_posts():
    #return "Hello World"
    result = db.session.execute(db.select(Product))
    posts = result.scalars().all()
    try:
        if current_user.id == 1:
            admin = True
        else:
            admin = False
    except:
        admin = False
    return render_template("index.html", all_posts=posts, admin=admin)


# TODO: Allow logged-in users to comment on posts
@app.route("/post/<int:post_id>",methods=["POST","GET"])
def show_post(post_id):
    requested_post = db.get_or_404(Product, post_id)
    comment_form = CommentForm()
    try:
        if current_user.id == 1:
            admin = True
        else:
            admin = False
    except:
        admin = False

    # Only allow logged-in users to comment on posts
    if comment_form.validate_on_submit():
        if not current_user.is_authenticated:
            flash("You need to login or register to comment.")
            return redirect(url_for("login"))

        new_comment = Comment(
            text=comment_form.comment_text.data,
            comment_author=current_user,
            parent_post=requested_post
        )
        db.session.add(new_comment)
        db.session.commit()

    #all_comments = db.session.execute(db.select(Comment)).scalars().all()
    return render_template("post.html", post=requested_post, admin=admin, form=comment_form)


# TODO: Use a decorator so only an admin user can create a new post
@app.route("/new-post", methods=["GET", "POST"])
@admin_only
def add_new_post():
    form = CreatePostForm()
    if form.validate_on_submit():
        new_post = Product(
            title=form.title.data,
            price=form.price.data,
            body=form.body.data,
            img_url=form.img_url.data,
        )
        db.session.add(new_post)
        db.session.commit()
        return redirect(url_for("get_all_posts"))
    return render_template("make-post.html", form=form)


# TODO: Use a decorator so only an admin user can edit a post
@app.route("/edit-post/<int:post_id>", methods=["GET", "POST"])
@admin_only
def edit_post(post_id):
    post = db.get_or_404(Product, post_id)
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
    return render_template("make-post.html", form=edit_form, is_edit=True)


# TODO: Use a decorator so only an admin user can delete a post
@app.route("/delete/<int:post_id>")
@admin_only
def delete_post(post_id):
    post_to_delete = db.get_or_404(Product, post_id)
    db.session.delete(post_to_delete)
    db.session.commit()
    return redirect(url_for('get_all_posts'))


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/contact",methods=['GET','POST'])
def contact():
    if request.method == 'POST':
        # Get form data
        name = request.form.get('name')  # Get the value of the 'name' field
        email = request.form.get('email')  # Get the value of the 'email' field
        message = request.form.get('message')  # Get the value of the 'message' field
        phone = request.form.get('phone')

        email_to_send = f"Name: {name}\nEmail: {email}\nPhone: {phone}\nMessage: {message}"
        with smtplib.SMTP("smtp.gmail.com",port=587) as connection:
            connection.starttls()
            connection.login(user=MY_EMAIL, password=MY_PASSWORD)
            connection.sendmail(from_addr=MY_EMAIL, to_addrs=MY_EMAIL, msg=f"Subject:Message from User\n\n{email_to_send}")

        # Process the form data (e.g., save to database, send an email, etc.)
        flash(f"Form submitted successfully! {email_to_send}, Status: Success")
    return render_template("contact.html")

@app.route("/buy_now/<int:product_id>",methods=['POST','GET'])
def buy_now(product_id):
    product = db.get_or_404(Product, product_id)
    total_bill = f"Rs {product.price}"
    if current_user.is_authenticated:
        payment_form = PaymentForm(name=current_user.name,
                                   email=current_user.email,
                                   bill=total_bill)
        payment_form.bill.render_kw = {"disabled": "disabled"}
        if payment_form.validate_on_submit():
            return render_template('thanks.html')
        return render_template('payment.html',form=payment_form)
    else:
        return redirect(url_for('login'))


if __name__ == "__main__":
    app.run(debug=True, port=5002)
