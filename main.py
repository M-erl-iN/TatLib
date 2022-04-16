from flask import Flask, render_template, redirect, request, make_response, jsonify
import datetime
from random import shuffle, choice
from data import db_session, books_api, users_api, words_api, levels_api, word_levels_api
from data.users import User
from data.questions import Question
from data.words import Word
from data.word_levels import Word_level
from data.levels import Level
from data.questions import Question
from data.books import Book
from forms.login import LoginForm
from forms.register import RegisterForm
from forms.quiz import QuizForm
from flask_login import LoginManager, current_user, login_user, login_required, logout_user, mixins

app = Flask(__name__)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'
login_manager = LoginManager()
login_manager.init_app(app)
user_progress = {}
max_question_id = 1
quiz_analyze_session = None
table_stage2time = {
    0: 0,
    1: 1,
    2: 3,
    3: 5,
    4: 6,
    5: 13,
    6: 28,
    7: 58,
    8: 118
}


def training_dict():
    now_time = datetime.datetime.now()
    final_dict = []
    wordlist = list(quiz_analyze_session.query(Word).all())
    userwordlist = list(quiz_analyze_session.query(Word).filter(Word.id.in_(
        [int(i) for i in current_user.words.split(',')])).all())
    shuffle(wordlist)
    shuffle(userwordlist)
    for word in range(len(userwordlist)):
        word_level = quiz_analyze_session.query(Word_level).filter(Word_level.word_id == userwordlist[word].id,
                                                                   Word_level.user_id == current_user.id).first()
        date = word_level.date
        stage = word_level.word_level
        if stage == 8:
            quiz_analyze_session.delete(userwordlist[word], word_level)
            quiz_analyze_session.commit()
        last_time = datetime.datetime.fromisoformat(str(date))  # ДД-ММ-ГГ
        limit_timedelta = datetime.timedelta(days=table_stage2time[stage])
        """word_level.word_level += 1
        quiz_analyze_session.commit()"""
        if (now_time - last_time) > limit_timedelta:
            final_dict.append([userwordlist[word].word])
            final_dict[word].append(userwordlist[word].word_ru)
            final_dict[word].append([userwordlist[word].word_ru])
            while len(final_dict[word][2]) < 4:
                ch = choice(wordlist)
                try_list = [i[0] for i in final_dict[word][2]]
                if ch.word not in try_list:
                    final_dict[word][2].append(ch.word_ru)
            shuffle(final_dict[word][2])
            for i in range(len(final_dict[word][2])):
                ind = 1 if final_dict[word][2][i] == final_dict[word][1] else 0
                final_dict[word][2][i] = (final_dict[word][2][i], ind)
    return final_dict


def training3_dict():
    now_time = datetime.datetime.now()
    final_dict = []
    wordlist = list(quiz_analyze_session.query(Word).all())
    userwordlist = list(quiz_analyze_session.query(Word).filter(Word.id.in_(
        [int(i) for i in current_user.words.split(',')])).all())
    shuffle(wordlist)
    shuffle(userwordlist)
    for word in range(len(userwordlist)):
        word_level = quiz_analyze_session.query(Word_level).filter(Word_level.word_id == userwordlist[word].id,
                                                                   Word_level.user_id == current_user.id).first()
        date = word_level.date
        stage = word_level.word_level
        if stage == 8:
            quiz_analyze_session.delete(userwordlist[word], word_level)
            quiz_analyze_session.commit()
        last_time = datetime.datetime.fromisoformat(str(date))  # ДД-ММ-ГГ
        limit_timedelta = datetime.timedelta(days=table_stage2time[stage])
        """word_level.word_level += 1
        quiz_analyze_session.commit()"""
        if (now_time - last_time) > limit_timedelta:
            shuffled_word = list(userwordlist[word].word)
            shuffle(shuffled_word)
            final_dict.append([userwordlist[word].word, ''.join(shuffled_word)])
    return final_dict


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


@app.errorhandler(404)
def not_found(error):
    print(error)
    return render_template("404.html", title='404')


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


