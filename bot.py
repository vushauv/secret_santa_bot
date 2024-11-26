import telebot
import os
import csv
import os
import random
import time
from loguru import logger

import kb
import buttons
import texts
import db
from config import TOKEN, ADMIN_ID, USERS_COLUMNS_LIST, USERS_STATUS_COLUMNS_LIST, FIELDS_FOR_INPUT, SANTA_CHILD_RELATION_COLUMNS_LIST



# comments
# 1. Тэксты трэба хаваць у jsonе
# 2. Праверыць паралельную рэгістрацы
# 3. Паглядзець правілы афармленьня Python кода (на будучыню)
# 4. Дакладна і для базы, і для карыстальнікаў можна было б круты клас стварыць

logger.add("debug.log", format="{time} {level} {message}", level="INFO", rotation="25 MB")
logger.info("Bot has started")

bot = telebot.TeleBot(TOKEN)
try:
    bot.send_message(ADMIN_ID,"Бот зноў працуе /start")
except:
    pass





@logger.catch
@bot.message_handler(commands=['start'])
def send_welcome(message):
    logger.info(f"User {message.chat.id} clicked /start")
    user = db.get_row_by_column_value("users_status", USERS_STATUS_COLUMNS_LIST, "tg_id", message.chat.id)
    if not len(user):
        # absolutely new user
        logger.info(f"User {message.chat.id} is new for the system")
        db.add_new_row("users", USERS_COLUMNS_LIST,{
            "tg_id": message.chat.id,
            "tg_nickname": message.from_user.username,
            "name_surname" : "",
            "group_name" : "",
            "group_number" : 0,
            "instagram_link" : "",
            })
        db.add_new_row("users_status", USERS_STATUS_COLUMNS_LIST,{
            "tg_id": message.chat.id,
            "admin_status": 0,
            "registration_status" : 0,
            "santa_status": 1, 
            })
        bot.send_message(message.chat.id, texts.welcome_unregistered, parse_mode="HTML", reply_markup=kb.welcome_unregistered)
    
    elif user["registration_status"] == 0:
        # registration is not finished
        logger.info(f"Message was sent to user {message.chat.id}, registration_status = 0")
        bot.send_message(message.chat.id, texts.welcome_unfinished_registration, parse_mode="HTML", reply_markup=choose_reply_markup(message.chat.id))
    elif user["registration_status"] == 1 or user["registration_status"] == 2:
        
        if user["santa_status"] == 1:
            # finished registration and waiting for santa
            logger.info(f"Message was sent to user {message.chat.id}, registration_status = 1, santa_status = 1")
            bot.send_message(message.chat.id, texts.welcome_finished_registration_waiting_for_santa, parse_mode="HTML", reply_markup=choose_reply_markup(message.chat.id))
        
        elif user["santa_status"] == 2:
            # finished registration and has santa
            logger.info(f"Message was sent to user {message.chat.id}, registration_status = 1, santa_status = 2")
            bot.send_message(message.chat.id, texts.welcome_finished_registration_has_santa, parse_mode="HTML", reply_markup=choose_reply_markup(message.chat.id))
        
        elif user["santa_status"] == 0:
            # finished registration and user does not want to participate
            logger.info(f"Message was sent to user {message.chat.id}, registration_status = 1, santa_status = 0")
            bot.send_message(message.chat.id, texts.welcome_finished_registration_doesnot_participate, parse_mode="HTML", reply_markup=choose_reply_markup(message.chat.id))
            

@logger.catch
def is_admin(message):
    logger.info(f"Checking user {message.chat.id} for being admin")
    user = db.get_row_by_column_value("users_status", USERS_STATUS_COLUMNS_LIST, "tg_id", message.chat.id)
    if len(user) == 0 or user["admin_status"] == 0:
        return 0
    else:
        return user["admin_status"]
    

