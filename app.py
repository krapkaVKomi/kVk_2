from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from email_validator import validate_email, EmailNotValidError
from flask_admin import Admin, AdminIndexView
from flask_admin.contrib.sqla import ModelView
from flask_security import UserMixin, RoleMixin, SQLAlchemyUserDatastore, Security, login_required, current_user

    ### ЗАДАЧІ
        # по 10 cтатей на сторінці, а далі перехід на іншу сторінку з наступними
        # Система тегів і пошуку статей


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///kvk_blog.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'super secret key'
app.config['SECURITY_PASSWORD_SALT'] = 'some arbitrary super secret string'

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
    text = db.Column(db.Text(50000), nullable=True)
    user = db.Column(db.String(50), nullable=True)


class AdminView(ModelView):
    def is_accessible(self):
        return current_user.has_role('admin')

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('security.login', next=request.url))


admin.add_view(AdminView(Articles, db.session))
user_datastore = SQLAlchemyUserDatastore(db, User, Role)
security = Security(app, user_datastore)


@app.route('/about')
def about():
    return render_template('test.html')


@app.route('/registration', methods=['POST', 'GET'])
def registration():
    if request.method == "POST":
        email = request.form['email']
        password = request.form['password']
        password2 = request.form['password2']
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
            new_user = User(email=email, password=password, active=1)
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


@app.route('/add-article', methods=['POST', 'GET'])
@login_required
def create_article():
    if request.method == "POST":
        title = request.form['title']
        intro = request.form['intro']
        text = request.form['text']
        user = request.form['user']

        article = Articles(title=title, intro=intro, text=text, user=user)
        try:
            db.session.add(article)
            db.session.commit()
            return redirect('/posts')
        except:
            return "Помилка при записі статті в базу даних"
    else:
        return render_template("create-article.html")


@app.route('/posts')
@app.route('/index')
@app.route('/')
def index():
    posts = Articles.query.order_by(Articles.date.desc()).all()

    pages = Articles.query.order_by(Articles.date.desc()).paginate(per_page=2)
    return render_template("posts.html", posts=posts, pages=pages)


@app.route('/posts/<int:id>')
def post(id):
    article = Articles.query.get(id)
    return render_template("post.html", article=article)


if __name__ == "__main__":
    app.run(debug=True)
