
from config import USERS_COLUMNS_LIST, USERS_STATUS_COLUMNS_LIST, SANTA_CHILD_RELATION_COLUMNS_LIST
import sqlite3
import os
from threading import Lock
lock= Lock()

connection = sqlite3.connect("santa.sqlite3",check_same_thread=False)
cur = connection.cursor()


def create_table(table_name, columns):
    lock.acquire(True)
    cur.execute(f'CREATE TABLE IF NOT EXISTS {table_name} ({", ".join(columns)})')
    lock.release()

def get_row_by_column_value(table_name, columns_list, column_name, row_value):
    lock.acquire(True)
    cur.execute(f"SELECT * FROM {table_name} WHERE {column_name} = {row_value}") 
    row = cur.fetchone()
    lock.release()
    dict_row = dict()
    if row == None:
        return dict_row
    
    for i in range(len(columns_list)):
        dict_row[columns_list[i]] = row[i]
    return dict_row


def add_new_row(table_name, columns_list, dict_of_values):
    lock.acquire(True)
    if columns_list == USERS_COLUMNS_LIST:
        cur.execute(f'INSERT INTO {table_name} ({", ".join(columns_list[1::])}) VALUES (?,?,?,?,?,?)',(dict_of_values["tg_id"], dict_of_values["name_surname"],dict_of_values["group_number"], dict_of_values["group_name"], dict_of_values["tg_nickname"], dict_of_values["instagram_link"]))
    elif columns_list == USERS_STATUS_COLUMNS_LIST:
        cur.execute(f'INSERT INTO {table_name} ({", ".join(columns_list)}) VALUES (?,?,?,?)',(dict_of_values["tg_id"], dict_of_values["admin_status"], dict_of_values["registration_status"], dict_of_values["santa_status"]))
    elif columns_list == SANTA_CHILD_RELATION_COLUMNS_LIST:
        cur.execute(f'INSERT INTO {table_name} ({", ".join(columns_list)}) VALUES (?,?,?,?)',(dict_of_values["tg_id"], dict_of_values["your_santa_id"], dict_of_values["your_child_id"], dict_of_values["was_sent"]))
    connection.commit()
    lock.release()

def update_row_value_by_column_value(table_name, id_column_name, id_column_value, new_column_value_name, new_row_value):
    lock.acquire(True)
    cur.execute(f'UPDATE {table_name} SET {new_column_value_name} = (?) WHERE {id_column_name} = (?)', (new_row_value, id_column_value))
    connection.commit()
    lock.release()

def get_rows_by_column_value(table_name, columns_list, id_column_name, id_column_value):
    lock.acquire(True)
    cur.execute(f'SELECT * FROM {table_name} WHERE {id_column_name} = (?)', (id_column_value,))
    users = cur.fetchall()
    lock.release()
    if len(users) == 0: 
        return []
    list_of_dict_users = []
    for i in range(len(users)):
        d = {}
        for j in range(len(columns_list)):
            d[columns_list[j]] = users[i][j]
        list_of_dict_users.append(d)
    return list_of_dict_users

def get_all_rows(table_name, columns_list):
    lock.acquire(True)
    cur.execute(f'SELECT * FROM {table_name}')
    users = cur.fetchall()
    list_of_dict_users = []
    for i in range(len(users)):
        d = {}
        for j in range(len(columns_list)):
            d[columns_list[j]] = users[i][j]
        list_of_dict_users.append(d)
    lock.release()
    return list_of_dict_users

create_table("users",[
    f"{USERS_COLUMNS_LIST[0]} INTEGER PRIMARY KEY AUTOINCREMENT",
    f"{USERS_COLUMNS_LIST[1]} INTEGER UNIQUE",
    f"{USERS_COLUMNS_LIST[2]} TEXT",
    f"{USERS_COLUMNS_LIST[3]} INTEGER",
    f"{USERS_COLUMNS_LIST[4]} INTEGER",
    f"{USERS_COLUMNS_LIST[5]} TEXT",
    f"{USERS_COLUMNS_LIST[6]} TEXT",
    ])
create_table("users_status", [
    f"{USERS_STATUS_COLUMNS_LIST[0]} INTEGER UNIQUE",
    f"{USERS_STATUS_COLUMNS_LIST[1]} INTEGER",
    f"{USERS_STATUS_COLUMNS_LIST[2]} INTEGER",
    f"{USERS_STATUS_COLUMNS_LIST[3]} INTEGER",
    ])
create_table("santa_child_relation", [
    f"{SANTA_CHILD_RELATION_COLUMNS_LIST[0]} INTEGER UNIQUE",
    f"{SANTA_CHILD_RELATION_COLUMNS_LIST[1]} INTEGER",
    f"{SANTA_CHILD_RELATION_COLUMNS_LIST[2]} INTEGER",
    f"{SANTA_CHILD_RELATION_COLUMNS_LIST[3]} INTEGER",
    ])

        



