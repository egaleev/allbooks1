import mimetypes
import os
import profile
import random
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from pathlib import Path
from sqlalchemy import desc
from werkzeug.utils import secure_filename
import smtplib
from data import db_session
from flask import Flask, render_template, redirect
from data.__all_models import User, Reserve
from flask import request
from data.__all_models import Post
from data.forms import RegisterForm, LoginForm, PostForm, ReserveForm, MailingForm, PaymentForm
from flask import redirect, url_for
import requests

app = Flask(__name__)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'
login_manager = LoginManager()
login_manager.init_app(app)


def send_book(pos, mail):
    filepath = f"static/instance/{pos}/book.epub"
    msg = MIMEMultipart()
    msg['From'] = 'allofbooks2020@gmail.com'  # Адресат
    msg['To'] = mail  # Получатель
    msg['Subject'] = 'Благодарим за покупку на нашем сайте!'
    text = 'Ваша книга прикреплена ниже.'
    msg.attach(MIMEText(text, 'plain'))
    filename = os.path.basename(filepath)
    ctype, encoding = mimetypes.guess_type(filepath)  # Определяем тип файла на основе его расширения
    if ctype is None or encoding is not None:  # Если тип файла не определяется
        ctype = 'application/octet-stream'  # Будем использовать общий тип
    maintype, subtype = ctype.split('/', 1)
    with open(filepath) as fp:  # Открываем файл для чтения
        file = MIMEBase(maintype, subtype)  # Используем общий MIME-тип
        file.set_payload(fp.read())  # Добавляем содержимое общего типа (полезную нагрузку)
        fp.close()
        encoders.encode_base64(file)
    file.add_header('Content-Disposition', 'attachment', filename=filename)  # Добавляем заголовки
    msg.attach(file)


def payment_history_last(rows_num, next_TxnId, next_TxnDate):
    my_login = '79090583560'
    api_access_token = '375d4bcd06e75e47b5515cdc45bde09d'
    s = requests.Session()
    s.headers['authorization'] = 'Bearer ' + api_access_token
    parameters = {'rows': rows_num, 'nextTxnId': next_TxnId, 'nextTxnDate': next_TxnDate}
    h = s.get('https://edge.qiwi.com/payment-history/v2/persons/' + my_login + '/payments', params=parameters)
    return h.json()


def check_payment(code):
    lastPayments = payment_history_last('5', '', '')
    sum = 1
    for i in lastPayments['data']:
        if sum == i['sum']['amount'] and str(code) == i['comment']:
            return True
        print(i['sum']['amount'], i['comment'])
        print(code)
        print(str(code) == i['comment'])
    return False


def generate_code():
    nums = '1234567890'
    ans = ''
    for i in range(5):
        ans += random.choice(nums)
    return ans


def start_mailing(mails, text):
    smtpObj = smtplib.SMTP('smtp.gmail.com', 587)
    smtpObj.starttls()
    smtpObj.login('allofbooks2020@gmail.com', '123QWEasdZXC')
    for i in mails:
        smtpObj.sendmail('allofbooks2020@gmail.com', i, text)


@login_manager.user_loader
def load_user(user_id):
    session = db_session.create_session()
    return session.query(User).get(user_id)


@app.route('/admin/mailing', methods=['POST', 'GET'])
@login_required
def mailing():
    if current_user.is_admin == "1":
        form = MailingForm()
        if form.validate_on_submit():
            text = form.text.data
            session = db_session.create_session()
            users = session.query(User).all()
            mails = []
            for i in users:
                mails.append(i.email)
            start_mailing(mails, text)
            return redirect('/admin')
        else:
            return render_template("mailing.html", form=form)
    else:
        return redirect('/')


