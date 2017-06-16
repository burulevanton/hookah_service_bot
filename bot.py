from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, RegexHandler, ConversationHandler
from telegram import ReplyKeyboardRemove,ReplyKeyboardMarkup
import settings
import sql_handler
import utils


CATEGORIES, PRODUCT = range(2)


def start(bot, update):
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
    text = utils.generate_message(db.get_product_info(text),db.get_columns(db.get_table_name(text)))
    markup = ReplyKeyboardRemove()
    bot.sendMessage(chat_id = update.message.chat_id,text = text,reply_markup = markup)
    return ConversationHandler.END


def cancel(bot,update):
    return ConversationHandler.END

updater = Updater(token=settings.token)

conv_handler = ConversationHandler(
    entry_points= [CommandHandler('start', start)],

    states={
        CATEGORIES : [MessageHandler(Filters.text, category)],

        PRODUCT : [MessageHandler(Filters.text,product)]
    },
    fallbacks=[CommandHandler('cancel',cancel)]

)
updater.dispatcher.add_handler(conv_handler)

updater.start_polling()


