import datetime
import json
import sqlite3
from os import remove
from os.path import exists
from helper import time_finder, user_finder, user_writer, text_writer
from PIL import Image

from werkzeug.security import check_password_hash, generate_password_hash
from flask import Flask, render_template, request, redirect, flash, url_for
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user
from flask_sqlalchemy import SQLAlchemy


app = Flask(__name__)
app.secret_key = '365424'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///shop.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
manager = LoginManager(app)

LOGIN = ''
time = int(datetime.datetime.now().hour)
TIME = time_finder(time)


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    login = db.Column(db.String(100), nullable=False, unique=True)
    password = db.Column(db.String(100), nullable=False)


@manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)


@app.route('/login', methods=['GET', 'POST'])
def login_page():
    login = request.form.get('login')
    password = request.form.get('password')

    if login and password:
        user = User.query.filter_by(login=login).first()

        if user and check_password_hash(user.password, password):

            user_writer(login)

            login_user(user)
            return redirect(url_for('create'))
        else:
            flash('not correct login/password/name')
    else:
        flash('fill login/password')

    return render_template('login.html')


@app.route('/change_password', methods=['GET', 'POST'])
def change_password():
    name = user_finder()
    com = sqlite3.connect('shop.db')
    cum = com.cursor()
    if request.method == 'POST':
        new_pwd = request.form.get('new_password')
        new_pwd1 = request.form.get('new_password1')

        login = request.form.get('login')
        if str(login) != str(name):
            flash('login is not correct')
        if str(new_pwd) != str(new_pwd1):
            flash('passwords are not equal!')
        if new_pwd and str(login) == str(name):

            sql_delete_query = f'''DELETE from user where login = "{login}"'''
            cum.execute(sql_delete_query)
            com.commit()

            hash_pwd = generate_password_hash(new_pwd)
            new_user = User(name=name, login=login, password=hash_pwd)
            db.session.add(new_user)
            db.session.commit()
            return redirect(url_for('logout'))

    return render_template('change_pwd.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    login = request.form.get('login')
    password1 = request.form.get('password1')
    password2 = request.form.get('password2')
    name = request.form.get('name')
    if request.method == 'POST':
        con = sqlite3.connect('shop.db')
        cur = con.cursor()
        res = cur.execute('''SELECT login FROM user''').fetchall()
        if str(login) in [str(i[0]) for i in res]:
            flash('Login already taken!')
        elif not (login or password1 or password2 or name):
            flash('Fill login | password!')
        elif password1 != password2:
            flash('Passwords are not equal!')
        elif len(name) > 15:
            flash('Name is too long!')
        elif len(login) < 4:
            flash('login is too short')
        else:
            hash_pwd = generate_password_hash(password1)
            new_user = User(name=name, login=login, password=hash_pwd)
            db.session.add(new_user)
            db.session.commit()

            return redirect(url_for('login_page'))
    return render_template('register.html')


@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    user_writer('')
    return redirect(url_for('login_page'))


@app.after_request
def redirect_to_sign_in(response):
    if int(response.status_code) == 401:
        return redirect(url_for('login_page') + '?next=' + request.url)

    return response


@app.route('/sample_file_upload', methods=['POST', 'GET'])
def sample_file_upload():
    if request.method == 'POST':
        f = request.files['file']
        name = user_finder()
        try:
            f = f.read()
            text_writer(f)
            with open('text.txt', 'rb') as textfile:
                bytestring = textfile.read()
                try:
                    remove(f'static/{name}.jpg')
                except ValueError:
                    pass
                with open(f'static/{name}.jpg', 'wb') as imagefile:

                    imagefile.write(bytestring)

            return redirect(url_for('create'))
        except ValueError:
            pass
    return render_template('face.html')


class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    type = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Integer, nullable=False)
    picture = db.Column(db.String(100))

    def __repr__(self):
        return self.title


# c:/Users/79876/PycharmProjects/WebProject/img/paw.png
@login_required
def find_items(items, title):
    new_items = []
    for i in list(items):
        if title in str(i):
            new_items.append(i)
    return new_items


@app.route('/', methods=['POST', 'GET'])
def index():
    items = Item.query.order_by(Item.price).all()

    con = sqlite3.connect('shop.db')
    cur = con.cursor()
    types = []
    d = []

    if request.method == 'POST':
        types = request.form.getlist('guns')
        types = tuple(types)

        login = user_finder()

        try:

            if login:
                title = request.form['title']
                items = find_items(items, title)
            else:
                return redirect(url_for('login_page'))

        except KeyError:

            with open('shop.json', encoding='utf8') as file:
                data = json.load(file)

                sub = request.form.get('sub_b')
                sub = ' '.join(sub.split()[1:])
                item_res = cur.execute(
                    f'''SELECT picture, title, price FROM item where title like "{sub}"''').fetchall()

                if login not in data:
                    data[login] = []
                data[login] = data[login] + item_res

            with open('shop.json', 'w', encoding='utf8') as file:
                json.dump(data, file, ensure_ascii=False, indent=2)

    a = []
    for i in items:
        a.append(str(i))
    if types:
        if len(types) > 1:
            task = f'''SELECT title FROM item where type in {types}'''
            type_res = cur.execute(task).fetchall()
        else:
            task = f'''SELECT title FROM item where type = "{types[0]}"'''
            type_res = cur.execute(task).fetchall()
    else:
        type_res = []
    print(type_res)
    print(items)
    new_items = []
    if type_res:
        for i in type_res:
            for j in items:
                if i[0] in str(j):
                    new_items.append(j)
        print(new_items)
        items = new_items

    for i in range(0, len(items), 3):
        try:
            d.append([items[i], items[i + 1], items[i + 2]])
        except IndexError:
            try:
                d.append([items[i], items[i + 1]])
            except IndexError:
                d.append([items[i]])
    if d:
        return render_template('index.html', data=d)
    else:
        return render_template('no_items.html')


@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/personal', methods=['POST', 'GET'])
@login_required
def create():
    login = user_finder()

    if request.method == 'POST':
        try:
            title = request.form['delete_t']

            with open('shop.json', encoding='utf8') as file:
                data = json.load(file)

                res = data[login]
                i = 0
                del_item = []
                while i != len(res):
                    if title in res[i]:
                        del_item = res[i]
                        break
                    i += 1

                res.remove(del_item)
                data[login] = res

            with open('shop.json', 'w', encoding='utf8') as file:
                json.dump(data, file, ensure_ascii=False, indent=2)
        except ValueError:
            pass

    try:
        with open('shop.json', 'r', encoding='utf8') as file:
            data_list = json.load(file)[login]
            price = sum(data_list[i][-1] for i in range(len(data_list)))
    except KeyError:
        data_list = 0
        price = 0
    com = sqlite3.connect('shop.db')
    cum = com.cursor()
    name = cum.execute(f'''SELECT name FROM user where login = "{login}"''').fetchall()[0][0]
    if exists(f'static/{login}.jpg'):
        return render_template('cab.html', time=TIME, user=str(name), data=data_list, price=price, pic=f'{login}.jpg')
    else:
        return render_template('cab.html', time=TIME, user=str(name), data=data_list, price=price, pic='main_face.jpg')


if __name__ == '__main__':
    app.run(debug=True)
