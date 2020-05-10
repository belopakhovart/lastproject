import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from vk_api.utils import get_random_id
from data import db_session
from data.users import User
from data.indicators import Indicators
from data.mapapi import *
import requests
from bs4 import BeautifulSoup

from config import TOKEN_VK, GROUP_ID

db_session.global_init("db/info.sqlite")
session = db_session.create_session()

users_data = {}

answers = {'Да': True, 'Нет': False}

vk_session = vk_api.VkApi(token=TOKEN_VK)

RULES = '''Основные меры предосторожности для защиты от новой коронавирусной инфекции
Следите за новейшей информацией о вспышке COVID-19, которую можно найти на веб-сайте ВОЗ, а также получить от органов общественного здравоохранения вашей страны и населенного пункта. Наибольшее число случаев COVID-19 по-прежнему выявлено в Китае, тогда как в других странах отмечаются вспышки локального характера. В большинстве случаев заболевание характеризуется легким течением и заканчивается выздоровлением, хотя встречаются осложнения. Защитить свое здоровье и здоровье окружающих можно, соблюдая следующие правила: 
'''

QUESTIONS = [('Какая у Вас температура?', 0),
             ('Часто ли Вы контактируете с людьми?', 1),
             ('Были ли Вы за границей недавно?', 1),
             ('Контактировали с заболевшими?', 1),
             ('Знаете ли вы о правилах в период эпидемии?', 1),
             ('Соблюдаете ли Вы самоизоляцию?', 1),
             ('Ваш адрес', 0),
             ('Узнать результат?', 2)]


class MessageError(Exception):
    pass


def parse_news():
    url = 'https://coronavirus-monitor.ru/ru/novosti'
    response = requests.get(url).text
    if response:
        soup = BeautifulSoup(response, 'html.parser')
        news = [[i.span.text, 'https://coronavirus-monitor.ru/' + i.a.attrs["href"], i.p.text]
                for i in soup.find_all('div', {'class': 'news-element'})]
        return news[:5]
    else:
        print('error while getting page, status code: {}'.format(response.status_code))
        return None


def auth_handler():
    """ При двухфакторной аутентификации вызывается эта функция. """
    key = input("Enter authentication code: ")
    remember_device = True
    return key, remember_device


def generate_keyboard(n):
    keyboard = VkKeyboard(one_time=True)
    if n == 2:
        keyboard.add_button('Карта', color=VkKeyboardColor.PRIMARY)
        keyboard.add_button('Заполнить анкету', color=VkKeyboardColor.PRIMARY)
        keyboard.add_button('Правила при эпидемии', color=VkKeyboardColor.PRIMARY)
        keyboard.add_line()
        keyboard.add_button('Новости о коронавирусе', color=VkKeyboardColor.PRIMARY)
    else:
        keyboard.add_button('Вернуться в меню', color=VkKeyboardColor.NEGATIVE)
    return keyboard


def generate_keyboard_rules():
    keyboard = VkKeyboard(one_time=True)
    keyboard.add_button('💦👏🧼', color=VkKeyboardColor.PRIMARY)
    keyboard.add_button('👫', color=VkKeyboardColor.PRIMARY)
    keyboard.add_button('🙊🙈🙉', color=VkKeyboardColor.PRIMARY)
    keyboard.add_line()
    keyboard.add_button('😷', color=VkKeyboardColor.PRIMARY)
    keyboard.add_button('💊', color=VkKeyboardColor.PRIMARY)
    keyboard.add_line()
    keyboard.add_button('Вернуться в меню', color=VkKeyboardColor.PRIMARY)
    return keyboard


def gen_true_false_keyboard():
    keyboard = VkKeyboard(one_time=True)
    keyboard.add_button('Да', color=VkKeyboardColor.PRIMARY)
    keyboard.add_button('Нет', color=VkKeyboardColor.NEGATIVE)
    return keyboard


def gen_result_keyboard():
    keyboard = VkKeyboard(one_time=True)
    keyboard.add_button('Мой результат', color=VkKeyboardColor.PRIMARY)
    return keyboard