@logger.catch
def choose_reply_markup(id):
    user = db.get_row_by_column_value("users_status", USERS_STATUS_COLUMNS_LIST, "tg_id", id)

    if len(user) == 0:
        return kb.welcome_unregistered
    elif id == ADMIN_ID:
        return kb.super_admin
    elif user["admin_status"] == 1:
        return kb.admin

    if len(user) == 0:
        return kb.welcome_unregistered
    elif user["registration_status"] == 0:
        return kb.welcome_unfinished_registration
    elif user["registration_status"] == 1 or user["registration_status"] == 2:
        if user["santa_status"] == 1:
            return kb.finished_registration_waiting_for_santa
        elif user["santa_status"] == 2:
            return kb.main
        elif user["santa_status"] == 0:
            return kb.welcome_finished_registration_doesnot_participate
        
    logger.warning(f"User {id} has gotten a  keyboard by its conditions")
    return kb.welcome_unregistered



@logger.catch
def get_field_for_insert(fields_for_input, user_data):
    field_for_insert = ""
    for f in fields_for_input:
        if (user_data[f] == ""):
            field_for_insert = f
            break
    return field_for_insert

@logger.catch
def ask_user_for_next_step(message, field):
    logger.info(f"User {message.chat.id} is trying to register and has sent {message.text}")
    if message.text == buttons.cancel:
        bot.send_message(message.chat.id, texts.stop_registration, parse_mode="HTML", reply_markup=choose_reply_markup(message.chat.id))
        return 
    if len(message.text) > 32:
        bot.send_message(message.chat.id, texts.too_long_field, parse_mode="HTML", reply_markup=choose_reply_markup(message.chat.id))
        logger.warning(f"User {message.chat.id} has tried to write too long messsage")
        return 
    logger.info(f"We try to update date for user {message.chat.id}: {field} = {message.text}")
    db.update_row_value_by_column_value("users", "tg_id", message.chat.id, field, message.text)
    logger.info(f"We have updated data successfully for {message.chat.id}")
    bot.send_message(message.chat.id, texts.added_successfully[field])
    logger.info(f"We check either user {message.chat.id} has inserted all fields")
    user_data = db.get_row_by_column_value("users", USERS_COLUMNS_LIST, "tg_id", message.chat.id)
    field_for_insert = get_field_for_insert(FIELDS_FOR_INPUT, user_data)
    if field_for_insert != "":
        logger.info(f"User {message.chat.id} has not inserted {field} so they continue registration process")
        register_user(message)
    else:
        logger.info(f"We try to update registration_status to 1 for user {message.chat.id}")
        db.update_row_value_by_column_value("users_status", "tg_id", message.chat.id, "registration_status", 1)
        logger.info(f"We have updated registration_status successfully for {message.chat.id}")
        bot.send_message(message.chat.id, texts.finished_registration, parse_mode="HTML", reply_markup=choose_reply_markup(message.chat.id))

@logger.catch
def response_for_unknown_message(message):
    logger.warning(f"User {message.chat.id} wrote something that he got that we understood its like unknown message")
    bot.send_message(message.chat.id, texts.unknown_message, parse_mode="HTML",reply_markup=choose_reply_markup(message.chat.id))


@logger.catch
def register_user(message):
    logger.info(f"User {message.chat.id} try to register")
    user = db.get_row_by_column_value("users_status", USERS_STATUS_COLUMNS_LIST, "tg_id", message.chat.id)
    logger.info(f"Data about user{message.chat.id}: {user}")
    if len(user) != 0 and user["registration_status"] != 0:
        bot.send_message(message.chat.id, texts.already_registered, parse_mode="HTML", reply_markup=choose_reply_markup(message.chat.id))
        return
    user_data = db.get_row_by_column_value("users", USERS_COLUMNS_LIST, "tg_id", message.chat.id)
    field_for_insert = get_field_for_insert(FIELDS_FOR_INPUT, user_data)
    logger.info(f"Next field for registration user {message.chat.id} is {field_for_insert}")
    if (field_for_insert == ""):
        logger.error(f"All fields for user {message.chat.id} are not empty but they have 0 registration status")
        bot.send_message(ADMIN_ID, f"<b>ERROR\n\n\n\nAll fields for user {message.chat.id} are not empty but they have 0 registration status</b>", parse_mode="HTML", reply_markup=kb.cancel)
        bot.send_message(message.chat.id, f"Мы ня можам атрымаць вашую заяўку, такое можа здарацца пры празмернай нагрузцы на сервер. Калі ласка звярніцеся да адміністратараў праз кнопку {buttons.get_help}", parse_mode="HTML", reply_markup=kb.cancel)
        return
    bot.send_message(message.chat.id, texts.ask_user[field_for_insert], parse_mode="HTML", reply_markup=kb.cancel)
    bot.register_next_step_handler(message, ask_user_for_next_step, field_for_insert)


