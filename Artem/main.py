import requests
from bs4 import BeautifulSoup
from flask import Flask, render_template, redirect, request
from data import db_session
from data.users import User
from data.indicators import Indicators
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, RadioField
from wtforms.fields.html5 import EmailField
from wtforms.validators import DataRequired


app = Flask(__name__)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'

login_manager = LoginManager()
login_manager.init_app(app)


def parse_news():
    url = 'https://стопкоронавирус.рф'
    response = requests.get(url).text
    if response:
        soup = BeautifulSoup(response, 'html.parser')
        news = [[x.div.span.text, x.find('div', attrs={'class': 'cv-countdown__item-label'}).text] for x in soup.find_all('div', {'class': 'cv-countdown__item'})]
        return news
    else:
        print('error while getting page, status code: {}'.format(response.status_code))
        return None


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


class AnkForm(FlaskForm):
    temperature = StringField('Какая у вас температура?', validators=[DataRequired()])
    contact_with_people = RadioField('Часто ли Вы контактируете с людьми?', choices=[('1', 'Да'), ('0', 'Нет')])
    abroad = RadioField('Были ли Вы за границей недавно?', choices=[('1', 'Да'), ('0', 'Нет')])
    people_with_corona = RadioField('Контактировали с заболевшими?', choices=[('1', 'Да'), ('0', 'Нет')])
    do_user_know_about = RadioField('Знаете ли вы о правилах в период эпидемии?', choices=[('1', 'Да'), ('0', 'Нет')])
    self_isolatioon = RadioField('Соблюдаете ли Вы самоизоляцию?', choices=[('1', 'Да'), ('0', 'Нет')])
    address = StringField('Ваш адрес', validators=[DataRequired()])

    submit = SubmitField('Сохранить')


@app.route('/ank', methods=['GET', 'POST'])
def ank():
    db_session.global_init("db/info.sqlite")
    session = db_session.create_session()
    form = AnkForm()
    if request.method == 'POST' and form.validate_on_submit():
        ind = Indicators()
        ind.user = current_user.id
        ind.temperature = float(form.temperature.data.replace(',', '.'))
        ind.contact_with_people = bool(int(form.contact_with_people.data))
        ind.abroad = bool(int(form.abroad.data))
        ind.people_with_corona = bool(int(form.people_with_corona.data))
        ind.do_user_know_about = bool(int(form.do_user_know_about.data))
        ind.self_isolatioon = bool(int(form.self_isolatioon.data))
        ind.address = form.address.data
        session.add(ind)
        session.commit()
        session.close()
        return redirect('/user_info')
    return render_template('ank.html', form=form)


@app.route('/corona_main')
@app.route('/index')
@app.route('/')
def main():
    db_session.global_init("db/info.sqlite")
    session = db_session.create_session()
    v = parse_news()
    i = []
    for ind in session.query(Indicators).all():
        i.append([ind.id, ind.temperature, ind.contact_with_people, ind.abroad, ind.people_with_corona])
    return render_template('corona.html', i=i, v=v)


@app.route('/map')
def ab():
    db_session.global_init("db/info.sqlite")
    return render_template('map.html')


@app.route('/news')
def news():
    a = []
    for i in range(1, 5):
        url = f'https://стопкоронавирус.рф/news/?page={i}'
        response = requests.get(url).text
        if response:
            soup = BeautifulSoup(response, 'html.parser')
            a.extend([[x.a.h2.text, 'https://стопкоронавирус.рф/news/' + x.a['href'], 
                       x.a.p.text] for x in soup.find_all('div', {'class': 'cv-news-page__news-list-item'})])

    return render_template('news.html', a=a)


@app.route('/coronainfo')
def map():
    return render_template('about.html')


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


@app.route('/user_info')
def main1():
    db_session.global_init("db/info.sqlite")
    session = db_session.create_session()

    pers = session.query(User).filter(User.id == current_user.id).first()
    a = [pers.name + ' ' + pers.surname, pers.age, pers.email]

    s = []
    for ind in session.query(Indicators).filter(Indicators.user == current_user.id):

        s.append([ind.temperature, ind.contact_with_people, ind.abroad,
                  ind.people_with_corona, ind.do_user_know_about, ind.self_isolatioon, ind.address])

    return render_template('selfinfo.html', a=a, s=s)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")