def answer_checking(vk, uid, msg):
    global name, surname

    users_answer = msg.text
    session = db_session.create_session()
    if users_answer == 'Мой результат':
        try:
            ind = Indicators()
            ind.user = session.query(User).filter(User.name == name, User.surname == surname).first().id
            ind.temperature = float(users_data[uid]['answers'][0].replace(',', '.'))
            ind.contact_with_people = users_data[uid]['answers'][1]
            ind.abroad = users_data[uid]['answers'][2]
            ind.people_with_corona = users_data[uid]['answers'][3]
            ind.do_user_know_about = users_data[uid]['answers'][4]
            ind.self_isolatioon = users_data[uid]['answers'][5]
            ind.address = users_data[uid]['answers'][6]
            session.add(ind)
            session.commit()
            session.close()
        except:
            vk.messages.send(user_id=uid, random_id=get_random_id(),
                             message='''Произошла ошибка. Возможно, вы невнимательно прочли правила.''',
                             keyboard=generate_keyboard(2).get_keyboard())
      
        b = {'contact_with_people': {True: 1, False: 0},
             'abroad': {True: 1, False: 0},
             'people_with_corona': {True: 1, False: 0},
             'do_user_know_about': {True: 0, False: 1},
             'self_isolatioon': {True: 0, False: 1}}
        ball = b['contact_with_people'][users_data[uid]['answers'][1]] + \
               b['abroad'][users_data[uid]['answers'][2]] + \
               b['people_with_corona'][users_data[uid]['answers'][3]] + \
               b['do_user_know_about'][users_data[uid]['answers'][4]] + \
               b['self_isolatioon'][users_data[uid]['answers'][5]] + \
               users_data[uid]['answers'][0] / 36.6

        if not users_data[uid]['answers'][4]:
            vk.messages.send(user_id=uid, random_id=get_random_id(),
                             message='''Если вы ничего не знаете о борьбе с вирусом, можете ознакомиться с 
                             основными правилами, выбрав соответствующий пункт меню. 
                             Настоятельно рекомендуем это сделать!''',
                             keyboard=generate_keyboard(2).get_keyboard())
        if users_data[uid]['answers'][3] or users_data[uid]['answers'][2] and float(users_data[uid]['answers'][0]) < 37.0:
            vk.messages.send(user_id=uid, random_id=get_random_id(),
                             message='''Хоть у Вас и нет симптомов заболевания, рекомендуем 
                             пройти 14-дневный, чтобы обезопасить себя и своих близких от коронавируса''',
                             keyboard=generate_keyboard(2).get_keyboard())
        if float(users_data[uid]['answers'][0]) >= 37.0:
            vk.messages.send(user_id=uid, random_id=get_random_id(),
                             message='''При повышении температуры следует обращаться к врачу!!!''',
                             keyboard=generate_keyboard(2).get_keyboard())
        if not users_data[uid]['answers'][5] or users_data[uid]['answers'][1]:
            vk.messages.send(user_id=uid, random_id=get_random_id(),
                             message='''Мы понимаем, что соблюдать самоизояцию тяжело. 
                             Но тем самым вы помогаете сдерживать рост заболеваемости.''',
                             keyboard=generate_keyboard(2).get_keyboard())
        if int(ball) == 1:
            vk.messages.send(user_id=uid, random_id=get_random_id(),
                             message='''Вы молодец! Спасибо, что помогаете сдерживать рост заболеваемости!!!''',
                             keyboard=generate_keyboard(2).get_keyboard())

    if users_answer == '💦👏🧼':
        a = '''1. Регулярно мойте руки
Регулярно обрабатывайте руки спиртосодержащим средством или мойте их с мылом. 
Зачем это нужно?  Если на поверхности рук присутствует вирус, то обработка рук спиртосодержащим средством или мытье их с мылом убьет его.'''
        vk.messages.send(user_id=uid, random_id=get_random_id(),
                         message=a,
                         keyboard=generate_keyboard_rules().get_keyboard())
    elif users_answer == '👫':
        a = '''2. Соблюдайте дистанцию в общественных местах
Держитесь от людей на расстоянии как минимум 1 метра, особенно если у них кашель, насморк и повышенная температура.
Зачем это нужно? Кашляя или чихая, человек, болеющий респираторной инфекцией, такой как 2019-nCoV, распространяет вокруг себя мельчайшие капли, содержащие вирус. Если вы находитесь слишком близко к такому человеку, то можете заразиться вирусом при вдыхании воздуха.
'''
        vk.messages.send(user_id=uid, random_id=get_random_id(),
                         message=a,
                         keyboard=generate_keyboard_rules().get_keyboard())

    elif users_answer == '🙊🙈🙉':
        a = '''3. По возможности, не трогайте руками глаза, нос и рот
Зачем это нужно? Руки касаются многих поверхностей, на которых может присутствовать вирус. Прикасаясь содержащими инфекцию руками к глазам, носу или рту, можно перенести вирус с кожи рук в организм.
'''
        vk.messages.send(user_id=uid, random_id=get_random_id(),
                         message=a,
                         keyboard=generate_keyboard_rules().get_keyboard())
    elif users_answer == '😷':
        a = '''4. Соблюдайте правила респираторной гигиены
При кашле и чихании прикрывайте рот и нос салфеткой или сгибом локтя; сразу выкидывайте салфетку в контейнер для мусора с крышкой и обрабатывайте руки спиртосодержащим антисептиком или мойте их водой с мылом.
Зачем это нужно? Прикрывание рта и носа при кашле и чихании позволяет предотвратить распространение вирусов и других болезнетворных микроорганизмов. Если при кашле или чихании прикрывать нос и рот рукой, микробы могут попасть на ваши руки, а затем на предметы или людей, к которым вы прикасаетесь.
'''
        vk.messages.send(user_id=uid, random_id=get_random_id(),
                         message=a,
                         keyboard=generate_keyboard_rules().get_keyboard())
    elif users_answer == '💊':
        a = '''5. При повышении температуры, появлении кашля и затруднении дыхания как можно быстрее обращайтесь за медицинской помощью
Если вы посещали районы Китая, где регистрируется 2019-nCoV, или тесно общались с кем-то, у кого после поездки из Китая наблюдаются симптомы респираторного заболевания, сообщите об этом медицинскому работнику.
Зачем это нужно? Повышение температуры, кашель и затруднение дыхания требуют незамедлительного обращения за медицинской помощью, поскольку могут быть вызваны респираторной инфекцией или другим серьезным заболеванием. Симптомы поражения органов дыхания в сочетании с повышением температуры могут иметь самые различные причины, среди которых в зависимости от совершенных пациентом поездок и его контактов может быть 2019-nCoV.'''
        vk.messages.send(user_id=uid, random_id=get_random_id(),
                         message=a,
                         keyboard=generate_keyboard_rules().get_keyboard())
    elif users_answer.lower() in ['меню', 'вернуться в меню']:
        menu(vk, uid)
    if users_answer != 'Мой результат':
        if 'answers' not in users_data[uid]:
            users_data[uid]['answers'] = []
        if users_answer in answers:
            users_data[uid]['answers'].append(answers[users_answer])
        else:
            if users_data[uid]['current_quest'][0] == 'Какая у Вас температура?':
                users_data[uid]['answers'].append(float(users_answer))
            else:
                users_data[uid]['answers'].append(users_answer)

        send_next(vk, uid)