@logger.catch
def change_participating_status(message):
    logger.info(f"User {message.chat.id} try to change status")
    user = db.get_row_by_column_value("users_status", USERS_STATUS_COLUMNS_LIST, "tg_id", message.chat.id)
    logger.info(f"Data about user {message.chat.id}: {user}")
    if len(user) == 0 or user["registration_status"] not in [1,2]:
        response_for_unknown_message(message)
        return 
    if user["santa_status"] == 1 and message.text == buttons.stop_patcipating:
            db.update_row_value_by_column_value("users_status", "tg_id", message.chat.id, "santa_status", 0)
            bot.send_message(message.chat.id, texts.status_changed_to_not_participating, parse_mode="HTML", reply_markup=choose_reply_markup(message.chat.id))
    elif user["santa_status"] == 0 and message.text == buttons.start_participating:
        db.update_row_value_by_column_value("users_status", "tg_id", message.chat.id, "santa_status", 1)
        bot.send_message(message.chat.id, texts.status_changed_to_participating, parse_mode="HTML", reply_markup=choose_reply_markup(message.chat.id))
    elif user["santa_status"] == 2:
        bot.send_message(message.chat.id, texts.you_cannot_change_status, reply_markup=choose_reply_markup(message.chat.id))
    else:
        participating_status = "Ня вызначаны (звярніцеся да адміністратараў)"
        if user["santa_status"] == 1:
            participating_status = "Удзельнік"
        elif user["santa_status"] == 0:
            participating_status = "Адмова ад удзелу"
        bot.send_message(message.chat.id, f"У нас узніклі складанасці са зменай вашага статуса. Зазавычай гэта выклікана празмернай нагрузкай на сервер або калі вы даслалі зашмат запытаў. Калі ласка, паспрабуйце пазней або звярніце па дапамогу праз кнопку {buttons.get_help}\n\n<i>На дадзены момант ваш статус: <u>{participating_status}</u></i>", parse_mode="HTML",reply_markup=choose_reply_markup(message.chat.id))
        logger.warning(f"User {message.chat.id} tried to change status and something went wrong, user_participating_status = {participating_status}")

@logger.catch
def get_user_card_for_admin(user_data):
    instagram_link = "Не дададзены"
    if user_data["instagram_link"] != "-":
        instagram_link = f"<a href='https://www.instagram.com/{user_data['instagram_link']}/'>{user_data['instagram_link']}</a>"
    return f"<b>Верыфікацыя чалавека:</b>\n\n<i>Тэхнічная інфармацыя:</i>\ntg_id: <code>{user_data['tg_id']}</code>\ntg_nickname: @{user_data['tg_nickname']}\n\n<i>Бачная інфармацыя:</i>\nІмя: {user_data['name_surname']}\nКлас: {user_data['group_name']}\nInstagram: {instagram_link}"


@logger.catch
def verificate_users(message):
    if is_admin(message) == 0:
        bot.send_message(message.chat.id, texts.unknown_message, parse_mode="HTML", reply_markup=choose_reply_markup(message.chat.id))
    users = db.get_rows_by_column_value("users_status", USERS_STATUS_COLUMNS_LIST, "registration_status", 1)
    number_of_waiting = f"На дадзены момант чакаюць верыфікацыі {len(users)} чалавек(і)"
    if len(users) == 0:
        bot.send_message(message.chat.id, number_of_waiting)
    if (len(users) != 0):
        user_data = db.get_row_by_column_value("users", USERS_COLUMNS_LIST, "tg_id", users[0]["tg_id"])
        logger.info(f"admin {message.from_user.username} checks card of {users[0]['tg_id']}")
        bot.send_message(message.chat.id, f"<b>{number_of_waiting}</b>\n\n\n" + get_user_card_for_admin(user_data), parse_mode="HTML", reply_markup=kb.get_kb_for_verification(user_data))