@app.route('/quiz', methods=['GET', 'POST'])
def quiz_form():
    if request.method == 'GET' and not isinstance(current_user, mixins.AnonymousUserMixin):
        try:
            if user_progress[current_user.id]["quiz"]["question_number"] == max_question_id + 1:
                try:
                    user_progress[current_user.id]["quiz"] = {'id': current_user.id, 'question_number': 1, 'count': 0,
                                                      'showed': False}
                except KeyError:
                    user_progress[current_user.id] = {}
                    user_progress[current_user.id]["quiz"] = {'id': current_user.id, 'question_number': 1, 'count': 0,
                                                              'showed': False}
        except:
            try:
                user_progress[current_user.id]["quiz"] = {'id': current_user.id, 'question_number': 1, 'count': 0,
                                                          'showed': False}
            except KeyError:
                user_progress[current_user.id] = {}
                user_progress[current_user.id]["quiz"] = {'id': current_user.id, 'question_number': 1, 'count': 0,
                                                          'showed': False}
        question_number = user_progress[current_user.id]["quiz"]["question_number"]
        quest = quiz_analyze_session.query(Question).filter(Question.id == question_number).first()
        answers_ = [int(i) for i in str(quest.answers).split(',')]
        answers_objects = []
        for i in quiz_analyze_session.query(Word):
            if i.id in answers_:
                answers_objects.append(i.word)
        current_answer = quiz_analyze_session.query(Word).filter(Word.id == quest.correct_answer).first().word
        form = QuizForm(quest.question, answers_objects, current_answer)
        params = {
            'question': form.question,
            'answers': form.answers_list,
            'current_answer': user_progress[current_user.id]["quiz"]["question_number"],
            'title': 'Quiz Answer' + str(user_progress[current_user.id]["quiz"]["question_number"])
        }
        return render_template('quiz.html', **params)
    elif request.method == 'POST' and type(current_user) != "AnonymousUserMixin":
        if request.form is not None:
            if len(request.form) > 1:
                user_progress[current_user.id]["quiz"]["question_number"] += 1
                user_progress[current_user.id]["quiz"]["count"] += int(request.form["options"])
        if user_progress[current_user.id]["quiz"]["question_number"] == max_question_id + 1:
            return redirect('/quiz_result')
        return redirect('/quiz')
    else:
        return redirect('/register')


@app.route('/quiz_result')
def quiz_result():
    try:
        count = user_progress[current_user.id]["quiz"]["count"]
        level_name = user_progress[current_user.id]["quiz"]["question_number"] - 1
    except:
        return redirect('/quiz')
    params = {
        'count': count,
        'level': level_name,
        'title': 'Quiz Result'
    }
    if user_progress[current_user.id]["quiz"]["showed"]:
        return render_template('quiz_rezult.html', **params)
    level_name = count / level_name
    if level_name < 0.3334:
        level_name = "Новичок"
    elif level_name < 0.6667:
        level_name = "Средний"
    else:
        level_name = "Профи"
    params["level_name"] = level_name
    user = quiz_analyze_session.query(User).filter(User.id == current_user.id).first()
    id_ = quiz_analyze_session.query(Level).filter(Level.name == level_name).first().level_id
    user.level_id = id_
    quiz_analyze_session.commit()
    user_progress[current_user.id]["quiz"]["showed"] = True
    return render_template('quiz_rezult.html', **params)


