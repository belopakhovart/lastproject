import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from vk_api.utils import get_random_id
from data import db_session
from data.users import User
from data.indicators import Indicators
from Artem.data.mapapi import *


from config import TOKEN_VK, GROUP_ID

db_session.global_init("db/info.sqlite")
session = db_session.create_session()

users_data = {}

answers = {'Да': True, 'Нет': False}

RULES = '''Основные меры предосторожности для защиты от новой коронавирусной инфекции
Следите за новейшей информацией о вспышке COVID-19, которую можно найти на веб-сайте ВОЗ, а также получить от органов общественного здравоохранения вашей страны и населенного пункта. Наибольшее число случаев COVID-19 по-прежнему выявлено в Китае, тогда как в других странах отмечаются вспышки локального характера. В большинстве случаев заболевание характеризуется легким течением и заканчивается выздоровлением, хотя встречаются осложнения. Защитить свое здоровье и здоровье окружающих можно, соблюдая следующие правила: 
1. Регулярно мойте руки
Регулярно обрабатывайте руки спиртосодержащим средством или мойте их с мылом. 
Зачем это нужно?  Если на поверхности рук присутствует вирус, то обработка рук спиртосодержащим средством или мытье их с мылом убьет его.
2. Соблюдайте дистанцию в общественных местах
Держитесь от людей на расстоянии как минимум 1 метра, особенно если у них кашель, насморк и повышенная температура.
Зачем это нужно? Кашляя или чихая, человек, болеющий респираторной инфекцией, такой как 2019-nCoV, распространяет вокруг себя мельчайшие капли, содержащие вирус. Если вы находитесь слишком близко к такому человеку, то можете заразиться вирусом при вдыхании воздуха.
3. По возможности, не трогайте руками глаза, нос и рот
Зачем это нужно? Руки касаются многих поверхностей, на которых может присутствовать вирус. Прикасаясь содержащими инфекцию руками к глазам, носу или рту, можно перенести вирус с кожи рук в организм.
4. Соблюдайте правила респираторной гигиены
При кашле и чихании прикрывайте рот и нос салфеткой или сгибом локтя; сразу выкидывайте салфетку в контейнер для мусора с крышкой и обрабатывайте руки спиртосодержащим антисептиком или мойте их водой с мылом.
Зачем это нужно? Прикрывание рта и носа при кашле и чихании позволяет предотвратить распространение вирусов и других болезнетворных микроорганизмов. Если при кашле или чихании прикрывать нос и рот рукой, микробы могут попасть на ваши руки, а затем на предметы или людей, к которым вы прикасаетесь.
5. При повышении температуры, появлении кашля и затруднении дыхания как можно быстрее обращайтесь за медицинской помощью
Если вы посещали районы Китая, где регистрируется 2019-nCoV, или тесно общались с кем-то, у кого после поездки из Китая наблюдаются симптомы респираторного заболевания, сообщите об этом медицинскому работнику.
Зачем это нужно? Повышение температуры, кашель и затруднение дыхания требуют незамедлительного обращения за медицинской помощью, поскольку могут быть вызваны респираторной инфекцией или другим серьезным заболеванием. Симптомы поражения органов дыхания в сочетании с повышением температуры могут иметь самые различные причины, среди которых в зависимости от совершенных пациентом поездок и его контактов может быть 2019-nCoV.'''

QUESTIONS = [('Какая у Вас температура?', 0),
             ('Часто ли Вы контактируете с людьми?', 1),
             ('Были ли Вы заграницей недавно?', 1),
             ('Контактировали с заболевшими?', 1),
             ('Знаете ли вы о правилах в период эпидемии?', 1),
             ('Соблюдаете ли Вы самоизоляцию?', 1),
             ('Ваш адрес', 0),
             ('Узнать результат?', 2)]


class MessageError(Exception):
    pass


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
        keyboard.add_line()
        keyboard.add_button('Правила при эпидемии', color=VkKeyboardColor.PRIMARY)
    else:
        keyboard.add_button('Вернуться в меню', color=VkKeyboardColor.NEGATIVE)
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
    users_answer = msg.text
    if users_answer == 'Мой результат':
        vk.messages.send(user_id=uid, random_id=get_random_id(),
                         message=' '.join(list(map(str, users_data[uid]['answers']))), keyboard=generate_keyboard(2).get_keyboard())
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
    menu(vk, uid)


def menu(vk, uid):
    users_data[uid]['state'] = 2
    keyboard = generate_keyboard(2)
    vk.messages.send(user_id=uid,
                     message='Меню', keyboard=keyboard.get_keyboard(),
                     random_id=get_random_id())


def show_rules(vk, uid):
    vk.messages.send(user_id=uid, message=RULES,
                     random_id=get_random_id(), keyboard=generate_keyboard(2).get_keyboard())


def show_map(vk, uid):
    params = ''
    session = db_session.create_session()
    people = [t.address for t in session.query(Indicators).all()]
    for x in people:
        params += 'pmwtm' + get_ll_span(x)[0] + '&'
    show_maps('Россия, Саратов', add_params=params)
    upload = vk_api.VkUpload(vk)
    photo = upload.photo_messages('static/img/map.png')
    owner_id = photo[0]['owner_id']
    photo_id = photo[0]['id']
    access_key = photo[0]['access_key']
    attachment = f'photo{owner_id}_{photo_id}_{access_key}'
    vk.messages.send(user_id=uid, random_id=get_random_id(), attachment=attachment, keyboard=generate_keyboard(2).get_keyboard())


def main():
    vk_session = vk_api.VkApi(token=TOKEN_VK)
    longpoll = VkBotLongPoll(vk_session, GROUP_ID)
    for event in longpoll.listen():
        if event.type == VkBotEventType.MESSAGE_NEW:
            vk = vk_session.get_api()
            uid = event.message.from_id
            response = vk.users.get(user_id=uid)
            users_data[uid] = users_data.get(uid, dict())
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