@logger.catch
def write_message_from_to_handler(message, recipient_id, recipient_type):
    logger.info(f"User {message.chat.id} try to send {message.text} to {recipient_id}, recipient_type = {recipient_type}")
    if message.text == buttons.cancel:
        if recipient_type == "admin":
            bot.send_message(message.chat.id, texts.donot_write_to["admin"], parse_mode="HTML", reply_markup=choose_reply_markup(message.chat.id))
        else:
            bot.send_message(message.chat.id, texts.donot_write_to_basic, parse_mode="HTML", reply_markup=choose_reply_markup(message.chat.id))
        return
    if recipient_type == "admin":
        admins = db.get_rows_by_column_value("users_status", USERS_STATUS_COLUMNS_LIST, "admin_status", 1)
        if len(admins) == 0:
            bot.send_message(message.chat.id, texts.error_you_wrote_message_to["admin"], parse_mode="HTML", reply_markup=choose_reply_markup(message.chat.id))
            bot.send_message(ADMIN_ID, "АДМІНАЎ НЯМА, А ЧАЛАВЕК ШТОСЬЦІ НАПІСАЎ", reply_markup=choose_reply_markup(ADMIN_ID))
        for admin in admins:
            try:
                bot.send_message(admin["tg_id"], f"<b>QUESTION FROM {message.chat.id}</b>", parse_mode="HTML", reply_markup=choose_reply_markup(admin["tg_id"]))
                m = bot.forward_message(admin["tg_id"], message.chat.id, message.id)
                bot.reply_to(m, f"Command for communication:\n/write_to_{message.chat.id}", parse_mode="HTML", reply_markup=choose_reply_markup(admin["tg_id"]))
                bot.send_message(message.chat.id, texts.you_request_has_been_received, parse_mode="HTML", reply_markup=choose_reply_markup(message.chat.id))
            except:
                logger.error(f"User {message.chat.id} tried to write to {admin['tg_id']} but it lead to error")
                bot.send_message(message.chat.id, texts.error_you_wrote_message_to["admin"], parse_mode="HTML", reply_markup=choose_reply_markup(message.chat.id))
    else:
        try:
            bot.send_message(recipient_id, texts.you_got_message_you_are[recipient_type], parse_mode="HTML", reply_markup=choose_reply_markup(recipient_id))
            bot.copy_message(recipient_id, message.chat.id, message.id)
            bot.send_message(message.chat.id, texts.you_wrote_message_to[recipient_type], parse_mode="HTML", reply_markup=choose_reply_markup(message.chat.id))
        except:
            logger.warning(f"User {message.chat.id} tried to write to {recipient_id} it leaded to Exception")
            bot.send_message(message.chat.id, texts.error_you_wrote_message_to[recipient_type], parse_mode="HTML", reply_markup=choose_reply_markup(message.chat.id))
            admins = db.get_rows_by_column_value("users_status", USERS_STATUS_COLUMNS_LIST, "admin_status", 1)
            for admin in admins:
                try:
                    bot.send_message(admin["tg_id"], f"<b>!!!PROBLEM!!!</b>\n\n\n{message.chat.id} спрабаваў напісаць {recipient_id}, але штосьці пайшло ня так. Найбольш верагодна тое, што другі адлучыўся ад бота.", parse_mode="HTML")
                except:
                    logger.error(f"User {message.chat.id} tried to write to {recipient_id}, it leaded to mistake but {admin['tg_id']} also has difficulties with getting message")


@logger.catch                    
def write_message_from_to(message, recipient_id, recipient_type):
    bot.send_message(message.chat.id, texts.write_message_to[recipient_type], parse_mode="HTML", reply_markup=kb.cancel)
    bot.register_next_step_handler(message, write_message_from_to_handler, recipient_id, recipient_type)