@app.route('/')
def main_page():
    q = request.args.get('q')
    session = db_session.create_session()
    if q:
        posts = session.query(Post).filter(Post.title.contains(q) | Post.content.contains(q)).all()
        return render_template("index.html", posts=posts)
    session.commit()
    return render_template('main.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")


@app.route('/reserve/<int:pos>', methods=['POST', 'GET'])
@login_required
def reserve(pos):
    form = ReserveForm()
    if request.method == 'POST':
        user_name = current_user.name
        session = db_session.create_session()
        book_name = session.query(Post).filter(Post.id == pos).first().title
        time = form.time.data
        print(time)
        reserve = Reserve(user_name=user_name, book_name=book_name, time=time)
        session = db_session.create_session()
        session.add(reserve)
        book = session.query(Post).filter(Post.title == book_name).first()
        book.available -= 1
        session.commit()
        return redirect('/')
    else:
        return render_template("reserve.html", form=form)


@app.route('/payment/<int:pos>/<int:code>', methods=['GET', 'POST'])
@login_required
def payment(pos, code):
    form = PaymentForm()
    if form.validate_on_submit():
        if check_payment(code):
            status = 'Оплачено'
            send_book(pos, current_user.email)
        else:
            status = 'Оплата не найдена'
        return render_template('payment.html', code=code, status=status, form=form)
    status = 'Оплата не найдена'
    return render_template('payment.html', code=code, status=status, form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        session = db_session.create_session()
        user = session.query(User).filter(User.email == form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            return redirect("/")
        return render_template('login.html',
                               message="Неправильный логин или пароль",
                               form=form)
    return render_template('login.html', title='Авторизация', form=form)


@app.route('/register', methods=['GET', 'POST'])
def reqister():
    form = RegisterForm()
    if form.validate_on_submit():
        print('kk')
        if form.password.data != form.password_again.data:
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Пароли не совпадают")
        session = db_session.create_session()
        if session.query(User).filter(User.email == form.email.data).first():
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Такой пользователь уже есть")
        user = User(
            name=form.name.data,
            email=form.email.data,
        )
        user.set_password(form.password.data)
        session.add(user)
        session.commit()
        return redirect('/login')
    print('kkk')
    return render_template('register.html', title='Регистрация', form=form)


@app.route("/post")
def index():
    q = request.args.get('q')
    session = db_session.create_session()
    if q:
        posts = session.query(Post).filter(Post.title.contains(q) | Post.content.contains(q)).all()
    else:
        query = session.query(Post)
        posts = query.order_by(Post.created_date.desc())
        session.commit()
    return render_template("index.html", posts=posts)


@app.route("/post/<int:pos>")
def post(pos):
    session = db_session.create_session()
    post = session.query(Post).filter(Post.id == pos).first()
    session.commit()
    way = f"/static/instance/{post.id}/book.jpg"
    code = generate_code()
    a = post.available
    return render_template("post.html", item=post, way=way, code=code, a=a)


@app.route('/admin/')
@login_required
def admin():
    if current_user.is_admin == "1":
        q = request.args.get('q')
        session = db_session.create_session()
        if q:
            posts = session.query(Post).filter(Post.title.contains(q) | Post.content.contains(q)).all()
        else:
            query = session.query(Post)
            posts = query.order_by(Post.created_date.desc()).all()
        session.commit()
        return render_template('admin.html', posts=posts)
    else:
        return redirect('/')


@app.route('/admin/delete_post/<int:pos>', methods=['POST'])
@login_required
def delete_post(pos):
    if current_user.is_admin == "1":
        session = db_session.create_session()
        post = session.query(Post).filter(Post.id == pos).first()
        way = f"static/instance/{post.id}"
        os.remove(r'' + way + '/book.jpg')
        os.remove(r'' + way + '/book.epub')
        os.rmdir(way)
        session.delete(post)
        session.commit()
        return redirect('/admin/')
    else:
        return redirect('/')


@app.route('/admin/reserves')
@login_required
def reserves():
    if current_user.is_admin == "1":
        session = db_session.create_session()
        reserves = session.query(Reserve).all()
        session.commit()
        return render_template("reserves.html", reserves=reserves)
    else:
        return redirect('/')


@app.route('/admin/delete_reserve/<int:rid>/<int:all>')
@login_required
def delete_reserve(rid, all):
    if current_user.is_admin == "1":
        session = db_session.create_session()
        reserves = session.query(Reserve).filter(Reserve.id == rid).first()
        book = session.query(Post).filter(Post.title == reserves.book_name).first()
        if all == 1:
            book.available += 1
        session.delete(reserves)
        session.commit()
        return redirect('/admin/reserves')
    else:
        return redirect('/')


@app.route('/admin/create_post', methods=['POST', 'GET'])
@login_required
def create_post():
    if current_user.is_admin == "1":
        form = PostForm()
        if form.validate_on_submit():
            title = form.title.data
            content = form.content.data
            available = form.available.data
            file = form.file.data
            pic = form.pic.data
            session = db_session.create_session()
            post = Post(title=title, content=content, available=available)
            instance_path = 'static/instance/'
            session.add(post)
            session.commit()
            print(post.title, post)
            uploads_dir = os.path.join(instance_path, f'{post.id}')
            os.makedirs(uploads_dir)
            file.save(os.path.join(uploads_dir, secure_filename(f'book.epub')))
            pic.save(os.path.join(uploads_dir, secure_filename(f'book.jpg')))
            return redirect("/admin/")
        else:
            form = PostForm()
            return render_template('create_post.html', form=form)
    else:
        return redirect('/')


@app.route('/admin/edit/<int:pos>', methods=['POST', 'GET'])
@login_required
def edit_post(pos):
    if current_user.is_admin == "1":
        session = db_session.create_session()
        post = session.query(Post).filter(Post.id == pos).first()
        if request.method == 'POST':
            form = PostForm()
            post.title = form.title.data
            post.content = form.content.data
            post.available = form.available.data
            session.commit()
            return redirect(url_for("index"))
        form = PostForm()
        session.commit()
        return render_template('edit.html', post=post, form=form)
    else:
        return redirect('/')


def main():
    db_session.global_init("db/users.sqlite")
    session = db_session.create_session()
    session.commit()
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)


if __name__ == '__main__':
    main()
