import sqlite3
from settings import database
from order_calc import CustomerTempData


class SqlHadler:

    def __init__(self):
        self.connection = sqlite3.connect(database)
        self.cursor = self.connection.cursor()

    def list_tuple_to_list(self,list_tuple):
        list = []
        for l in list_tuple:
            list.append(l[0])
        return list

    def get_table_name(self,text):
        sql_request = 'SELECT Table_name FROM Categories INNER JOIN Assortment ON Categories.Category_id = Assortment.Category_id AND Assortment.Product_name = "{}"'.format(text)
        return self.cursor.execute(sql_request).fetchall()[0][0]

    def get_categories(self):
        with self.connection:
            list_tuple = self.cursor.execute('SELECT Category FROM Categories').fetchall()
            return self.list_tuple_to_list(list_tuple)


    def get_full_assortment(self):
        with self.connection:
            sql = 'SELECT Product_name FROM Assortment'
            list_tuple = self.cursor.execute(sql).fetchall()
            return self.list_tuple_to_list(list_tuple)

    def get_assortment(self,text):
        with self.connection:
            sql_request = 'SELECT Product_name FROM Assortment INNER JOIN Categories On Category="{}" and Assortment.Category_id = Categories.Category_id'.format(text)
            list_tuple = self.cursor.execute(sql_request).fetchall()
            return self.list_tuple_to_list(list_tuple)

    def get_product_info(self,text):
        with self.connection:
            columns = 'Description,Price,Small_discount,Small_discount_treshold,Big_discount,Big_discount_treshold,Unit'
            sql_request = 'SELECT {0} FROM Products INNER JOIN Assortment ON Products.Product_id = Assortment."Product id" AND Assortment.Product_name = "{1}"'.format(columns,text)
            list_tuple = self.cursor.execute(sql_request).fetchall()
            return list_tuple

    def get_full_subproduct_info(self):
        with self.connection:
            sql_request = 'SELECT Description FROM Products'
            list_tuple = self.cursor.execute(sql_request).fetchall()
            return self.list_tuple_to_list(list_tuple)

    def get_subproduct_info(self,text):
        with self.connection:
            sql_request = 'SELECT Description FROM Products INNER JOIN Assortment ON Products.Product_id = Assortment."Product id" and Product_name="{0}"'.format(text)
            list_tuple = self.cursor.execute(sql_request).fetchall()
            return self.list_tuple_to_list(list_tuple)

    def get_unit(self,subproduct_id):
        with self.connection:
            sql_request = 'SELECT Unit FROM Products WHERE Sub_product_id={0}'.format(subproduct_id)
            return self.cursor.execute(sql_request).fetchone()[0]

    def get_order_info_for_customer(self,subproduct_id):
        with self.connection:
            sql_request ='SELECT Category,Product_name,Description,Unit FROM Assortment INNER JOIN Products' \
                         ' ON Assortment."Product id" = Products.Product_id and Sub_product_id={0} INNER JOIN Categories' \
                         ' ON Assortment.Category_id = Categories.Category_id'.format(subproduct_id)
            return self.cursor.execute(sql_request).fetchone()

    def count_order_info(self,subproduct_id):
        with self.connection:
            sql_request = 'SELECT Price,Small_discount,Small_discount_treshold,Big_discount,Big_discount_treshold,Unit_size FROM Assortment INNER JOIN Products' \
                          ' ON Assortment."Product id" = Products.Product_id and Sub_product_id={0} INNER JOIN Categories' \
                          ' ON Assortment.Category_id = Categories.Category_id'.format(subproduct_id)
            return self.cursor.execute(sql_request).fetchone()

    def set_subproduct_id(self,chat_id,text):
        with self.connection:
            temp_data = CustomerTempData().temp_data(chat_id)
            sql = "SELECT Sub_product_id FROM Products INNER JOIN Assortment ON Products.Product_id = Assortment.\"Product id\" and Description = '{0}' AND \"Product_name\"='{1}'".format(text,temp_data)
            subproduct_id = self.cursor.execute(sql).fetchone()[0]
            CustomerTempData().customer_subproduct_id(chat_id,subproduct_id)

    def add_customer(self,chat_id,phone_number):
        with self.connection:
            sql = 'SELECT customer_id FROM Customer WHERE customer_chat_id={0}'.format(chat_id)
            if len(self.cursor.execute(sql).fetchall())==0:
                sql = "INSERT INTO Customer (phone_number, customer_chat_id) VALUES ('{0}','{1}');".format(phone_number,chat_id)
                self.cursor.execute(sql)

    def add_order(self,chat_id,full_price):
        with self.connection:
            sql ='SELECT customer_id FROM Customer WHERE customer_chat_id={}'.format(chat_id)
            customer_id = self.cursor.execute(sql).fetchone()[0]
            sql = 'INSERT INTO "Order" (Customer_id, Total_cost) VALUES ({},{})'.format(customer_id,full_price)
            self.cursor.execute(sql)
            return self.cursor.execute('SELECT Order_id FROM "Order" WHERE rowid = last_insert_rowid()').fetchone()[0]

    def add_order_product(self,order_id,product_id,weigth,price):
        with self.connection:
            sql = 'INSERT INTO OrderProducts (Order_id, Product_id, Weight, Price) VALUES ({},{},{},{})'.format(order_id,product_id,weigth,price)
            self.cursor.execute(sql)

    def get_order_ids(self, chat_id):
        with self.connection:
            sql = 'SELECT customer_id FROM Customer WHERE customer_chat_id={}'.format(chat_id)
            customer_id = self.cursor.execute(sql).fetchone()
            if not customer_id:
                return []
            else:
                customer_id = customer_id[0]
            sql = 'SELECT Order_id FROM "Order" INNER JOIN Customer ON "Order".Customer_id = Customer.customer_id and Customer.customer_id={}'.format(customer_id)
            list = self.list_tuple_to_list(self.cursor.execute(sql).fetchall())
            return list

    def get_product_info_from_order(self,order_id):
        with self.connection:
            sql = 'SELECT Product_id,Weight,Price FROM OrderProducts WHERE Order_id={}'.format(order_id)
            list_tuple = self.cursor.execute(sql).fetchall()
            return list_tuple

    def get_min_weight(self,subproduct_id):
        with self.connection:
            sql ='SELECT Min_weight FROM Products Where Sub_product_id={}'.format(subproduct_id)
            return self.cursor.execute(sql).fetchone()[0]


    def close(self):
        self.connection.close()