@logger.catch
def send_file(message, file_name, data, columns_list):
    logger.info("Creating file")
    with open(file_name, "w", encoding="UTF-8") as f:
        csvwriter = csv.writer(f)  
        csvwriter.writerow(columns_list)  
        for row in data:
            list_for_writing = []
            for key in row:
                list_for_writing.append(row[key])
            csvwriter.writerow(list_for_writing)
    f = open(file_name, "r", encoding="UTF-8")
    bot.send_document(message.chat.id, f)
    os.remove(file_name)

@logger.catch
def create_links(message):
    if message.chat.id != ADMIN_ID:
        logger.warning(f"User {message.chat.id} tried to create links without such permission")
        response_for_unknown_message(message)
    else:
        participating_users = db.get_rows_by_column_value("users_status", USERS_STATUS_COLUMNS_LIST, "santa_status", 1)
        send_file(message, "users_for_links.csv", participating_users, USERS_STATUS_COLUMNS_LIST)
        if (len(participating_users) < 3):
            bot.send_message(message.chat.id, "Людзей замала", reply_markup=choose_reply_markup(message.chat.id))
            return
        random.shuffle(participating_users)
        santa_child_relation = []
        for i in range(1, len(participating_users)-1):
            user_dict = dict()
            user_dict["tg_id"] =  participating_users[i]["tg_id"]
            user_dict["your_santa_id"] = participating_users[i-1]["tg_id"]
            user_dict["your_child_id"] = participating_users[i+1]["tg_id"]
            user_dict["was_sent"] = 0
            santa_child_relation.append(user_dict)

        santa_child_relation.append({
            "tg_id" : participating_users[0]["tg_id"],
            "your_santa_id" : participating_users[-1]["tg_id"],
            "your_child_id" : participating_users[1]["tg_id"],
            "was_sent" : 0,
        })
        santa_child_relation.append({
            "tg_id" : participating_users[-1]["tg_id"],
            "your_santa_id" : participating_users[-2]["tg_id"],
            "your_child_id" : participating_users[0]["tg_id"],
            "was_sent" : 0,
        })

        send_file(message, "links.csv", santa_child_relation, SANTA_CHILD_RELATION_COLUMNS_LIST)
        for relation in santa_child_relation:
            try:
                db.add_new_row("santa_child_relation", SANTA_CHILD_RELATION_COLUMNS_LIST, relation)
            except:
                bot.send_message(message.chat.id, f"Праблема з дадаваннем у спіс удзельніка:\n\n {relation}")
                continue
            try:
                db.update_row_value_by_column_value("users_status", "tg_id", relation["tg_id"], "santa_status", 2)
            except:
                bot.send_message(message.chat.id, f"Праблема з абнаўленнем даных у ўдзельніка:\n\n {relation}")
        bot.send_message(message.chat.id, "Спіс дададзены ў БД", reply_markup=choose_reply_markup(message.chat.id))
        


@logger.catch
def write_to_all(message):
    logger.info(f"User {message.chat.id} tried to write to all message = {message.text}")
    if message.text == buttons.cancel:
        bot.send_message(message.chat.id, "Дасыланне скасаванае", parse_mode="HTML", reply_markup=choose_reply_markup(message.chat.id))
        return
    # send_to_all_message
        


@logger.catch
def get_database(message):
    logger.info(f"User {message.chat.id} tried to get data_bases")
    if is_admin(message) != 1:
        logger.warning(f"User {message.chat.id} tried to get data_bases but they do not have such permission")
        response_for_unknown_message(message)
    else:
        tables = ["users", "users_status", "santa_child_relation"]
        columns = [USERS_COLUMNS_LIST, USERS_STATUS_COLUMNS_LIST, SANTA_CHILD_RELATION_COLUMNS_LIST]
        for i in range(len(tables)):
            data = db.get_all_rows(tables[i], columns[i])
            send_file(message, tables[i] + ".csv", data, columns[i])

