from flask import Flask, render_template, redirect, request
from data import db_session
from data.u import User
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from flask_wtf import FlaskForm, Form
from wtforms import StringField, PasswordField, SubmitField, BooleanField, DateField, SelectField, IntegerField, \
    FieldList, FormField
from wtforms.fields.html5 import EmailField
from wtforms.validators import DataRequired
from data.j import Jobs
from data.d import Departments


app = Flask(__name__)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'

login_manager = LoginManager()
login_manager.init_app(app)


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
    email = StringField('Почта', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    password_again = PasswordField('Повторите пароль', validators=[DataRequired()])
    name = StringField('Имя пользователя', validators=[DataRequired()])
    surname = StringField('Фамилия пользователя', validators=[DataRequired()])
    address = StringField('Адрес пользователя', validators=[DataRequired()])
    speciality = StringField('Специальность', validators=[DataRequired()])
    position = StringField('Должность', validators=[DataRequired()])
    age = StringField('Возраст', validators=[DataRequired()])

    submit = SubmitField('Войти')


class DepartmentsForm(FlaskForm):
    db_session.global_init("db/blogs.sqlite")
    session = db_session.create_session()
    a = []
    for user in session.query(User):
        a.append((user.name, user.name + ' ' + user.surname))
    chief = SelectField('Chief', choices=a, validators=False)
    email = StringField('Почта', validators=[DataRequired()])
    name = StringField('Название', validators=[DataRequired()])
    collaborators = StringField('Участники', validators=[DataRequired()])

    submit = SubmitField('Создать')


class JobForm(FlaskForm):
    db_session.global_init("db/blogs.sqlite")
    session = db_session.create_session()
    a = []
    for user in session.query(User):
        a.append((user.name, user.name + ' ' + user.surname))
    team_leader = SelectField('Тимлид', choices=a, validators=False)
    name = StringField('Название', validators=[DataRequired()])
    work_size = IntegerField('Продолжительность', validators=[DataRequired()])
    collaborators = StringField('Участники', validators=[DataRequired()])
    start_date = DateField('Дата начала', validators=[DataRequired()], format='%Y-%m-%d')
    is_finished = BooleanField('Работа завершена?', validators=False)

    submit = SubmitField('Создать')


@app.route('/create_job', methods=['GET', 'POST'])
def create_job():
    form = JobForm()
    db_session.global_init("db/blogs.sqlite")
    session = db_session.create_session()
    if request.method == 'POST' and form.validate_on_submit():
        team_id = session.query(User).filter(User.name == form.team_leader.data).first().id

        job = Jobs()
        job.team_leader = team_id
        job.job = form.name.data
        job.work_size = form.work_size.data
        job.collaborators = form.collaborators.data
        job.start_date = form.start_date.data
        job.is_finished = form.is_finished.data

        session.add(job)
        session.commit()

        return redirect('/jobs')
    return render_template('create_job.html', form=form)


@app.route('/create_department', methods=['GET', 'POST'])
def create_department():
    form = DepartmentsForm()
    db_session.global_init("db/blogs.sqlite")
    session = db_session.create_session()
    if request.method == 'POST' and form.validate_on_submit():
        chief_id = session.query(User).filter(User.name == form.chief.data).first().id
        dep = Departments()

        dep.chief = chief_id
        dep.title = form.name.data
        dep.members = form.collaborators.data
        dep.email = form.email.data

        session.add(dep)
        session.commit()

        return redirect('/departments')
    return render_template('create_department.html', form=form)


@app.route('/edit_job/<int:id>', methods=['GET', 'POST'])
def edit_job(id):
    form = JobForm()
    db_session.global_init("db/blogs.sqlite")
    session = db_session.create_session()

    if request.method == 'POST' and form.validate_on_submit():
        team_id = session.query(User).filter(User.name == form.team_leader.data).first().id

        job = session.query(Jobs).filter(Jobs.id == id).first()
        job.team_leader = team_id
        job.job = form.name.data
        job.work_size = form.work_size.data
        job.collaborators = form.collaborators.data
        job.start_date = form.start_date.data
        job.is_finished = form.is_finished.data

        session.commit()

        return redirect('/jobs')

    else:
        job = session.query(Jobs).filter(Jobs.id == id).first()
        team_name = session.query(User).filter(User.id == job.team_leader).first().name
        form.team_leader.data = team_name
        form.name.data = job.job
        form.work_size.data = job.work_size
        form.collaborators.data = job.collaborators
        form.start_date.data = job.start_date
        form.is_finished.data = job.is_finished

    return render_template('create_job.html', form=form)


@app.route('/edit_department/<int:id>', methods=['GET', 'POST'])
def edit_department(id):
    form = DepartmentsForm()
    db_session.global_init("db/blogs.sqlite")
    session = db_session.create_session()
    if request.method == 'POST' and form.validate_on_submit():
        chief_id = session.query(User).filter(User.name == form.chief.data).first().id
        dep = Departments()

        dep.chief = chief_id
        dep.title = form.name.data
        dep.members = form.collaborators.data
        dep.email = form.email.data

        session.add(dep)
        session.commit()

        return redirect('/departments')

    else:
        dep = session.query(Departments).filter(Departments.id == id).first()
        chief_name = session.query(User).filter(User.id == dep.chief).first().name
        form.chief.data = chief_name
        form.name.data = dep.title
        form.collaborators.data = dep.members
        form.email.data = dep.email

    return render_template('create_department.html', form=form)


@app.route('/job_delete/<int:id>', methods=['GET', 'POST'])
@login_required
def job_delete(id):
    session = db_session.create_session()
    job = session.query(Jobs).filter(Jobs.id == id, Jobs.user == current_user).first()
    if job:
        session.delete(job)
        session.commit()
    return redirect('/jobs')


@app.route('/department_delete/<int:id>', methods=['GET', 'POST'])
@login_required
def department_delete(id):
    session = db_session.create_session()
    job = session.query(Departments).filter(Departments.id == id, Departments.user == current_user).first()
    if job:
        session.delete(job)
        session.commit()
    return redirect('/departments')


@app.route('/register', methods=['GET', 'POST'])
def reqister():
    db_session.global_init("db/blogs.sqlite")
    form = RegisterForm()
    if request.method == 'POST' and form.validate_on_submit():
        if form.password.data != form.password_again.data:
            return render_template('register.html', title='Регистрация', form=form, message="Пароли не совпадают")
        session = db_session.create_session()
        if session.query(User).filter(User.email == form.email.data).first():
            return render_template('register.html', title='Регистрация', form=form,
                                   message="Такой пользователь уже есть")
        user = User(
            name=form.name.data,
            surname=form.surname.data,
            email=form.email.data,
            address=form.address.data,
            speciality=form.speciality.data,
            position=form.position.data,
            age=int(form.age.data)
        )
        user.set_password(form.password.data)
        session.add(user)
        session.commit()
        return redirect('/login')
    return render_template('register.html', title='Регистрация', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if request.method == 'POST' and form.validate_on_submit():
        session = db_session.create_session()
        user = session.query(User).filter(User.email == form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect("/jobs")
        return render_template('login.html', message="Неправильный логин или пароль", form=form)
    else:
        return render_template('login.html', title='Авторизация', form=form)


@app.route('/jobs')
def main():
    db_session.global_init("db/blogs.sqlite")
    session = db_session.create_session()

    i = []
    for job in session.query(Jobs).all():
        team = session.query(User).filter(User.id == job.team_leader).first().name
        team += ' ' + session.query(User).filter(User.id == job.team_leader).first().surname
        i.append([job.id, job.job, team, job.work_size, job.collaborators, job.is_finished, job.user.id])
    return render_template('corona.html', i=i)


@app.route('/departments')
def main1():
    db_session.global_init("db/blogs.sqlite")
    session = db_session.create_session()

    i = []
    for job in session.query(Departments).all():
        team = session.query(User).filter(User.id == job.chief).first().name
        team += ' ' + session.query(User).filter(User.id == job.chief).first().surname
        i.append([job.id, job.title, team, job.members, job.email, job.user.id])
    return render_template('department.html', i=i)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")


@app.route('/index')
@app.route('/')
def qwe():
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
