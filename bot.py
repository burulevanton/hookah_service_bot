from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, RegexHandler, ConversationHandler,CallbackQueryHandler
from telegram import ReplyKeyboardRemove,ReplyKeyboardMarkup,InlineKeyboardMarkup,InlineKeyboardButton
import settings
import sql_handler
import utils
import order_calc
from decimal import *
from order_calc import TempShelve
import telebot

CATEGORIES, PRODUCT, SUBPRODUCT,SETWEIGHT, COUNT, CHECK  = range(6)
bot = telebot.TeleBot(token=settings.token)
kek = 'lol'

def start(bot,update):
    message = 'Здравствуйте, вас приветствует бот HookahService Челябинск\n' \
              'vk.com/hookahservice01\n' \
              'Напишите /price, чтобы увидеть цену продукта\n'
    bot.sendMessage(chat_id = update.message.chat_id, text = message)


def helper(bot,update):
    message = '/price - цена определенного продукта\n' \
              '/cancel - отменить выбор и начать заново'
    bot.sendMessage(chat_id = update.message.chat_id, text = message)


def price(bot, update):
    db = sql_handler.SqlHadler()
    markup = utils.generate_markup(db.get_categories())
    bot.sendMessage(chat_id=update.message.chat_id, text="Выберите категорию",reply_markup=markup)
    db.close()
    return CATEGORIES


def category(bot,update):
    db = sql_handler.SqlHadler()
    markup = utils.generate_markup(db.get_assortment(update.message.text))
    bot.sendMessage(chat_id = update.message.chat_id, text = "Выберите необходимого производителя",reply_markup = markup)
    db.close()
    return PRODUCT


def product(bot, update):
    db = sql_handler.SqlHadler()
    text = update.message.text
    text = utils.generate_message(db.get_product_info(text))
    markup = ReplyKeyboardRemove()
    bot.sendMessage(chat_id = update.message.chat_id,text = text,reply_markup = markup)
    db.close()
    return ConversationHandler.END


def cancel(bot,update):
    message = 'Отмена...\n' \
              'Чтобы начать заново, напишите /price'
    bot.sendMessage(chat_id = update.message.chat_id,text = message, reply_markup = ReplyKeyboardRemove())
    return ConversationHandler.END


def get_order_keyboard_and_message(chat_id):
    message = temp_shelve.order_info(chat_id)
    db = sql_handler.SqlHadler()
    if not message:
        message = 'Калькулятор заказов\n' \
                  'Выберите категорию'
        markup = utils.generate_markup(db.get_categories())
    else:
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(telebot.types.InlineKeyboardButton('Оформить заказ', callback_data='execute_order'),
                   telebot.types.InlineKeyboardButton('Удалить некоторые товары', callback_data='delete_order_product'))
        markup.add(telebot.types.InlineKeyboardButton('Удалить заказ', callback_data='delete_order'))
        markup.add(telebot.types.InlineKeyboardButton('Продолжить выбор товаров', callback_data='continue'))
    db.close()
    return message,markup


@bot.message_handler(commands=['order'])
def order(message):
    text,markup = get_order_keyboard_and_message(message.chat.id)
    bot.send_message(chat_id=message.chat.id,text = text,reply_markup=markup)


@bot.message_handler(func=lambda mess: mess.text in sql_handler.SqlHadler().get_categories() and kek =='lol',content_types=['text'])
def order_categories(message):
    db = sql_handler.SqlHadler()
    markup = utils.generate_markup(db.get_assortment(message.text))
    db.close()
    bot.send_message(chat_id=message.chat.id,text = 'Выберите необходимого производителя',reply_markup=markup)

@bot.message_handler(func = lambda mess:mess.text in sql_handler.SqlHadler().get_full_assortment(),content_types=['text'])
def order_product(message):
    db = sql_handler.SqlHadler()
    text = 'Выберите необходимый тип товара\n\n'
    text = text + utils.generate_message(db.get_product_info(message.text))
    markup = utils.generate_markup(db.get_subproduct_info(message.text))
    order_calc.initialize_customer(str(message.chat.id),message.text)
    db.close()
    bot.send_message(chat_id=message.chat.id, text = text, reply_markup=markup)