def send_next(vk, uid):
    try:
        current_quest = next(users_data[uid]['quest'])
        users_data[uid]['current_quest'] = current_quest
        keyb = current_quest[1]
        if keyb == 0:
            vk.messages.send(user_id=uid, random_id=get_random_id(),
                             message=current_quest[0])
        elif keyb == 1:
            keyboard = gen_true_false_keyboard()
            vk.messages.send(user_id=uid, random_id=get_random_id(),
                             message=current_quest[0], keyboard=keyboard.get_keyboard())
        elif keyb == 2:
            keyboard = gen_result_keyboard()
            vk.messages.send(user_id=uid, random_id=get_random_id(),
                             message=current_quest[0], keyboard=keyboard.get_keyboard())

    except Exception as e:
        print(e)


def new_user(response, vk, uid):
    message = f"Привет, {response[0]['first_name']}!"
    vk.messages.send(user_id=uid,
                     message=message,
                     random_id=get_random_id())
    vk.messages.send(user_id=uid,
                     message='Прочтите, пожалуйста, инструкцию к боту в закрепленных сообщениях группы',
                     random_id=get_random_id())
    menu(vk, uid)


def menu(vk, uid):
    users_data[uid]['state'] = 2
    keyboard = generate_keyboard(2)
    vk.messages.send(user_id=uid,
                     message='Меню', keyboard=keyboard.get_keyboard(),
                     random_id=get_random_id())


