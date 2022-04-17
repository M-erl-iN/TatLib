from data import db_session
from data.words import Word


db_session.global_init('db/database.db')
session = db_session.create_session()
words_ = [['сказать', 'әйтергә'],
['этот', 'бу'],
['который', 'Ул'],
['мочь', 'бәвел'],
['человек', 'кеше'],
['о', 'о'],
['один', 'берсе'],
['бы', 'бы'],
['такой', 'мондый'],
['только', 'бары тик'],
['себя', 'үз-үзен'],
['какой', 'нинди'],
['когда', 'кайчан'],
['уже', 'инде'],
['для', 'өчен'],
['вот', 'Менә'],
['кто', 'Кем'],
['да', 'әйе'],
['говорить', 'сөйләргә'],
['год', 'бер ел'],
['знать', 'белергә'],
['мой', 'минеке'],
['до', 'кадәр'],
['или', 'яисә'],
['если', 'әгәр'],
['время', 'Вакыт'],
['рука', 'кул'],
['нет', 'юк'],
['самый', 'иң'],
['стать', 'булырга'],
['большой', 'зур'],
['даже', 'хәтта'],
['другой', 'Икенче'],
['наш', 'безнеке'],
['свой', 'үзеңнеке'],
['под', 'астына'],
['где', 'кайда'],
['дело', 'эш'],
['есть', 'бар'],
['сам', 'үзе'],
['раз', 'бер'],
['чтобы', 'өчен'],
['два', 'ике'],
['там', 'анда'],
['чем', 'нәрсә белән'],
['глаз', 'күзләр'],
['жизнь', 'тормыш'],
['первый', 'беренчесе'],
['день', 'көн'],
['ничто', 'бернәрсә дә'],
['потом', 'Аннары'],
['очень', 'бик'],
['хотеть', 'Теләү'],
['ли', 'ли'],
['при', 'при'],
['голова', 'баш'],
['надо', 'кирәк'],
['без', 'без'],
['видеть', 'күрергә'],
['идти', 'барырга'],
['теперь', 'хәзер'],
['тоже', 'шулай ук'],
['стоять', 'басып торырга'],
['друг', 'дус'],
['дом', 'йорт'],
['сейчас', 'хәзер'],
['можно', 'Мөмкин'],
['после', 'Соңыннан'],
['слово', 'сүз'],
['здесь', 'монда'],
['думать', 'уйларга'],
['место', 'урын'],
['через', 'аша'],
['лицо', 'йөзе'],
['что', 'нәрсә'],
['тогда', 'ул вакытта'],
['ведь', 'бит'],
['хороший', 'яхшы']]
for i in words_:
    word = Word()
    word.word = i[1]
    word.word_ru = i[0]
    session.add(word)
session.commit()