@app.route('/training/1', methods=['GET', 'POST'])
def training1_form():
    if request.method == 'GET' and not isinstance(current_user, mixins.AnonymousUserMixin):
        try:
            if user_progress[current_user.id]["tr1"]["question_training_number"] == user_progress[current_user.id]["tr1"]['train_len']:
                try:
                    user_progress[current_user.id]["tr1"] = {'id': current_user.id, 'question_training_number': 0,
                                                      'count_training': 0, 'showed': False,
                                                      'training_program': training_dict()}
                    user_progress[current_user.id]["tr1"]['train_len'] = len(user_progress[current_user.id]["tr1"]['training_program'])
                except KeyError:
                    user_progress[current_user.id] = {}
                    user_progress[current_user.id]["tr1"] = {'id': current_user.id, 'question_training_number': 0,
                                                             'count_training': 0, 'showed': False,
                                                             'training_program': training_dict()}
                    user_progress[current_user.id]["tr1"]['train_len'] = len(
                        user_progress[current_user.id]["tr1"]['training_program'])
        except:
            try:
                user_progress[current_user.id]["tr1"] = {'id': current_user.id, 'question_training_number': 0,
                                                         'count_training': 0, 'showed': False,
                                                         'training_program': training_dict()}
                user_progress[current_user.id]["tr1"]['train_len'] = len(
                    user_progress[current_user.id]["tr1"]['training_program'])
            except KeyError:
                user_progress[current_user.id] = {}
                user_progress[current_user.id]["tr1"] = {'id': current_user.id, 'question_training_number': 0,
                                                         'count_training': 0, 'showed': False,
                                                         'training_program': training_dict()}
                user_progress[current_user.id]["tr1"]['train_len'] = len(
                    user_progress[current_user.id]["tr1"]['training_program'])
        num = user_progress[current_user.id]["tr1"]['question_training_number']
        train = user_progress[current_user.id]["tr1"]['training_program']
        params = {
            'question': train[num][0],
            'answers': train[num][2],
            'current_answer': train[num][1],
            'title': 'Training' + train[num][0]
        }
        return render_template('training1.html', **params)
    elif request.method == 'POST' and type(current_user) != "AnonymousUserMixin":
        num = user_progress[current_user.id]["tr1"]['question_training_number']
        train = user_progress[current_user.id]["tr1"]['training_program']
        if request.form is not None:
            if len(request.form) > 1:
                user_progress[current_user.id]["tr1"]["question_training_number"] += 1
                user_progress[current_user.id]["tr1"]["count_training"] += int(request.form["options"])
                last_word = quiz_analyze_session.query(Word).filter(Word.word == train[num][0]).first()
                if int(request.form["options"]) == 1: # int(request.form["options"]) [0 or 1] правильность слова
                    # last_word.level += 1
                    pass
                elif int(request.form["options"]) == 0:
                    last_word.level = 0
                quiz_analyze_session.commit()
        if user_progress[current_user.id]["tr1"]['question_training_number'] == user_progress[current_user.id]["tr1"]['train_len']:
            return redirect('/training/1_result')
        return redirect('/training/1')
    else:
        return redirect('/register')


@app.route('/training/1_result')
def training1_result():
    try:
        count = user_progress[current_user.id]["tr1"]["count_training"]
        level = user_progress[current_user.id]["tr1"]["question_training_number"]
    except:
        return redirect('/training/1')
    params = {
        'count': count,
        'level': level,
        'title': 'Training Result'
    }
    if user_progress[current_user.id]["tr1"]["showed"]:
        return render_template('training1_rezult.html', **params)
    level_name = count / level
    if level_name < 0.3334:
        level_name = "Новичок"
    elif level_name < 0.6667:
        level_name = "Средний"
    else:
        level_name = "Профи"
    params["level_name"] = level_name
    user = quiz_analyze_session.query(User).filter(User.id == current_user.id).first()
    id_ = quiz_analyze_session.query(Level).filter(Level.name == level_name).first().level_id
    user.level_id = id_
    quiz_analyze_session.commit()
    user_progress[current_user.id]["tr1"]["showed"] = True
    return render_template('training1_rezult.html', **params)


