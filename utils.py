from telegram import ReplyKeyboardMarkup
from settings import translation

def separation(lst, n):
    return [lst[i:i + n] for i in range(0, len(lst), n)]


def generate_list_list(list):
    list_list = []
    if len(list)>3:
        list_list = separation(list,3)
    else:
        list_list.append(list)
    return list_list


def generate_markup(keyboard):
    list = generate_list_list(keyboard)
    markup = ReplyKeyboardMarkup(list,one_time_keyboard=True,resize_keyboard=True)
    return markup

def generate_message(list_tuple,text):
    message='В наличии:\n\n'
    text = text.split(',')
    for l in list_tuple:
        for i in range(len(l)):
            message = message + translation[text[i]]+' - ' + str(l[i]) + '\n'
        message = message +'\n'
    return message