import sqlalchemy
from flask import Flask, render_template, redirect, request, make_response, jsonify
from data import db_session, books_api, users_api, words_api, levels_api, word_levels_api
from data.users import User
from data.words import Word
from data.word_levels import Word_level
from data.levels import Level
from data.questions import Question
from data.books import Book
from forms.login import LoginForm
from forms.register import RegisterForm
from forms.add_text import TextForm
from flask_login import LoginManager, current_user, login_user, login_required, logout_user
import os, shutil

app = Flask(__name__)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'
login_manager = LoginManager()
login_manager.init_app(app)


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ['epub']

@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(User).get(user_id)

@app.route("/logout")
def logout():
    logout_user()
    return redirect("/")

@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template('index.html', title='index')

@app.errorhandler(401)
def not_found(error):
    return redirect('/register')

@app.errorhandler(404)
def not_found(error):
    print(error)
    return make_response(jsonify({'error': 'Not found'}), 404)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.email == form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect("/")
        return render_template('login.html',
                               message="Неправильный логин или пароль",
                               form=form)
    return render_template('login.html', title='Авторизация', form=form)

@app.route('/register', methods=['GET', 'POST'])
def reqister():
    form = RegisterForm()
    if form.validate_on_submit():
        if form.password.data != form.password_again.data:
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Пароли не совпадают")
        db_sess = db_session.create_session()
        if db_sess.query(User).filter(User.email == form.email.data).first():
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Такой пользователь уже есть")
        user = User(
            name=form.name.data,
            email=form.email.data,
        )
        user.set_password(form.password.data)
        db_sess.add(user)
        db_sess.commit()
        return redirect('/login')
    return render_template('register.html', title='Регистрация', form=form)


@app.route('/training/<int:num>', methods=['GET', 'POST'])
@login_required
def training(num):

    return render_template('training.html', title=f'тренировка {num}')


@app.route('/settings')
@login_required
def settings():
    return render_template('settings.html')


@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html')


@app.route('/books_and_texts/<int:val>', methods=['GET', 'POST'])
@login_required
def books_and_texts(val):
    db_sess = db_session.create_session()
    if request.method == 'POST':
        books = db_sess.query(Book).filter((Book.title.like(f"%{request.form.get('field')}%")) | (Book.author.like(f"%{request.form.get('field')}%")))
        return render_template('books_and_texts.html', title='книги и тексты', books=books)
    if val == 0:
        books = db_sess.query(Book).all()
    else:
        books = db_sess.query(Book).filter(Book.level_id == val).all()
    return render_template('books_and_texts.html', title='книги и тексты', books=books)


@app.route('/words', methods=['GET', 'POST'])
@login_required
def words():
    db_sess = db_session.create_session()
    user_words_id = db_sess.query(User.words).filter(User.id == current_user.id).first()[0].split(',')
    if request.method == 'POST':
        words = db_sess.query(Word).filter((Word.word.like(f"%{request.form.get('field')}%")) | (Word.word_ru.like(f"%{request.form.get('field')}%")), Word.id.in_(list(map(int, user_words_id))))
        return render_template('words.html', title='мои слова', words=words)
    user_words_id = db_sess.query(User.words).filter(User.id == current_user.id, Word.id.in_(list(map(int, user_words_id)))).first()[0].split(',')
    words = db_sess.query(Word).filter(Word.id.in_(list(map(int, user_words_id)))).all()
    return render_template('words.html', title='мои слова', words=words)


@app.route('/books', methods=['GET', 'POST'])
@login_required
def books():
    db_sess = db_session.create_session()
    if request.method == 'POST':
        books = db_sess.query(Book).filter(Book.user_author_id == current_user.id, Book.title.like(f"%{request.form.get('field')}%")).all()
        return render_template('books.html', title='мои слова', books=books)
    books = db_sess.query(Book).filter(Book.user_author_id == current_user.id).all()
    return render_template('books.html', title='мои слова', books=books)


@app.route('/add_text', methods=['GET', 'POST'])
@login_required
def add_text():
    form = TextForm()
    if form.validate_on_submit():
        if form.author.data and form.title.data and form.file.data and form.difficult.data:
            db_sess = db_session.create_session()
            max_id = db_sess.query(Book).order_by(Book.id).all()
            if not max_id:
                max_id = 1
            else:
                max_id = max_id[-1].id + 1
            book = Book()
            book.author = form.author.data
            book.title = form.title.data
            book.level_id = form.difficult.data
            if allowed_file(form.file.data.filename):
                f = request.files['file']
                path = f"books\{max_id}.epub"
                f.save(path)
                os.mkdir(f"books\{max_id}")
                shutil.move(f"books\{max_id}.epub", f"books\{max_id}\{max_id}.epub")
            book.pages = 1
            book.user_author_id = current_user.id
            db_sess.merge(current_user)
            db_sess.add(book)
            db_sess.commit()
            return redirect("/books_and_texts/0")
        return render_template('add_text.html',
                               message="не все поля заполнены",
                               form=form)
    return render_template('add_text.html', title='добавление текста', form=form)


def main():
    db_session.global_init("db/database.db")
    app.register_blueprint(books_api.blueprint)
    app.register_blueprint(users_api.blueprint)
    app.register_blueprint(words_api.blueprint)
    app.register_blueprint(levels_api.blueprint)
    app.register_blueprint(word_levels_api.blueprint)
    app.run(port=8080, host='127.0.0.1')


if __name__ == '__main__':
    main()
