from flask import Flask, render_template, redirect, request
from data import db_session
from data.users import User
from data.indicators import Indicators
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField
from wtforms.fields.html5 import EmailField
from wtforms.validators import DataRequired


app = Flask(__name__)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'

login_manager = LoginManager()
login_manager.init_app(app)


@app.route('/corona_main')
def main():
    db_session.global_init("db/info.sqlite")
    session = db_session.create_session()

    i = []
    for job in session.query(Indicators).all():
        team = session.query(User).filter(User.id == job.user).first().name
        team += ' ' + session.query(User).filter(User.id == job.user).first().surname
        i.append([job.id, job.temperature, job.contact_with_people, job.abroad, job.people_with_corona])
    return render_template('corona.html', i=i)

@login_manager.user_loader
def load_user(user_id):
    session = db_session.create_session()
    return session.query(User).get(user_id)


class LoginForm(FlaskForm):
    email = EmailField('Почта', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    remember_me = BooleanField('Запомнить меня')
    submit = SubmitField('Войти')


class RegisterForm(FlaskForm):
    name = StringField('Имя пользователя', validators=[DataRequired()])
    surname = StringField('Фамилия пользователя', validators=[DataRequired()])
    email = StringField('Почта', validators=[DataRequired()])
    address = StringField('Адрес пользователя', validators=[DataRequired()])
    age = StringField('Возраст', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    password_again = PasswordField('Повторите пароль', validators=[DataRequired()])

    submit = SubmitField('Войти')


@app.route('/register', methods=['GET', 'POST'])
def reqister():
    db_session.global_init("db/info.sqlite")
    form = RegisterForm()
    if request.method == 'POST' and form.validate_on_submit():
        if form.password.data != form.password_again.data:
            return render_template('register.html', title='Регистрация', form=form, message="Пароли не совпадают")
        session = db_session.create_session()
        if session.query(User).filter(User.email == form.email.data).first():
            return render_template('register.html', title='Регистрация', form=form,
                                   message="Такой пользователь уже есть")
        user = User()
        user.name = form.name.data
        user.surname = form.surname.data
        user.email = form.email.data
        user.address = form.address.data
        user.age = int(form.age.data)
        user.set_password(form.password.data)
        session.add(user)
        session.commit()
        return redirect('/login')
    return render_template('register.html', title='Регистрация', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    db_session.global_init("db/info.sqlite")
    form = LoginForm()
    if request.method == 'POST' and form.validate_on_submit():
        session = db_session.create_session()
        user = session.query(User).filter(User.email == form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect("/corona_main")
        return render_template('login.html', message="Неправильный логин или пароль", form=form)
    else:
        return render_template('login.html', title='Авторизация', form=form)

@app.route('/selfinfo')
def main1():
    db_session.global_init("db/blogs.sqlite")
    session = db_session.create_session()

    i = []
    for job in session.query(Indicators).filter(User.surname.address.like(current_user.surname), User.surname.address.like(current_user.name)):
        team = session.query(User).filter(User.id == job.chief).first().name
        team += ' ' + session.query(User).filter(User.id == job.chief).first().surname
        i.append([job.id, job.title, team, job.members, job.email, job.user.id])
    return render_template('selfinfo.html', i=i)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")


@app.route('/index')
@app.route('/')
def qwe():
    db_session.global_init("db/info.sqlite")
    return '''<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
    <link rel="stylesheet"
          href="https://stackpath.bootstrapcdn.com/bootstrap/4.4.1/css/bootstrap.min.css"
          integrity="sha384-Vkoo8x4CGsO3+Hhxv8T/Q5PaXtkKtu6ug5TOeNV6gBiFeWPGFN9MuhOf23Q9Ifjh"
          crossorigin="anonymous">
    <link rel="stylesheet" href="/static/css/style.css">
</head>
<body>
    <header>
        <nav class="navbar navbar-light bg-light">
            <h1 class="navbar-brand" href="#">Миссия Колонизация Марса</h1>
            <p>
                <a class="btn btn-primary " href="/register">Зарегистрироваться</a>
                <a class="btn btn-success" href="/login">Войти</a>
            </p>
            <h1>Главная</h1>
        </nav>
    </header>
</body>
</html>'''





if __name__ == '__main__':
    app.run(debug=True, port=8080, host='127.0.0.1')
