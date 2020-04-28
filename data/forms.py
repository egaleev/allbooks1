from flask_wtf import FlaskForm, Form
from wtforms import PasswordField, TextAreaField, StringField, SubmitField, BooleanField, FileField, DateField
from wtforms.fields.html5 import EmailField
from wtforms.validators import DataRequired


class RegisterForm(FlaskForm):
    email = EmailField('Почта', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    password_again = PasswordField('Повторите пароль', validators=[DataRequired()])
    name = StringField('Имя пользователя', validators=[DataRequired()])
    submit = SubmitField('Войти')


class LoginForm(FlaskForm):
    email = EmailField('Почта', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    submit = SubmitField('Войти')


class PostForm(FlaskForm):
    title = StringField('Название', validators=[DataRequired()])
    content = TextAreaField('Описание', validators=[DataRequired()])
    available = StringField('Сколько доступно', validators=[DataRequired()])
    file = FileField('файл электронной книги', validators=[DataRequired()])
    pic = FileField('Картинка', validators=[DataRequired()])
    submit = SubmitField('Выложить')


class ReserveForm(FlaskForm):
    time = DateField('На какой день вы хотитие забронировать?', validators=[DataRequired()])
    submit = SubmitField('Забронировать')


class MailingForm(FlaskForm):
    text = StringField('Введите текст рассылки', validators=[DataRequired()])
    submit = SubmitField('Начать')


class PaymentForm(FlaskForm):
    submit = SubmitField('Проверить оплату')