@bot.message_handler(func = lambda mess: mess.text in sql_handler.SqlHadler().get_full_subproduct_info(),content_types=['text'])
def set_weight(message):
    markup = telebot.types.ReplyKeyboardRemove()
    db = sql_handler.SqlHadler()
    db.set_subproduct_id(message.chat.id,message.text)
    text = 'Введите необходимое количество в {0}'.format(db.get_unit(order_calc.get_subproduct_id(message.chat.id)))
    db.close()
    bot.send_message(chat_id=message.chat.id, text = text, reply_markup=markup)



@bot.message_handler(func=lambda message: utils.isFloat(message.text), content_types=['text'])
def count_order(message):
    db = sql_handler.SqlHadler()
    subproduct_id = order_calc.get_subproduct_id(message.chat.id)
    Category, Product_name, Description, Unit = db.get_order_info_for_customer(subproduct_id)
    weigth = float(message.text)
    Price, Small_discount, Small_discount_treshold, Big_discount, Big_discount_treshold, Unit_size = db.count_order_info(
        order_calc.get_subproduct_id(message.chat.id))
    if Decimal(str(weigth))%Decimal(str(Unit_size)) !=0.0:
        bot.send_message(chat_id=message.chat.id,text = 'Вы указали неправильное количество товара')
        return
    count = weigth/Unit_size
    price = 0
    if not Big_discount_treshold:
        if weigth<Small_discount_treshold:
            price = count*Price
        else:
            price = count*Small_discount
    else:
        if weigth<Small_discount_treshold:
            price = count*Price
        elif weigth>=Small_discount_treshold and weigth<Big_discount_treshold:
            price = count*Small_discount
        else:
            price = count*Big_discount
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton(text = 'Подтвердить', callback_data='accept'))
    markup.add(telebot.types.InlineKeyboardButton(text = 'Изменить количество товара', callback_data='change'))
    markup.add(telebot.types.InlineKeyboardButton(text = 'Удалить товар',callback_data='delete'))
    text = 'Вы выбрали:\n' \
           '{} {} {} {} {} - {} рублей'.format(Category, Product_name, Description, weigth, Unit, int(price))
    order_calc.add_order_product(message.chat.id,int(price),weigth)
    bot.send_message(chat_id=message.chat.id, text = text, reply_markup=markup)
    db.close()


def set_keyboard(chat_id):
    markup = telebot.types.InlineKeyboardMarkup()
    for subproduct_id in temp_shelve.get_order_keys(chat_id):
        markup.add(telebot.types.InlineKeyboardButton(temp_shelve.order_description(subproduct_id),callback_data = str(subproduct_id)))
    return markup

@bot.callback_query_handler(func=lambda call: call.data == 'execute_order')
def execute_order(call):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False)
    markup.add(telebot.types.KeyboardButton(text = 'Нажмите на кнопку, чтобы передать ваш номер телефона', request_contact=True))
    bot.edit_message_text(text=call.message.text, chat_id=call.message.chat.id, message_id=call.message.message_id)
    bot.send_message(text='Для начала сообщите свой номер телефона', chat_id=call.message.chat.id,reply_markup=markup)

def add_products(db,chat_id,order_id):
    for product in temp_shelve.get_order_items(chat_id):
        subproduct_id = product[0]
        weigth, price = product[1]
        db.add_order_product(order_id,int(subproduct_id),weigth,price)