@logger.catch
def add_admin(message, id):
    logger.info(f"User {message.chat.id} tried to add admin to {id}")
    if message.chat.id != ADMIN_ID:
        logger.warning(f"User {message.chat.id} tried to add admin to {id}, but they do not have such permision")
        response_for_unknown_message(message)
    else:
        user = db.get_row_by_column_value("users_status", USERS_STATUS_COLUMNS_LIST, "tg_id", id)
        if len(user) == 0:
            bot.send_message(ADMIN_ID, "Вы даеце адмінку таму, каго няма", reply_markup=choose_reply_markup(ADMIN_ID))
            return
        try:
            db.update_row_value_by_column_value("users_status", "tg_id", id, "admin_status", 1)
            bot.send_message(ADMIN_ID, "Адмінку далі", reply_markup=choose_reply_markup(ADMIN_ID))
        except:
            bot.send_message(ADMIN_ID, "Адмінку НЕ АТРЫМАЛАСЯ даць", reply_markup=choose_reply_markup(ADMIN_ID))
@logger.catch
def create_user_card_for_user(user_data):
    instagram_link = "не дададзены"
    if user_data["instagram_link"] != '-':
        instagram_link = f"<a href='https://www.instagram.com/{user_data['instagram_link']}'>{user_data['instagram_link']}</a>"
    str = "<b><u>Даныя твайго Атрымальніка:</u></b>\n\n"
    str += f"Яго клічуць: <i>{user_data['name_surname']}</i>\n"
    str += f"Ягоны клас: <i>{user_data['group_name']}</i>\n"
    str += f"Ягоны Instagram <i>{instagram_link}</i>\n\n"
    str += f"<i>Нагадваем, што вы можаце напісаць і свайму Санце, і Атрымальніку націснуўны або даслаўшы <code>{buttons.write_to_santa}</code> і <code>{buttons.write_to_child}</code></i>"
    return str

@logger.catch
def send_notifications(message):
    users = db.get_rows_by_column_value("santa_child_relation", SANTA_CHILD_RELATION_COLUMNS_LIST, "was_sent", 0)
    print(users)
    for user in users:
        print()
        print("user data:",user)
        print()
        try:
            child_data = db.get_row_by_column_value("users", USERS_COLUMNS_LIST, "tg_id", user["your_child_id"])
            bot.send_message(user["tg_id"], texts.you_got_santa_and_child, parse_mode="HTML")
            print("child data:",child_data)
            print(create_user_card_for_user(child_data))
            bot.send_message(user["tg_id"], create_user_card_for_user(child_data), parse_mode="HTML", reply_markup=choose_reply_markup(user["tg_id"]))
            try:
                db.update_row_value_by_column_value("santa_child_relation", "tg_id", user["tg_id"], "was_sent", 1)
            except:
                bot.send_message(ADMIN_ID, "PROBLEM 2")
                logger.error(f"Bot tried to change was_sent to 1 for {user['tg_id']} but it raised an exception.")
        except:
            bot.send_message(ADMIN_ID, f"Паведамленне пра тое, што ў чалавека з'явіўся Санта не дайшло да {user['tg_id']}")
            logger.warning(f"Паведамленне пра тое, што ў чалавека з'явіўся Санта не дайшло да {user['tg_id']}")
        time.sleep(0.5)
        