@app.route('/training/2', methods=['GET', 'POST'])
def training2_form():
    if request.method == 'GET' and not isinstance(current_user, mixins.AnonymousUserMixin):
        try:
            if user_progress[current_user.id]["tr2"]["training2_number"] == user_progress[current_user.id]["tr2"]['train_len']:
                try:
                    user_progress[current_user.id]["tr2"] = {'id': current_user.id, 'question_training_number': 0,
                                                      'count_training': 0, 'showed': False,
                                                      'training_program': training_dict()}
                    user_progress[current_user.id]["tr2"]['train_len'] = len(user_progress[current_user.id]["tr2"]['training_program'])
                except KeyError:
                    user_progress[current_user.id] = {}
                    user_progress[current_user.id]["tr2"] = {'id': current_user.id, 'question_training_number': 0,
                                                             'count_training': 0, 'showed': False,
                                                             'training_program': training_dict()}
                    user_progress[current_user.id]["tr2"]['train_len'] = len(
                        user_progress[current_user.id]["tr2"]['training_program'])
        except:
            try:
                user_progress[current_user.id]["tr2"] = {'id': current_user.id, 'question_training_number': 0,
                                                         'count_training': 0, 'showed': False,
                                                         'training_program': training_dict()}
                user_progress[current_user.id]["tr2"]['train_len'] = len(
                    user_progress[current_user.id]["tr2"]['training_program'])
            except KeyError:
                user_progress[current_user.id] = {}
                user_progress[current_user.id]["tr2"] = {'id': current_user.id, 'question_training_number': 0,
                                                         'count_training': 0, 'showed': False,
                                                         'training_program': training_dict()}
                user_progress[current_user.id]["tr2"]['train_len'] = len(
                    user_progress[current_user.id]["tr2"]['training_program'])
        num = user_progress[current_user.id]["tr2"]['question_training_number']
        train = user_progress[current_user.id]["tr2"]['training_program']
        params = {
            'question': train[num][0],
            'answers': train[num][2],
            'current_answer': train[num][1],
            'title': 'Training' + train[num][0]
        }
        return render_template('training1.html', **params)
    elif request.method == 'POST' and type(current_user) != "AnonymousUserMixin":
        num = user_progress[current_user.id]["tr2"]['question_training_number']
        train = user_progress[current_user.id]["tr2"]['training_program']
        if request.form is not None:
            if len(request.form) > 1:
                user_progress[current_user.id]["tr2"]["question_training_number"] += 1
                user_progress[current_user.id]["tr2"]["count_training"] += int(request.form["options"])
                last_word = quiz_analyze_session.query(Word).filter(Word.word == train[num][0]).first()
                if int(request.form["options"]) == 1:  # int(request.form["options"]) [0 or 1] правильность слова
                    # last_word.level += 1
                    pass
                elif int(request.form["options"]) == 0:
                    last_word.level = 0
                quiz_analyze_session.commit()
        if user_progress[current_user.id]["tr2"]['question_training_number'] == user_progress[current_user.id]["tr2"]['train_len']:
            return redirect('/training/1_result')
        return redirect('/training/1')
    else:
        return redirect('/register')


@app.route('/training/2_result')
def training2_result():
    try:
        count = user_progress[current_user.id]["tr2"]["count_training"]
        level = user_progress[current_user.id]["tr2"]["question_training_number"]
    except:
        return redirect('/training/2')
    params = {
        'count': count,
        'level': level,
        'title': 'Training Result'
    }
    if user_progress[current_user.id]["tr2"]["showed"]:
        return render_template('training_rezult.html', **params)
    level_name = count / level
    if level_name < 0.3334:
        level_name = "Новичок"
    elif level_name < 0.6667:
        level_name = "Средний"
    else:
        level_name = "Профи"
    params["level_name"] = level_name
    user = quiz_analyze_session.query(User).filter(User.id == current_user.id).first()
    id_ = quiz_analyze_session.query(Level).filter(Level.name == level_name).first().level_id
    user.level_id = id_
    quiz_analyze_session.commit()
    user_progress[current_user.id]["tr2"]["showed"] = True
    return render_template('training_rezult.html', **params)


