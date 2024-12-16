from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField
from wtforms.validators import DataRequired, URL
from flask_ckeditor import CKEditorField


# WTForm for creating a blog post
class CreatePostForm(FlaskForm):
    title = StringField("Product Title", validators=[DataRequired()])
    price = StringField("Price", validators=[DataRequired()])
    img_url = StringField("Product Image URL", validators=[DataRequired(), URL()])
    body = CKEditorField("Product Description", validators=[DataRequired()])
    submit = SubmitField("Add Product")


# TODO: Create a RegisterForm to register new users
class RegisterForm(FlaskForm):
    name = StringField(label="Name", validators=[DataRequired()])
    email = StringField(label="Email", validators=[DataRequired()])
    password = PasswordField(label="Password",validators=[DataRequired()])
    submit = SubmitField(label="Sign Me up!", validators=[DataRequired()])


# TODO: Create a LoginForm to login existing users
class LoginForm(FlaskForm):
    email = StringField(label="Email", validators=[DataRequired()])
    password = PasswordField(label="Password", validators=[DataRequired()])
    login = SubmitField(label="Log Me In", validators=[DataRequired()])


# TODO: Create a CommentForm so users can leave comments below posts
class CommentForm(FlaskForm):
    comment_text = CKEditorField(label="Review", validators=[DataRequired()])
    submit = SubmitField(label="Post Review", validators=[DataRequired()])

class PaymentForm(FlaskForm):
    name = StringField(label="Name", validators=[DataRequired()])
    email = StringField(label="Email", validators=[DataRequired()])
    card_no = StringField(label="Card no.", validators=[DataRequired()])
    expiry_date = StringField(label="Expiry Data (MM/YY)", validators=[DataRequired()])
    cvc = StringField(label="CVC", validators=[DataRequired()])
    address = StringField(label="Address", validators=[DataRequired()])
    bill = StringField(label="Total Bill", validators=[DataRequired()])
    submit = SubmitField(label="Confirm Payment", validators=[DataRequired()])