@logger.catch
@bot.message_handler(content_types= ['text'])
def work_with_chat(message):
    logger.info(f"Bot got message from {message.chat.id}, {message.from_user.username} equals to {message.text}")
    if (message.text[0] == '/'):
        if message.text == "write_to_all":
            if is_admin(message.chat.id):
                bot.send_message(message.chat.id, "Вашае наступнае паведамленне будзе перасланае ўсім карыстальнікам. Дашліце /cancel, каб скасаваць дасыланне.")
                bot.register_next_step_handler(write_to_all, message)
        elif message.text[0:9] == "/write_to":
            write_message_from_to(message, int(message.text[10::]),"user")
        elif message.text[0:10] == "/add_admin":
            add_admin(message, int(message.text[11::]))
    else:
        match message.text:
            case buttons.get_help:
                write_message_from_to(message, 0, "admin")
            case buttons.registration:
                register_user(message)
            case buttons.registration_unfinished:
                register_user(message)
            case buttons.start_participating:
                change_participating_status(message)
            case buttons.stop_patcipating:
                change_participating_status(message)
            case buttons.verificate:
                verificate_users(message)
            case buttons.create_links:
                create_links(message)
            case buttons.get_database:
                get_database(message)
            case buttons.send_links_to_users:
                send_notifications(message)
            case buttons.write_to_child:
                your_child = db.get_row_by_column_value("santa_child_relation", SANTA_CHILD_RELATION_COLUMNS_LIST, "tg_id", message.chat.id)
                if len(your_child) == 0:
                    bot.send_message(message.chat.id, "У вас няма атрымальніка, каб яму напісаць.")
                else:
                    write_message_from_to(message, your_child["your_child_id"],"child")
            case buttons.write_to_santa:
                your_santa = db.get_row_by_column_value("santa_child_relation", SANTA_CHILD_RELATION_COLUMNS_LIST, "tg_id", message.chat.id)
                if len(your_santa) == 0:
                    bot.send_message(message.chat.id, "У вас няма атрымальніка, каб яму напісаць.")
                else:
                    write_message_from_to(message, your_santa["your_santa_id"],"santa")
            case _:
                response_for_unknown_message(message)            






@logger.catch
def change_field_to_call_value(message, message_id, id ,table_name,field_name):
    logger.info(f"User {message.chat.id} tries to change value for {id}")
    if message.text == "/cancel":
        user_data = db.get_row_by_column_value("users", USERS_COLUMNS_LIST, "tg_id", id)
        bot.edit_message_text(chat_id=message.chat.id, message_id=message_id, text=get_user_card_for_admin(user_data), parse_mode="HTML", reply_markup=kb.get_kb_for_verification(user_data))
        bot.delete_message(message.chat.id,message_id=message.id)
    else:
        user = db.get_row_by_column_value("users_status", USERS_STATUS_COLUMNS_LIST, "tg_id", id)
        if user["registration_status"] == 1:
            db.update_row_value_by_column_value(table_name, "tg_id", id, field_name, message.text)
            user_data = db.get_row_by_column_value("users", USERS_COLUMNS_LIST, "tg_id", id)
            bot.edit_message_text(chat_id=message.chat.id, message_id=message_id, text=get_user_card_for_admin(user_data), parse_mode="HTML", reply_markup=kb.get_kb_for_verification(user_data))
            bot.delete_message(message.chat.id,message_id=message.id)
        else:
            bot.delete_message(message.chat.id,message_id=message_id)
            bot.send_message(chat_id=message.chat.id, text="<b>ВЫ СПРАБУЕЦЕ ЗМЯНІЦЬ ДАНЫЯ Ў ЧАЛАВЕКА, ЯКІ ЎЖО БЫЎ ВЕРЫФІКАВАНЫ</b>", parse_mode="HTML", reply_markup=choose_reply_markup(message.chat.id))