def show_news(vk, uid):
    news = parse_news()
    keyboard = generate_keyboard(2)
    for x in news:
        vk.messages.send(user_id=uid,
                         message='\n'.join(x), keyboard=keyboard.get_keyboard(),
                         random_id=get_random_id())


def show_rules(vk, uid):
    vk.messages.send(user_id=uid, message=RULES,
                     random_id=get_random_id(), keyboard=generate_keyboard_rules().get_keyboard())


def show_map(vk, uid):
    b = {'contact_with_people': {True: 1, False: 0},
         'abroad': {True: 1, False: 0},
         'people_with_corona': {True: 1, False: 0},
         'do_user_know_about': {True: 0, False: 1},
         'self_isolatioon': {True: 0, False: 1}}
    session = db_session.create_session()
    ball = [b['contact_with_people'][t.contact_with_people] +
            b['abroad'][t.abroad] +
            b['people_with_corona'][t.people_with_corona] +
            b['do_user_know_about'][t.do_user_know_about] +
            b['self_isolatioon'][t.self_isolatioon] +
            (t.temperature / 36.6) for t in session.query(Indicators).all()]
    people_add = [t.address for t in session.query(Indicators).all()]
    p = list(zip(ball, people_add))
    params = []
    for x in p:
        if x[0] > 4:
            params.append(get_ll_span(x[1])[0] + ',pmrdl' + str(int(x[0])))
        else:
            params.append(get_ll_span(x[1])[0] + ',pmwtl' + str(int(x[0])))
    params = '~'.join(params)
    show_maps('Россия, Саратов', add_params=params)
    upload = vk_api.VkUpload(vk)
    photo = upload.photo_messages('static/img/map.png')
    owner_id = photo[0]['owner_id']
    photo_id = photo[0]['id']
    access_key = photo[0]['access_key']
    attachment = f'photo{owner_id}_{photo_id}_{access_key}'
    vk.messages.send(user_id=uid, random_id=get_random_id(), attachment=attachment,
                     keyboard=generate_keyboard(2).get_keyboard())


def main():
    global name, surname
    longpoll = VkBotLongPoll(vk_session, GROUP_ID)
    for event in longpoll.listen():
        if event.type == VkBotEventType.MESSAGE_NEW:
            vk = vk_session.get_api()
            uid = event.message.from_id
            response = vk.users.get(user_id=uid)
            users_data[uid] = users_data.get(uid, dict())
            user = vk.users.get(user_ids=uid, fields=['city'])[0]
            name, surname = user["first_name"], user["last_name"]
            try:
                if 'state' not in users_data[uid]:
                    new_user(response, vk, uid)
                    users_data[uid]['quest'] = iter(QUESTIONS)
                elif event.message.text.lower() in ['меню', 'вернуться в меню']:
                    menu(vk, uid)
                elif users_data[uid]['state'] == 2:
                    if event.message.text.lower() == 'карта':
                        show_map(vk, uid)
                    elif event.message.text.lower() == 'заполнить анкету':
                        send_next(vk, uid)
                    elif event.message.text.lower() == 'правила при эпидемии':
                        show_rules(vk, uid)
                    elif event.message.text.lower() == 'новости о коронавирусе':
                        show_news(vk, uid)
                    elif event.message.text:
                        answer_checking(vk, uid, event.message)
                    else:
                        raise MessageError
                else:
                    raise MessageError
            except MessageError:
                keyboard = generate_keyboard(users_data[uid])
                vk.messages.send(user_id=uid, message='Попробуйте еще раз',
                                 random_id=get_random_id(), keyboard=keyboard.get_keyboard())


if __name__ == '__main__':
    main()
