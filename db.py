# -*- coding: utf-8 -*-
#import fdb
import os

import psycopg2
from psycopg2 import OperationalError
from datetime import datetime
#from utils.general import LOGGER
import tempfile
import logging
logging.basicConfig(filename='db.log', filemode='w', level=logging.DEBUG)

def is_valid_date_format(s):
    try:
        datetime.strptime(s, '%Y-%m-%d')
        return True
    except ValueError:
        return False
import logging

# Логгирование
logging.basicConfig(level=logging.INFO)

def is_valid_date_format(date_str):
    try:
        datetime.strptime(date_str, '%Y-%m-%d')
        return True
    except ValueError:
        return False

class DB:
    def __init__(self):
        self._connect()

    def _connect(self):
        try:
            self.con = psycopg2.connect(
                user="postgres",
                password="root",
                host="192.168.231.1",
                port="5432",
                database="postgres",
                client_encoding='utf8'
            )
            self.cur = self.con.cursor()
        except OperationalError as e:
            logging.error(f"The error '{e}' occurred")
            raise e

    def _execute_query(self, query, params=()):
        try:
            with self.con.cursor() as cur:
                cur.execute(query, params)
                # Проверка, является ли запрос операцией выбора (SELECT)
                if cur.description:
                    return cur.fetchall()
                else:
                    # Для операций, которые не возвращают результатов
                    self.con.commit()
                    return None
        except OperationalError as e:
            logging.error(f"Database operation error: {e}")
            return None

    # ... остальные методы ...

    def __del__(self):
        if self.con:
            self.con.close()

    def get_user_id_by_login(self, login):
        rows = self._execute_query("SELECT * FROM users WHERE login = %s", (login,))
        return rows[0][0] if rows and len(rows) == 1 else None

    def get_user_login_tg_id(self, tg_id):
        rows = self._execute_query("SELECT login FROM users WHERE telegram_id = %s", (tg_id,))
        return str(rows[0][0]) if rows and len(rows) == 1 else None

    def get_user_name_by_id(self, name):
        rows = self._execute_query("SELECT user_id FROM users WHERE \"NAME\" = %s", (name,))
        return str(rows[0][0]) if rows and len(rows) == 1 else None

    def get_user_id_by_tg_id(self, tg_id):
        rows = self._execute_query("SELECT user_id FROM users WHERE telegram_id = %s", (tg_id,))
        return str(rows[0][0]) if rows and len(rows) == 1 else None

    def get_report_type(self, name):
        rows = self._execute_query("SELECT * FROM ESTABLISHMENTS WHERE \"NAME\" = %s", (name,))
        return rows[0][6] if rows and len(rows) == 1 else None

    def get_id_est_by_name(self, name):
        query = "SELECT * FROM ESTABLISHMENTS WHERE \"NAME\" = %s"
        rows = self._execute_query(query, (name,))
        return rows[0][0] if rows and len(rows) == 1 else None

    def set_base_report(self, est_name, realdate, baseinfo=None):
        if is_valid_date_format(realdate):
            query = """
                INSERT INTO REPORT (ESTABLISHMENT_ID, REALDATE, BASEINFO, BASE_DONE) 
                VALUES (%s, %s, %s, %s)
            """
            est_id = self.get_id_est_by_name(est_name)
            if est_id is not None:
                self._execute_query(query, (est_id, realdate, baseinfo, datetime.now().date()))
                logging.info(f'Added report for {est_name} and date {realdate}')

    def update_base_report(self, est_name, realdate, baseinfo=None):
        if is_valid_date_format(realdate):
            query = """
                UPDATE REPORT SET BASEINFO = %s
                WHERE ESTABLISHMENT_ID = %s AND REALDATE = %s
            """
            est_id = self.get_id_est_by_name(est_name)
            if est_id is not None:
                self._execute_query(query, (baseinfo, est_id, realdate))
                logging.info(f'Updated BASEINFO for {est_name} and date {realdate}')

    def get_est_info_by_name(self, est_name):
        query = 'SELECT * FROM establishments WHERE "NAME" = %s'
        rows = self._execute_query(query, (est_name,))
        if rows and len(rows) == 1:
            return rows[0]
        else:
            return None

    def get_list_reports_for_period(self, start_date, end_date, est_name):
        est_id = self.get_id_est_by_name(est_name)
        query = """
            SELECT baseinfo FROM public.report 
            WHERE realdate BETWEEN %s AND %s AND establishment_id = %s
        """
        rows = self._execute_query(query, (start_date, end_date, est_id))
        for r in rows:
            print(r)

    def subscribe_user_to_est(self, telegram_id, est_name, pass_est):
        est_info = self.get_est_info_by_name(est_name)
        if not est_info:
            return "Название не найдено"
        est_id, _, _, est_pass, _, _, _, _, _, _ = est_info

        if est_pass != pass_est:
            return "Неправильный пароль"

        user_id = self.get_user_id_by_tg_id(telegram_id)
        if not user_id:
            self._execute_query("INSERT INTO USERS (TELEGRAM_ID, ROLE_ID) VALUES (%s, %s)", (telegram_id, 5))
            user_id = self.get_user_id_by_tg_id(telegram_id)

        subscription_exists = self._execute_query(
            "SELECT * FROM SUBSCRIPTION WHERE USER_ID = %s AND ESTABLISHMENTS_ID = %s",
            (user_id, est_id)
        )
        if subscription_exists:
            return "Вы уже подписаны"

        self._execute_query(
            "INSERT INTO SUBSCRIPTION (USER_ID, ESTABLISHMENTS_ID) VALUES (%s, %s)",
            (user_id, est_id)
        )
        return "success"

    def get_users_list_for_est(self, est_name):
        est_info = self.get_est_info_by_name(est_name)
        if not est_info:
            return "Название не найдено"

        est_id = est_info[0]
        query = "SELECT USER_ID FROM SUBSCRIPTION WHERE ESTABLISHMENTS_ID = %s"
        rows = self._execute_query(query, (est_id,))
        return [row[0] for row in rows] if rows else []

    def get_telegram_id(self, user_id):
        query = "SELECT * FROM users WHERE user_id = %s"
        rows = self._execute_query(query, (user_id,))
        return rows[0][-1] if rows and len(rows) == 1 else None

    def get_license_list(self):
        query = "SELECT * FROM license"
        rows = self._execute_query(query)
        return [f"{row[2]} {row[1]}" for row in rows] if rows else []

    def get_full_license_list(self):
        query = "SELECT * FROM license"
        return self._execute_query(query)

    def get_full_est_list(self):
        query = "SELECT * FROM establishments"
        return self._execute_query(query)

    def get_role_list(self):
        query = "SELECT * FROM public.\"ROLE\""
        rows = self._execute_query(query)
        return [f"{row[0]} {row[1]}" for row in rows] if rows else []

    def get_est_list_in_reports(self):
        query = "SELECT * FROM REPORT"
        rows = self._execute_query(query)
        return {row[1]: row[4] for row in rows} if rows else {}

    def get_curent_servers_tasks_count(self, server_id):
        query = "SELECT COUNT(*) FROM TASKS WHERE SERVER_ID = %s AND END_TIME IS NULL"
        row = self._execute_query(query, (server_id,))
        return row[0][0] if row else 0

    def get_server_for_task(self, id_not_res=[]):
        query = "SELECT * FROM SERVERS"
        rows = self._execute_query(query)
        best_tasks = -1000
        selected_server = {'ip': '', 'id': '', 'dev_id': ''}
        for row in rows:
            id, desc, ip, threads, dev = row
            if ip in id_not_res:
                continue
            current_tasks = self.get_curent_servers_tasks_count(id)
            if best_tasks < (threads - current_tasks):
                best_tasks = threads - current_tasks
                selected_server = {'ip': ip, 'id': id, 'dev_id': dev}
        return selected_server['ip'], selected_server['id'], selected_server['dev_id']

    def get_server_ip_by_id(self, server_id):
        query = "SELECT IP FROM SERVERS WHERE SERVER_ID = %s"
        row = self._execute_query(query, (server_id,))
        return row[0][0] if row and len(row) == 1 else None

    def is_tg_user_owner(self, telegram_id):
        user_id = self.get_user_id_by_tg_id(telegram_id)
        if not user_id:
            return False
        query = "SELECT COUNT(*) FROM ESTABLISHMENTS WHERE OWNER_ID = %s"
        count = self._execute_query(query, (user_id,))[0][0]
        return count > 0

    def get_money_for_tg_user(self, telegram_id):
        user_id = self.get_user_id_by_tg_id(telegram_id)
        if not user_id:
            return 0
        query = "SELECT MONEY FROM USERS WHERE USER_ID = %s"
        row = self._execute_query(query, (user_id,))
        return row[0][0] if row else 0

    def addmomey_for_tg_user(self, telegram_id, money):
        user_id = self.get_user_id_by_tg_id(telegram_id)
        if not user_id:
            return False
        current_money = self.get_money_for_tg_user(telegram_id)
        if current_money is None: current_money = 0
        new_money = current_money + money
        query = "UPDATE USERS SET MONEY = %s WHERE USER_ID = %s"
        self._execute_query(query, (new_money, user_id))
        return True

    def get_est_list_for_tg_user(self, telegram_id):
        user_id = self.get_user_id_by_tg_id(telegram_id)
        if not user_id:
            return []
        query = "SELECT ESTABLISHMENTS_ID FROM SUBSCRIPTION WHERE USER_ID = %s"
        rows = self._execute_query(query, (user_id,))
        return [self.get_est_name_by_id(row[0]) for row in rows] if rows else []

    def get_est_name_by_id (self, id):
        self.cur = self.con.cursor()
        self.cur.execute(f"SELECT \"NAME\" FROM ESTABLISHMENTS WHERE ESTABLISHMENTS_ID = {id}")
        user = self.cur.fetchall()
        if len(user) == 0:
            return None
        return user[0][0]

    def get_est_id_by_name (self, name):
        self.cur = self.con.cursor()
        self.cur.execute(f"SELECT ESTABLISHMENTS_ID FROM ESTABLISHMENTS WHERE \"NAME\" = '{name}'")
        user = self.cur.fetchall()
        if len(user) == 0:
            return None
        return user[0][0]

    def get_est_name_by_owner_id(self, telegram_id):
        user_id = self.get_user_id_by_tg_id(telegram_id)
        if not user_id:
            return None
        query = "SELECT \"NAME\" FROM ESTABLISHMENTS WHERE OWNER_ID = %s"
        rows = self._execute_query(query, (user_id,))
        return [row[0] for row in rows] if rows else []

    def get_license_name_and_price(self, lic_id):
        query = "SELECT \"NAME\", price FROM license WHERE license_id = %s"
        row = self._execute_query(query, (lic_id,))
        return (row[0][0], row[0][1]) if row else (None, None)

    def get_license_id_by_name(self, lic_name):
        query = "SELECT license_id FROM license WHERE \"NAME\" = %s"
        row = self._execute_query(query, (lic_name,))
        return (row[0][0]) if row else (None, None)

    def set_start_task(self, server_id, est_id, path):
        insert_query = """
            INSERT INTO public.tasks (server_id, est_id, begin_time, "path")
            VALUES (%s, %s, %s, %s);
        """
        self._execute_query(insert_query, (server_id, est_id, datetime.now().time(), path))

    def set_end_task(self, server_id, est_id, path):
        delete_query = """
            DELETE FROM public.tasks
            WHERE server_id = %s AND est_id = %s AND "path" = %s AND begin_time IS NOT NULL;
        """
        self._execute_query(delete_query, (server_id, est_id, path))

    def db_set_date_license_expired(self, date, est_id):
        update_query = """
            UPDATE public.establishments
            SET datelicense_expire = %s 
            WHERE establishments_id = %s;
        """
        self._execute_query(update_query, (date, est_id))

    def get_weights(self):
        query = "SELECT dbpath FROM public.settings WHERE setting_id = %s"
        row = self._execute_query(query, (1,))[0]

        if row:
            file_data = row[0]
            with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                temp_file_name = temp_file.name
                temp_file.write(file_data.tobytes())
            os.rename(temp_file_name, temp_file_name + '.pt')
            return temp_file_name + '.pt'

    def get_est_extra_by_name(self, name):
        self.cur = self.con.cursor()
        self.cur.execute(f"SELECT  extra FROM ESTABLISHMENTS WHERE  \"NAME\" = '{name}'")
        user = self.cur.fetchall()
        if len(user) == 0:
            return None
        return user[0][0]