@logger.catch
@bot.callback_query_handler(func=lambda call: True)
def callback_worker(call): 
    logger.info(f"Bot got callback_query from {call.message.chat.id}, call =  {call.data}")
    if call.data[0:11] == "change_name":
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id, text="Увядзіце новае імя (або /cancel)", parse_mode="HTML")
        bot.register_next_step_handler(call.message, change_field_to_call_value, call.message.id, int(call.data[12::]),"users","name_surname")
    elif call.data[0:12] == "change_group":
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id, text="Увядзіце новы клас (або /cancel)", parse_mode="HTML")
        bot.register_next_step_handler(call.message, change_field_to_call_value, call.message.id, int(call.data[13::]),"users","group_name")
    elif call.data[0:16] == "change_instagram":
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id, text="Увядзіце новы Instagram (або /cancel)", parse_mode="HTML")
        bot.register_next_step_handler(call.message, change_field_to_call_value, call.message.id, int(call.data[17::]),"users","instagram_link")
    elif call.data[0:6] == "accept":
        db.update_row_value_by_column_value("users_status", "tg_id", int(call.data[7::]), "registration_status", 2)
        user = db.get_row_by_column_value("users_status", USERS_STATUS_COLUMNS_LIST, "tg_id", int(call.data[7::]))
        if user["santa_status"] == 0:
            try:
                bot.send_message(int(call.data[7::]), texts.verified_successfully_doesnot_participate, parse_mode="HTML", reply_markup=choose_reply_markup(int(call.data[7::])))
            except:
                logger.warning(f"Карыстальнік {int(call.data[7::])} ВЫЙШАЎ З БОТА, АЛЕ ЯГОНАЯ ЗАЯЎКА ВЕРЫФІКАВАНАЯ ЗВЯРТАЙСЯ ДА ВАСІЛЯ")
                db.update_row_value_by_column_value("users_status", "tg_id", int(call.data[7::]), "registration_status", 0)
                db.update_row_value_by_column_value("users", "tg_id", int(call.data[7::]), "name_surname", "")
                db.update_row_value_by_column_value("users", "tg_id", int(call.data[7::]), "group_name", "")
                db.update_row_value_by_column_value("users", "tg_id", int(call.data[7::]), "instagram_link", None)
                # Люты кастыль!!!
                bot.send_message(call.message.chat.id, "Карыстальнік ВЫЙШАЎ З БОТА, АЛЕ ЯГОНАЯ ЗАЯЎКА ВЕРЫФІКАВАНАЯ ЗВЯРТАЙСЯ ДА ВАСІЛЯ")
        elif user["santa_status"] == 1:
            try:
                logger.warning(f"Карыстальнік {int(call.data[7::])} ВЫЙШАЎ З БОТА, АЛЕ ЯГОНАЯ ЗАЯЎКА ВЕРЫФІКАВАНАЯ ЗВЯРТАЙСЯ ДА ВАСІЛЯ")
                db.update_row_value_by_column_value("users_status", "tg_id", int(call.data[7::]), "registration_status", 0)
                bot.send_message(int(call.data[7::]), texts.verified_successfully_participant, parse_mode="HTML", reply_markup=choose_reply_markup(int(call.data[7::])))
            except:
                logger.warning(f"Карыстальнік {int(call.data[7::])} ВЫЙШАЎ З БОТА, АЛЕ ЯГОНАЯ ЗАЯЎКА ВЕРЫФІКАВАНАЯ ЗВЯРТАЙСЯ ДА ВАСІЛЯ")
                db.update_row_value_by_column_value("users_status", "tg_id", int(call.data[7::]), "registration_status", 0)
                db.update_row_value_by_column_value("users", "tg_id", int(call.data[7::]), "name_surname", "")
                db.update_row_value_by_column_value("users", "tg_id", int(call.data[7::]), "group_name", "")
                db.update_row_value_by_column_value("users", "tg_id", int(call.data[7::]), "instagram_link", None)
                # Люты кастыль!!!
                bot.send_message(call.message.chat.id, "Карыстальнік ВЫЙШАЎ З БОТА, АЛЕ ЯГОНАЯ ЗАЯЎКА ВЕРЫФІКАВАНАЯ ЗВЯРТАЙСЯ ДА ВАСІЛСЯ")
        bot.delete_message(call.message.chat.id,message_id=call.message.id)
        bot.send_message(call.message.chat.id, f"User <code>{call.data[7::]}</code> was verified successfully", parse_mode="HTML")
        verificate_users(call.message)

    elif call.data[0:7] == "decline":
        db.update_row_value_by_column_value("users_status", "tg_id", int(call.data[8::]), "registration_status", -1)
        bot.send_message(int(call.data[8::]), texts.verified_unsuccessfully, parse_mode="HTML", reply_markup=choose_reply_markup(int(call.data[8::])))
        bot.delete_message(call.message.chat.id,message_id=call.message.id)
        bot.send_message(call.message.chat.id, f"User <code>{call.data[8::]}</code> was <b>NOT VERIFIED SUCCESSFULLY</b>", parse_mode="HTML")
        verificate_users(call.message)
    elif call.data == "close_session":
        bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.id)



bot.polling()  