@bot.message_handler(content_types=['contact'])
def contact(message):
    db = sql_handler.SqlHadler()
    db.add_customer(message.chat.id,message.contact.phone_number)
    order_id = db.add_order(message.chat.id,temp_shelve.get_full_price(message.chat.id))
    add_products(db,message.chat.id,order_id)
    text = 'Ваш заказ №{} был оформлен, ожидайте, пока мы вам позвоним'.format(order_id)

    bot.send_message(text = text, chat_id=message.chat.id)
    text = 'Новый заказ №{0}!\n'.format(order_id) + temp_shelve.order_info(message.chat.id)
    bot.send_message(text = text, chat_id=***REMOVED***)
    bot.send_contact(chat_id=***REMOVED***,phone_number=message.contact.phone_number,first_name=message.contact.first_name)
    temp_shelve.del_order(message.chat.id)


@bot.callback_query_handler(func = lambda call : call.data.isdigit())
def delete_buttons(call):
        temp_shelve.del_product(call.message.chat.id,call.data)
        message,markup = get_order_keyboard_and_message(call.message.chat.id)
        if isinstance(markup,telebot.types.ReplyKeyboardMarkup):
            text = 'Вы удалили все товары в заказе\n' \
                   'Выберите /order, чтобы начать заново'
            bot.edit_message_text(text=text, chat_id=call.message.chat.id, message_id=call.message.message_id)
        else:
            bot.edit_message_text(text=message, chat_id=call.message.chat.id, message_id=call.message.message_id,reply_markup = markup)

@bot.callback_query_handler(func= lambda call: True)
def button(call):
    db = sql_handler.SqlHadler()
    if call.data =='accept':
        subproduct_id, weigth, price = order_calc.get_order_product(call.message.chat.id)
        Category, Product_name, Description, Unit = db.get_order_info_for_customer(subproduct_id)
        temp_shelve.add_product(call.message.chat.id)
        message = 'Вы добавили продукт\n' \
                  '{} {} {} {} {} - {} рублей\n\n' \
                  'Выберите /order, чтобы продолжить работу с заказом'.format(Category, Product_name, Description,
                                                                              weigth, Unit, int(price))
        bot.edit_message_text(text = message, chat_id=call.message.chat.id,message_id=call.message.message_id)
    if call.data == 'change':
        message = 'Изменение количества товара\n' \
                  'Введите необходимое количество товара'
        bot.edit_message_text(text = message, chat_id=call.message.chat.id,message_id=call.message.message_id)
    if call.data == 'delete':
        order_calc.del_order(call.message.chat.id)
        message = 'Вы удалили товар из данного заказа\n' \
                  'Выберите /order, чтобы продолжить работу с заказом'
        bot.edit_message_text(text=message, chat_id=call.message.chat.id, message_id=call.message.message_id)
    if call.data == 'continue':
        markup = utils.generate_markup(db.get_categories())
        bot.edit_message_text(text = 'Продолжение выбора заказа', chat_id=call.message.chat.id, message_id=call.message.message_id)
        bot.send_message(chat_id = call.message.chat.id, text = 'Выбор категории', reply_markup = markup)
    if call.data == 'delete_order_product':
        markup = set_keyboard(call.message.chat.id)
        bot.edit_message_text(text = call.message.text,chat_id=call.message.chat.id, message_id=call.message.message_id,reply_markup = markup)
    if call.data == 'delete_order':
        message = 'Удаление заказа\n' \
                  'Выберите /order, чтобы начать заново'
        temp_shelve.del_order(call.message.chat.id)
        bot.edit_message_text(text=message, chat_id=call.message.chat.id, message_id=call.message.message_id)
    db.close()



if __name__=='__main__':
    temp_shelve = TempShelve()
    bot.polling(none_stop=True)

    updater = Updater(token=settings.token)
    conv_handler = ConversationHandler(
        entry_points= [CommandHandler('price', price)],

        states={
            CATEGORIES : [MessageHandler(Filters.text, category)],

            PRODUCT : [MessageHandler(Filters.text,product)]
        },
        fallbacks=[CommandHandler('cancel',cancel)]

    )
    updater.dispatcher.add_handler(conv_handler)

    updater.start_polling()


