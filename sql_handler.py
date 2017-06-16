import sqlite3
from settings import database

class SqlHadler:

    def __init__(self):
        self.connection = sqlite3.connect(database)
        self.cursor = self.connection.cursor()

    @staticmethod
    def list_tuple_to_list(list_tuple):
        list = []
        for l in list_tuple:
            list.append(l[0])
        return list

    def get_columns(self,table_name):
        with self.connection:
            sql_request = "PRAGMA TABLE_INFO ({})".format(table_name)
            list = self.cursor.execute(sql_request).fetchall()
            columns_list = []
            for l in list:
                if l[1] != 'Product_id':
                    columns_list.append(table_name+'."'+l[1]+'"')
            return ",".join(columns_list)

    def get_table_name(self,text):
        sql_request = 'SELECT Table_name FROM Categories INNER JOIN Assortment ON Categories.Category_id = Assortment.Category_id AND Assortment.Product_name = "{}"'.format(text)
        return self.cursor.execute(sql_request).fetchall()[0][0]

    def get_categories(self):
        with self.connection:
            list_tuple = self.cursor.execute('SELECT Category FROM Categories').fetchall()
            return self.list_tuple_to_list(list_tuple)

    def get_assortment(self,text):
        with self.connection:
            sql_request = 'SELECT Product_name FROM Assortment INNER JOIN Categories On Category="{}" and Assortment.Category_id = Categories.Category_id'.format(text)
            list_tuple = self.cursor.execute(sql_request).fetchall()
            return self.list_tuple_to_list(list_tuple)

    def get_product_info(self,text):
        with self.connection:
            table_name = self.get_table_name(text)
            sql_request = 'SELECT {0} FROM {1} INNER JOIN Assortment ON {1}.Product_id = Assortment."Product id" AND Assortment.Product_name = "{2}"'.format(self.get_columns(table_name),table_name,text)
            list_tuple = self.cursor.execute(sql_request).fetchall()
            return list_tuple

    def close(self):
        self.connection.close()
