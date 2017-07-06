import shelve
from settings import shelve_name
import sql_handler


class CustomerTempData:

    def initialize_customer(self, chat_id, product_name):
        with shelve.open(shelve_name) as storage:
            storage[chat_id] = product_name

    def temp_data(self, chat_id):
        with shelve.open(shelve_name) as storage:
            return storage.pop(str(chat_id))

    def customer_subproduct_id(self, chat_id,subproduct_id):
        with shelve.open(shelve_name) as storage:
            storage[str(chat_id)] = subproduct_id

    def get_subproduct_id(self, chat_id):
        with shelve.open(shelve_name) as storage:
            if isinstance(storage[str(chat_id)], tuple):
                return storage[str(chat_id)][0]
            else:
                return storage[str(chat_id)]

    def add_order_product(self, chat_id, price, weigth):
        with shelve.open(shelve_name) as storage:
            if isinstance(storage[str(chat_id)], tuple):
                subproduct_id = storage.pop(str(chat_id))[0]
            else:
                subproduct_id = storage.pop(str(chat_id))
            storage[str(chat_id)] = (subproduct_id, weigth, price)

    def get_order_product(self, chat_id):
        with shelve.open(shelve_name) as storage:
            return storage[str(chat_id)]

    def del_order(self, chat_id):
        with shelve.open(shelve_name) as storage:
            del storage[str(chat_id)]

    def get_order(self, chat_id):
        with shelve.open(shelve_name) as storage:
            return storage.pop(str(chat_id))


class TempShelve:

    def __init__(self):
        self.dictionary = {}
        self.temp_data = CustomerTempData()

    def add_product(self,chat_id):
        if str(chat_id) not in self.dictionary:
            subproduct_id, weigth,price = self.temp_data.get_order(str(chat_id))
            self.dictionary[str(chat_id)] = {str(subproduct_id) : (weigth,price)}
        else:
            subproduct_id,weigth,price = self.temp_data.get_order(str(chat_id))
            if str(subproduct_id) not in self.dictionary[str(chat_id)].keys():
                self.dictionary[str(chat_id)][str(subproduct_id)] = (weigth, price)
            else:
                old_weigth,old_price = self.dictionary[str(chat_id)].get(str(subproduct_id))
                self.dictionary[str(chat_id)][str(subproduct_id)] = (weigth+old_weigth, price+old_price)

    def order_description(self,subproduct_id,weigth=0,price=0):
        db = sql_handler.SqlHadler()
        Category, Product_name, Description, Unit = db.get_order_info_for_customer(subproduct_id)
        if weigth==0:
            return '{} {} {} '.format(Category, Product_name, Description)
        else:
            return '{} {} {} {} {} - {} рублей\n'.format(Category, Product_name, Description, weigth,
                                                                      Unit, int(price))

    def order_info(self,chat_id):
        if str(chat_id) not in self.dictionary:
            return None
        else:
            message = 'Ваш заказ\n'
            order_price = 0
            for product in self.dictionary[str(chat_id)].items():
                subproduct_id= product[0]
                weigth, price = product[1]
                message = message +self.order_description(subproduct_id,weigth,price)
                order_price = order_price + int(price)
            return message + 'Общая стоимость - {} руб.'.format(order_price)

    def get_full_price(self,chat_id):
        full_price = 0
        for product in self.dictionary[str(chat_id)].items():
            price = product[1][1]
            full_price = full_price + int(price)
        return full_price

    def get_order_keys(self,chat_id):
        return self.dictionary[str(chat_id)].keys()

    def get_order_items(self,chat_id):
        return self.dictionary[str(chat_id)].items()

    def del_order(self,chat_id):
        del self.dictionary[str(chat_id)]

    def del_product(self,chat_id,subproduct_id):
        del self.dictionary[str(chat_id)][str(subproduct_id)]
        if len(self.dictionary[str(chat_id)])<1:
            self.del_order(str(chat_id))