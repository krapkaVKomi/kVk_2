from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from email_validator import validate_email, EmailNotValidError
from flask_admin import Admin, AdminIndexView
from flask_admin.contrib.sqla import ModelView
from flask_security import UserMixin, RoleMixin, SQLAlchemyUserDatastore, Security, login_required, current_user
from werkzeug.utils import secure_filename
import os

    ### ЗАДАЧІ
        # Зображення в статтях
        # Система тегів і пошуку статей
        # Профіль юзера

# папка для сохранения загруженных файлов
UPLOAD_FOLDER = 'static/images/'
# расширения файлов, которые разрешено загружать
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///kvk_blog3.db'
# app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:postgres@localhost:5432/kvk_blog'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'super secret key'
app.config['SECURITY_PASSWORD_SALT'] = 'some arbitrary super secret string'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
db = SQLAlchemy(app)


class HomeAdminView(AdminIndexView):
    def is_accessible(self):
        return current_user.has_role('admin')

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('security.login', next=request.url))


admin = Admin(app, 'FlaskApp', url='/', index_view=HomeAdminView(name='Home'))

roles_users = db.Table('roles_users',
                       db.Column('user_id', db.Integer(), db.ForeignKey('user.id')),
                       db.Column('role_id', db.Integer(), db.ForeignKey('role.id'))
                       )


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(50), unique=True)
    password = db.Column(db.String(255))
    active = db.Column(db.Boolean())
    roles = db.relationship('Role', secondary=roles_users, backref=db.backref('users', lazy='dynamic'))
    posts = db.relationship('Articles', backref='poster')
    avatar = db.Column(db.Text, nullable=True)
    name = db.Column(db.String(50))


class Role(db.Model, RoleMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True)
    description = db.Column(db.String(255))


class Articles(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=True)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    title = db.Column(db.String(500), nullable=True)
    intro = db.Column(db.String(500), nullable=True)
    text = db.Column(db.Text, nullable=True)
    user = db.Column(db.String(50), nullable=True)
    poster_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    img = db.Column(db.Text, nullable=True)


class Avatars(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    img = db.Column(db.Text)
    poster_id = db.Column(db.Integer, db.ForeignKey('user.id'))


class AdminView(ModelView):
    def is_accessible(self):
        return current_user.has_role('admin')

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('security.login', next=request.url))


db.create_all()
db.session.commit()


admin.add_view(AdminView(Articles, db.session))
user_datastore = SQLAlchemyUserDatastore(db, User, Role)
security = Security(app, user_datastore)


@app.route('/uploads/<name>')
def download_file(name):
    return send_from_directory(app.config["UPLOAD_FOLDER"], name)


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/registration', methods=['POST', 'GET'])
def registration():
    if request.method == "POST":
        email = request.form['email']
        password = request.form['password']
        password2 = request.form['password2']
        name = request.form['name']
        erors = []

        # перевірка поля email
        try:
            email = validate_email(email).email
        except EmailNotValidError:
            erors.append('ПОМИЛКА!   Не правильна електронна адреса')
        try:
            user = User.query.filter(User.email == email).all()
        except:
            return "Помилка бази даних"
        if user != []:
            erors.append('Помилка!   Електронна адреса зайнята')
        # перевіркка паролю
        if len(password) < 6 or len(password) > 33:
            erors.append('ПОМИЛКА!   Пароль не може бути коротшим 6 символів, та має бути не довшим 33 символів')
        else:
            pass
        # перевірка паролю №2
        if password2 != password:
            erors.append('ПОМИЛКА!   Паролi в обох полях не співпадають')
        else:
            pass
        # створюємо і відправляємо екземпляр класу User
        if len(erors) == 0:
            new_user = User(email=email, password=password, active=1, name=name)
            try:
                db.session.add(new_user)
                db.session.commit()
                return redirect('/login')
            except:
                return "Помилка при записі нового користувача в базу даних"
        else:
            return render_template('registration.html', erors=erors)

    else:
        return render_template("registration.html", erors='')


@app.route('/add-article', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        title = request.form['title']
        intro = request.form['intro']
        text = request.form['text']
        user = request.form['user']
        article = Articles(title=title, intro=intro, text=text, user=current_user.name)
        try:
            db.session.add(article)
            db.session.commit()
        except:
            return "ERROR WRITING TO DB"
    return render_template("add_article.html")


@app.route('/posts')
@app.route('/index')
@app.route('/')
def index():
    posts = Articles.query.order_by(Articles.date.desc()).all()

    pages = Articles.query.order_by(Articles.date.desc()).paginate(per_page=5)
    return render_template("posts.html", posts=posts, pages=pages)


@app.route('/posts/<int:id>')
def post(id):
    article = Articles.query.get(id)
    return render_template("post.html", article=article)


@login_required
#@app.route('/profile')
@app.route('/profile', methods=['GET', 'POST'])
def profile():
    id = current_user.id
    user_profile = User.query.get(id)
    if request.method == 'POST':
         # загрузка аватарки
        erors = []
        if 'file' not in request.files:
            erors.append('ПОМИЛКА!   Неможу прочитати файл')
            return render_template("profile.html", erors=erors)

        file = request.files['file']

        if file.filename == '':
            erors.append('ПОМИЛКА!   Немає вибраного файлу')
            return render_template("profile.html", erors=erors)
        # збереження аватарки
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            name_add = ''
            flag = True
            for i in reversed(filename):
                if i == '.':
                    flag = False
                if flag == True:
                    name_add += i
            new_name = '.'
            for i in reversed(name_add):
                new_name += i
            a = str(datetime.utcnow())
            b = ''
            c = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '0']
            for i in a:
                if i in c:
                    b += i
            avatar = b + 'id-avatar' + str(current_user.id) + new_name
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], avatar))

            current_user.avatar = avatar
            db.session.commit()
            return redirect('/profile')

    else:
        return render_template("profile.html", user_profile=current_user)


if __name__ == "__main__":
    app.run(debug=True)