@app.route('/training/3', methods=['GET', 'POST'])
def training3_form():
    if request.method == 'GET' and not isinstance(current_user, mixins.AnonymousUserMixin):
        try:
            if user_progress[current_user.id]["tr3"]["question_training_number"] == user_progress[current_user.id]["tr3"]['train_len']:
                try:
                    user_progress[current_user.id]["tr3"] = {'id': current_user.id, 'question_training_number': 0,
                                                      'count_training': 0, 'showed': False,
                                                      'training_program': training3_dict()}
                    user_progress[current_user.id]["tr3"]['train_len'] = len(user_progress[current_user.id]["tr3"]['training_program'])
                except KeyError:
                    user_progress[current_user.id] = {}
                    user_progress[current_user.id]["tr3"] = {'id': current_user.id, 'question_training_number': 0,
                                                             'count_training': 0, 'showed': False,
                                                             'training_program': training3_dict()}
                    user_progress[current_user.id]["tr3"]['train_len'] = len(
                        user_progress[current_user.id]["tr3"]['training_program'])
        except:
            try:
                user_progress[current_user.id]["tr3"] = {'id': current_user.id, 'question_training_number': 0,
                                                         'count_training': 0, 'showed': False,
                                                         'training_program': training3_dict()}
                user_progress[current_user.id]["tr3"]['train_len'] = len(
                    user_progress[current_user.id]["tr3"]['training_program'])
            except KeyError:
                user_progress[current_user.id] = {}
                user_progress[current_user.id]["tr3"] = {'id': current_user.id, 'question_training_number': 0,
                                                         'count_training': 0, 'showed': False,
                                                         'training_program': training3_dict()}
                user_progress[current_user.id]["tr3"]['train_len'] = len(
                    user_progress[current_user.id]["tr3"]['training_program'])
        num = user_progress[current_user.id]["tr3"]['question_training_number']
        train = user_progress[current_user.id]["tr3"]['training_program']
        params = {
            'question': train[num][1]
        }
        return render_template('training3.html', **params)
    elif request.method == 'POST' and type(current_user) != "AnonymousUserMixin":
        num = user_progress[current_user.id]["tr3"]['question_training_number']
        train = user_progress[current_user.id]["tr3"]['training_program']
        if request.form is not None:
            if len(request.form) > 1:
                user_progress[current_user.id]["tr3"]["question_training_number"] += 1
                last_word = quiz_analyze_session.query(Word).filter(Word.word == train[num][0]).first()
                if request.form["user_answer"] == train[num][0]:
                    user_progress[current_user.id]["tr3"]["count_training"] += 1
                    # last_word.level += 1
                    pass
                else:
                    last_word.level = 0
                quiz_analyze_session.commit()
        if user_progress[current_user.id]["tr3"]['question_training_number'] == user_progress[current_user.id]["tr3"]['train_len']:
            return redirect('/training/3_result')
        return redirect('/training/3')
    else:
        return redirect('/register')


@app.route('/training/3_result')
def training3_result():
    try:
        count = user_progress[current_user.id]["tr3"]["count_training"]
        level = user_progress[current_user.id]["tr3"]["question_training_number"]
    except:
        return redirect('/training/3')
    params = {
        'count': count,
        'level': level
    }
    if user_progress[current_user.id]["tr3"]["showed"]:
        return render_template('training_rezult.html', **params)
    level_name = count / level
    if level_name < 0.3334:
        level_name = "Новичок"
    elif level_name < 0.6667:
        level_name = "Средний"
    else:
        level_name = "Профи"
    params["level_name"] = level_name
    user = quiz_analyze_session.query(User).filter(User.id == current_user.id).first()
    id_ = quiz_analyze_session.query(Level).filter(Level.name == level_name).first().level_id
    user.level_id = id_
    quiz_analyze_session.commit()
    user_progress[current_user.id]["tr3"]["showed"] = True
    return render_template('training3_rezult.html', **params)


def set_max_question_id():
    global max_question_id, quiz_analyze_session
    quiz_analyze_session = db_session.create_session()
    max_question_id = quiz_analyze_session.query(Question).order_by(Question.id.desc()).first().id


def main():
    db_session.global_init("db/database.db")
    set_max_question_id()
    app.register_blueprint(books_api.blueprint)
    app.register_blueprint(users_api.blueprint)
    app.register_blueprint(words_api.blueprint)
    app.register_blueprint(levels_api.blueprint)
    app.register_blueprint(word_levels_api.blueprint)
    app.run(port=8080, host='127.0.0.1')


if __name__ == '__main__':
    main()
