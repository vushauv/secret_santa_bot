import telebot 
import buttons

# kb_welcome = types.InlineKeyboardMarkup(row_width=2)
# key_registration = types.InlineKeyboardButton(text='Рэгістрацыя', callback_data='registration')
# key_write_admin = types.InlineKeyboardButton(text='Сувязь', callback_data='write_admin')
# kb_welcome.add(key_registration, key_write_admin)





welcome_unregistered = telebot.types.ReplyKeyboardMarkup(True)
welcome_unregistered.row(buttons.registration, buttons.get_help)

welcome_unfinished_registration = telebot.types.ReplyKeyboardMarkup(True)
welcome_unfinished_registration.row(buttons.registration_unfinished, buttons.get_help)

finished_registration_waiting_for_santa = telebot.types.ReplyKeyboardMarkup(True)
finished_registration_waiting_for_santa.row(buttons.stop_patcipating, buttons.get_help)

welcome_finished_registration_doesnot_participate = telebot.types.ReplyKeyboardMarkup(True)
welcome_finished_registration_doesnot_participate.row(buttons.start_participating, buttons.get_help)

main = telebot.types.ReplyKeyboardMarkup(True)
main.row(buttons.write_to_child, buttons.write_to_santa)
main.row(buttons.get_help)



admin = telebot.types.ReplyKeyboardMarkup(True)
admin.row(buttons.write_to_child, buttons.write_to_santa)
admin.row(buttons.get_help, buttons.verificate)
admin.row("Атрымаць базы")

super_admin = telebot.types.ReplyKeyboardMarkup(True)
super_admin.row(buttons.get_help, buttons.verificate)
super_admin.row(buttons.create_links, buttons.registration)
super_admin.row(buttons.get_database, buttons.get_logs)
super_admin.row(buttons.send_links_to_users)
super_admin.row(buttons.write_to_child, buttons.write_to_santa)
super_admin.row(buttons.stop_patcipating, buttons.start_participating)

cancel = telebot.types.ReplyKeyboardMarkup(True)
cancel.row(buttons.cancel)

communication_with_admin = telebot.types.ReplyKeyboardMarkup(True)
communication_with_admin.row(buttons.cancel)



from telebot import types

def get_kb_for_verification(user_data):
    verification_admin = types.InlineKeyboardMarkup()
    change_name = types.InlineKeyboardButton(text='Змяніць імя🀄️', callback_data='change_name_'+ str(user_data["tg_id"]))
    change_group = types.InlineKeyboardButton(text='Змяніць клас🏳️‍🌈', callback_data='change_group_'+ str(user_data["tg_id"]))
    change_instagram = types.InlineKeyboardButton(text='Змяніць Instagram🌐', callback_data='change_instagram_'+ str(user_data["tg_id"]))
    accept_user = types.InlineKeyboardButton(text='Прыняць заяўку✅', callback_data='accept_'+ str(user_data["tg_id"]))
    decline_user = types.InlineKeyboardButton(text='❌Скасаваць заяўку❌', callback_data='decline_'+ str(user_data["tg_id"]))
    close_session = types.InlineKeyboardButton(text="🔐🔐Закрыць Сэсію🔐🔐",callback_data="close_session")
    verification_admin.add(change_name, change_group)
    verification_admin.add(change_instagram, decline_user)
    verification_admin.add(accept_user)
    verification_admin.add(close_session)
    return verification_admin