def main():
    db = DB()

    out = ''
    print(db.addmomey_for_tg_user('440385834', 2000))
    print(db.get_est_list_for_tg_user('440385834'))
    print(db.get_money_for_tg_user('440385834'))
    print(db.get_curent_servers_tasks_count(1))
    print(db.subscribe_user_to_est('440385834', 'Pekarnya', 'Test'))

    db.set_base_report('2023-08-06', 'Basic informat')
    db.get_est_info_by_name('Pekarnya')
    print(db.get_report_type('Pekarnya'))
    print(db.get_license_list())
    print(db.get_id_est_by_name('Pekarnya'))
    print(db.get_users_list_for_est('Pekarnya'))
    print(db.get_user_id_by_login('discens'))
    print(db.get_telegram_id(0))
    print(db.get_license_name_and_price(1))
    print(db.get_server_for_task())

    db.set_start_task("Test1", '1', '1', 'path1')
    db.set_start_task("Test1", '1', '1', 'path2')
    db.set_start_task("Test1", '1', '1', 'path3')
    db.set_start_task("Test1", '1', '1', 'path4')
    db.set_start_task("Test1", '1', '1', 'path5')
    print(db.get_server_for_task())
    db.set_start_task("Test1", '1', '1', 'path6')

    db.set_end_task("Test1", '1', '1', 'path')
    temp = db.get_weights()
    print(temp)
    os.remove(temp)


if __name__ == '__main__':
    main()