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

vk_session = vk_api.VkApi(token=TOKEN_VK)

RULES = '''СИДИДОМАБЛЯТЬ'''

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
    session = db_session.create_session()
    if users_answer == 'Мой результат':
        vk.messages.send(user_id=uid, random_id=get_random_id(),
                         message=' '.join(list(map(str, users_data[uid]['answers']))),
                         keyboard=generate_keyboard(2).get_keyboard())
        ind = Indicators()
        ind.user =
        ind.temperature = users_data[uid]['answers'][0]
        ind.contact_with_people = users_data[uid]['answers'][1]
        ind.abroad = users_data[uid]['answers'][2]
        ind.people_with_corona = users_data[uid]['answers'][3]
        ind.do_user_know_about = users_data[uid]['answers'][4]
        ind.self_isolatioon = users_data[uid]['answers'][5]
        ind.address = users_data[uid]['answers'][6]
        session.add(ind)
        session.commit()
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
    vk.messages.send(user_id=uid, random_id=get_random_id(), attachment=attachment,
                     keyboard=generate_keyboard(2).get_keyboard())


def main():
    longpoll = VkBotLongPoll(vk_session, GROUP_ID)
    for event in longpoll.listen():
        name, surname = vk_session.method('users.get',{'user_ids': event.obj.message['from_id']})[0]['first_name'], vk_session.method('users.get',{'user_ids': event.obj.message['from_id']})[0]['last_name']

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
