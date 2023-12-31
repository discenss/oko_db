import os.path
import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QTableWidget, QTableWidgetItem, QWidget, QDateEdit, QHBoxLayout, QFileDialog,
                             QVBoxLayout, QPushButton, QInputDialog, QTabWidget, QDialog, QMenu, QLineEdit, QLabel, QMessageBox, QComboBox, QTextEdit)
from PyQt5.QtCore import Qt
from db import DB
from datetime import datetime
import telebot
bot = telebot.TeleBot('6560876647:AAGZXlZDeCazV8vQ9Wf6NZlqpJV7enc1olM')

import re

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import random
import string

def generate_password(length=12, include_digits=True, include_special_chars=True):
    # Символы для формирования пароля (буквы верхнего и нижнего регистра по умолчанию)
    characters = string.ascii_letters

    # Добавление цифр
    if include_digits:
        characters += string.digits

    # Добавление специальных символов
    if include_special_chars:
        characters += string.punctuation

    # Генерация пароля
    password = ''.join(random.choice(characters) for _ in range(length))
    return password

def is_valid_email(text):
    email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')

    # Проверка текста на соответствие регулярному выражению
    return bool(re.match(email_pattern, text))

def send_email(to_email, message_test):
    from_email = "sysinfookoai@gmail.com"
    password = 'ozti ehbb wvkp biaq'

    msg = MIMEMultipart()
    msg['From'] = from_email
    msg['To'] = to_email
    msg['Subject'] = "Логін і пароль OKOAI"
    msg.attach(MIMEText(message_test, 'plain'))
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(from_email, password)
    text = msg.as_string()
    server.sendmail(from_email, to_email, text)
    server.quit()


def extract_info_from_string(s):
    pattern = r'^(?P<name>[a-zA-Z\s]+)\s+(?P<date>\d{4}-\d{2}-\d{2})\.pdf$'
    match = re.match(pattern, s)

    if match:
        return True, match.group('name').strip(), match.group('date')
    else:
        return False, None, None


class ReportsTableWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.layout = QVBoxLayout(self)

        # Таблица в верхней части
        self.table = QTableWidget(self)
        self.layout.addWidget(self.table)

        # ComboBox прямо под таблицей
        hbox_dates = QHBoxLayout()
        self.label = QLabel("Establishment:", self)
        hbox_dates.addWidget(self.label)
        self.comboBox = QComboBox(self)
        hbox_dates.addWidget(self.comboBox)

        # Горизонтальные макеты для элементов выбора даты


        self.dateFromLabel = QLabel("Date from:", self)
        hbox_dates.addWidget(self.dateFromLabel)
        self.dateFromEdit = QDateEdit(self)
        self.dateFromEdit.setFixedSize(100, 30)
        hbox_dates.addWidget(self.dateFromEdit)

        date_end_layout = QHBoxLayout()
        self.dateEndLabel = QLabel("Date end:", self)
        date_end_layout.addWidget(self.dateEndLabel)
        self.dateEndEdit = QDateEdit(self)
        self.dateEndEdit.setFixedSize(100, 30)
        date_end_layout.addWidget(self.dateEndEdit)
        hbox_dates.addLayout(date_end_layout)  # добавляем этот макет в hbox_dates

        # Добавляем горизонтальный макет с элементами выбора даты в основной макет


        self.button = QPushButton("Поиск", self)
        hbox_dates.addWidget(self.button)

        # Подключение кнопки к обработчику
        self.button.clicked.connect(self.button_clicked)

        self.layout.addLayout(hbox_dates)

        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.context_menu)

        # После инициализации, заполните таблицу
        self.refresh_table()

    def button_clicked(self):
        date_from = self.dateFromEdit.date().toString("yyyy-MM-dd")
        date_end = self.dateEndEdit.date().toString("yyyy-MM-dd")
        db = DB()
        est_name = self.comboBox.currentText()
        name = db.get_est_id_by_name(est_name)

        query = """SELECT r.REPORT_ID, e.\"NAME\", r.REALDATE, r.BASEINFO, r.BASE_DONE, r.FULL_DONE
                   FROM REPORT r
                   JOIN ESTABLISHMENTS e ON e.ESTABLISHMENTS_ID = r.ESTABLISHMENT_ID
                   WHERE r.ESTABLISHMENT_ID = %s AND r.REALDATE BETWEEN %s AND %s"""

        db.cur.execute(query, (name, date_from, date_end))
        rows = db.cur.fetchall()

        self.table.setRowCount(len(rows))
        if rows == None or len(rows) == 0:
            return

        self.table.setColumnCount(len(rows[0]))
        for row_index, row in enumerate(rows):
            for col_index, data in enumerate(row):
                self.table.setItem(row_index, col_index, QTableWidgetItem(str(data)))

        self.table.setHorizontalHeaderLabels(
            ["REPORT_ID", "ESTABLISHMENT", "REALDATE", "BASEINFO", "BASE_DONE", "FULL_DONE"])

        for est in self.get_column_data(self.table, 1):
            if self.comboBox.findText(est) == -1:  # Если элемент не найден
                self.comboBox.addItem(est)


    def context_menu(self, position):
        # Ваш код для контекстного меню
        pass

    def get_column_data(self, table_widget, column):
        data = []
        for row in range(table_widget.rowCount()):
            item = table_widget.item(row, column)
            if item and item.text():
                data.append(item.text())
        return data

    def refresh_table(self):
        db = DB()
        db.cur.execute("""SELECT r.REPORT_ID, e."NAME", r.REALDATE, r.BASEINFO, r.BASE_DONE, r.FULL_DONE
         FROM REPORT r
         JOIN ESTABLISHMENTS e ON e.ESTABLISHMENTS_ID = r.ESTABLISHMENT_ID""")
        rows = db.cur.fetchall()

        self.table.setRowCount(len(rows))
        self.table.setColumnCount(len(rows[0]))
        for row_index, row in enumerate(rows):
            for col_index, data in enumerate(row):
                self.table.setItem(row_index, col_index, QTableWidgetItem(str(data)))


        self.table.setHorizontalHeaderLabels(
            ["REPORT_ID", "ESTABLISHMENT", "REALDATE", "BASEINFO", "BASE_DONE", "FULL_DONE"])

        for est in self.get_column_data(self.table, 1):
            if self.comboBox.findText(est) == -1:  # Если элемент не найден
                self.comboBox.addItem(est)

    def show_error_message(self, message):
        QMessageBox.critical(self, "Ошибка", message, QMessageBox.Ok)

    def context_menu(self, position):
        menu = QMenu(self)

        add_action = menu.addAction("Добавить отчёт к записи")
        edit_action = menu.addAction("Получить отчёт из записи")
        delete_action = menu.addAction("Удалить")
        update_action = menu.addAction("Обновить")

        action = menu.exec_(self.mapToGlobal(position))

        if action == add_action:
            self.add_record()
        elif action == edit_action:
            self.edit_record()
        elif action == delete_action:
            self.delete_record()
        elif action == update_action:
            self.refresh_table()

    def add_record(self):
        row = self.table.currentRow()
        if row == -1:
            return

        file_name, _ = QFileDialog.getOpenFileName(self, "Open File", "", "All Files (*);;Text Files (*.pdf)")

        if not file_name:
            return  # пользователь отменил выбор файла

        res, est_name_in_file, rep_date_in_file = extract_info_from_string(os.path.basename(file_name))
        if res == False:
            print(f"Ошибка: имя отчёта не соответствует шаблону: ИМЯ ГГГГ-ММ-ДД.")
            return

        est_name = str(
            self.table.item(row, 1).text())
        if est_name != est_name_in_file:
            print("ОШИБКА: Имя заведения из файла не соответствует выбранному заведению для отправки отчёта")
            return

        date_rep = str(
            self.table.item(row, 2).text())

        if date_rep != rep_date_in_file:
            print("ОШИБКА: Дата указанная в файле и реальная дата отчёта не совпадают")
            return

        with open(file_name, 'rb') as file:
            file_data = file.read()
        db = DB()
        report_id = int(
            self.table.item(row, 0).text())

        query = """UPDATE REPORT SET FULLINFO = %s, FULL_DONE = %s WHERE REPORT_ID = %s"""
        data = (file_data, str(datetime.now().date()), report_id)
        db.cur.execute(query, data)
        db.con.commit()
        self.refresh_table()

        users = db.get_users_list_for_est(est_name)
        for user in users:
            if user is None:
                continue
            tg_id = db.get_telegram_id(user)
            print(tg_id)
            with open(file_name, 'rb') as doc:
                bot.send_message(tg_id,f"Вам надіслано звіт оператора для закладу {est_name_in_file} за дату {date_rep}" )
                bot.send_document(tg_id, doc)

    def edit_record(self):
        print("Test")

    def delete_record(self):
        print("Test")

class UsersTableWidget(QTableWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        self.refresh_table()

    def init_ui(self):
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.context_menu)

    def refresh_table(self):

        db = DB()
        db.cur.execute("SELECT * FROM USERS")
        rows = db.cur.fetchall()

        self.setRowCount(len(rows))
        self.setColumnCount(len(rows[0]))
        for row_index, row in enumerate(rows):
            for col_index, data in enumerate(row):
                self.setItem(row_index, col_index, QTableWidgetItem(str(data)))

        self.setHorizontalHeaderLabels(["USER_ID", "NAME", "LOGIN", "ROLE_ID", "PASS",
                                            "MONEY", "TELEGRAM_ID"])
    def show_error_message(self, message):
        QMessageBox.critical(self, "Ошибка", message, QMessageBox.Ok)

    def context_menu(self, position):
        menu = QMenu(self)

        add_action = menu.addAction("Добавить")
        edit_action = menu.addAction("Изменить")
        delete_action = menu.addAction("Удалить")

        action = menu.exec_(self.mapToGlobal(position))

        if action == add_action:
            self.add_record()
        elif action == edit_action:
            self.edit_record()
        elif action == delete_action:
            self.delete_record()

    def add_record(self):
        db = DB()
        dialog = QDialog(self)
        layout = QVBoxLayout()
        dialog.setWindowTitle('Добавление пользователя')

        self.name_input = QLineEdit(dialog)
        layout.addWidget(QLabel("Name:"))
        layout.addWidget(self.name_input)

        self.login_input = QLineEdit(dialog)
        layout.addWidget(QLabel("Login:"))
        layout.addWidget(self.login_input)

        self.pass_input = QLineEdit(dialog)
        layout.addWidget(QLabel("Pass:"))
        layout.addWidget(self.pass_input)

        layout.addWidget(QLabel("Role:"))
        self.role_combo = QComboBox(dialog)
        layout.addWidget(self.role_combo)
        for l in db.get_role_list():
            self.role_combo.addItem(l)

        self.tg_input = QLineEdit(dialog)
        layout.addWidget(QLabel("telegram id"))
        layout.addWidget(self.tg_input)

        submit_button = QPushButton("Применить", dialog)
        submit_button.clicked.connect(dialog.accept)
        layout.addWidget(submit_button)

        dialog.setLayout(layout)

        result = dialog.exec_()
        if result == QDialog.Accepted:
            name = self.name_input.text()
            login = self.login_input.text()
            passw = self.pass_input.text()
            role = self.role_combo.currentText().split(' ')[0]
            tg_input = self.tg_input.text()

            if is_valid_email(login) is False:
                print("ОШИБКА: Логин не является валидным email")
                return
            # Добавление записи в таблицу ESTABLISHMENTS
            db.cur.execute(f"INSERT INTO USERS (\"NAME\", login, ROLE_ID, PASS, telegram_id) VALUES"
                        f" ('{name}', '{login}', '{role}', '{passw}', '{tg_input}')")
            db.con.commit()
            self.refresh_table()

    def edit_record(self):
        row = self.currentRow()
        if row == -1:
            return
        db = DB()
        dialog = QDialog(self)
        layout = QVBoxLayout()
        dialog.setWindowTitle('Добавление записи')

        self.name_input = QLineEdit(dialog)
        layout.addWidget(QLabel("Name:"))
        layout.addWidget(self.name_input)

        self.login_input = QLineEdit(dialog)
        layout.addWidget(QLabel("Login"))
        layout.addWidget(self.login_input)

        layout.addWidget(QLabel("Role:"))
        self.role_combo = QComboBox(dialog)
        layout.addWidget(self.role_combo)
        for l in db.get_role_list():
            self.role_combo.addItem(l)

        self.pass_input = QLineEdit(dialog)
        layout.addWidget(QLabel("Password:"))
        layout.addWidget(self.pass_input)

        self.tg_input = QLineEdit(dialog)
        layout.addWidget(QLabel("TG User:"))
        layout.addWidget(self.tg_input)


        # Заполните начальные значения из выбранной строки:
        self.name_input.setText(self.item(row, 1).text())
        self.login_input.setText(self.item(row, 2).text())
        self.pass_input.setText(self.item(row, 4).text())
        self.tg_input.setText(self.item(row, 6).text())

        # Добавьте аналогичные виджеты для всех других полей

        submit_button = QPushButton("Отправить", dialog)
        submit_button.clicked.connect(dialog.accept)
        layout.addWidget(submit_button)

        dialog.setLayout(layout)

        result = dialog.exec_()
        if result == QDialog.Accepted:
            name = self.name_input.text()
            login = self.login_input.text()
            passw = self.pass_input.text()
            role = self.role_combo.currentText().split(' ')[0]
            tg_id = self.tg_input.text()

            if is_valid_email(login) is False:
                print("ОШИБКА: Логин не является валидным email")
                return
            # Добавление записи в таблицу ESTABLISHMENTS
            user_id = int(
                self.item(row, 0).text())
            db.cur.execute(
                f"UPDATE USERS SET \"NAME\" = '{name}', login = '{login}', role_id = '{role}', pass = '{passw}', telegram_id = '{tg_id}'  WHERE user_id = {user_id} ")
            db.con.commit()
            self.refresh_table()

    def delete_record(self):
        db = DB()
        row = self.currentRow()
        if row == -1:
            return

        establishment_id = int(self.item(row, 0).text())

        db.cur.execute(f"DELETE FROM users WHERE user_id = {establishment_id}")
        db.con.commit()
        self.refresh_table()

class EstablishmentsTableWidget(QTableWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        self.refresh_table()

    def init_ui(self):
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.context_menu)


    def refresh_table(self):
        db = DB()
        db.cur.execute("""SELECT e.ESTABLISHMENTS_ID, e."NAME", e.ADDRESS, e.PASS,
                                e.LICENSE_ID, u.telegram_id, e.REPORT_TYPE, e.VIDEO_PATH, 
                                e.DATELICENSE_EXPIRE 
                           FROM ESTABLISHMENTS e 
                           JOIN USERS u ON e.OWNER_ID = u.USER_ID""")
        rows = db.cur.fetchall()

        self.setRowCount(len(rows))
        self.setColumnCount(len(rows[0]))
        for row_index, row in enumerate(rows):
            for col_index, data in enumerate(row):
                self.setItem(row_index, col_index, QTableWidgetItem(str(data)))

        self.setHorizontalHeaderLabels(["ESTABLISHMENTS_ID", "NAME", "ADDRESS", "PASS",
                                            "LICENSE_ID", "OWNER TG", "REPORT_TYPE",
                                            "VIDEO_PATH", "DATELICENSE_EXPIRE"])

    def show_error_message(self, message):
        QMessageBox.critical(self, "Ошибка", message, QMessageBox.Ok)

    def context_menu(self, position):
        menu = QMenu(self)

        add_action = menu.addAction("Добавить")
        edit_action = menu.addAction("Изменить")
        delete_action = menu.addAction("Удалить")
        send_action = menu.addAction("Добавить отправить данные авторизации")

        action = menu.exec_(self.mapToGlobal(position))

        if action == add_action:
            self.add_record()
        elif action == edit_action:
            self.edit_record()
        elif action == delete_action:
            self.delete_record()
        elif action == send_action:
            self.send_auth()

    def add_record(self):
        db = DB()
        dialog = QDialog(self)
        layout = QVBoxLayout()
        dialog.setWindowTitle('Добавление записи')

        self.name_input = QLineEdit(dialog)
        layout.addWidget(QLabel("Name:"))
        layout.addWidget(self.name_input)

        self.address_input = QLineEdit(dialog)
        layout.addWidget(QLabel("Address:"))
        layout.addWidget(self.address_input)

        self.pass_input = QLineEdit(dialog)
        layout.addWidget(QLabel("Password:"))
        layout.addWidget(self.pass_input)
        self.pass_input.setText(generate_password(5, True, False))

        layout.addWidget(QLabel("License type:"))
        self.license_combo = QComboBox(dialog)
        layout.addWidget(self.license_combo)
        for l in db.get_license_list():
            self.license_combo.addItem(l)

        self.user_input = QLineEdit(dialog)
        layout.addWidget(QLabel("User(TG ID):"))
        layout.addWidget(self.user_input)

        self.rep_input = QLineEdit(dialog)
        layout.addWidget(QLabel("Report type:"))
        layout.addWidget(self.rep_input)

        self.video_input = QLineEdit(dialog)
        layout.addWidget(QLabel("Video path:"))
        layout.addWidget(self.video_input)

        self.date_input = QLineEdit(dialog)
        layout.addWidget(QLabel("Date expire"))
        layout.addWidget(self.date_input)

        submit_button = QPushButton("Применить", dialog)
        submit_button.clicked.connect(dialog.accept)
        layout.addWidget(submit_button)

        dialog.setLayout(layout)

        result = dialog.exec_()
        if result == QDialog.Accepted:
            name = self.name_input.text()
            address = self.address_input.text()
            passw = self.pass_input.text()
            license = db.get_license_id_by_name(self.license_combo.currentText().split(' ')[1])
            user = self.user_input.text()
            rep_input = self.rep_input.text()
            video_input = self.video_input.text()
            date_input = self.date_input.text()

            #user_name = db.get_user_name_by_id(user)
            user_id = db.get_user_id_by_tg_id(user)
            if user_id is None:
                self.show_error_message('Пользователь не найден')
                return



            # Добавление записи в таблицу ESTABLISHMENTS
            db.cur.execute(f"INSERT INTO ESTABLISHMENTS (\"NAME\", ADDRESS, PASS, LICENSE_ID, OWNER_ID, REPORT_TYPE, VIDEO_PATH, datelicense_expire) VALUES"
                        f" ('{name}', '{address}', '{passw}', '{license}', '{user_id}' , '{rep_input}', '{video_input}', '{date_input}' )")
            db.con.commit()
            self.refresh_table()

    def edit_record(self):
        row = self.currentRow()
        if row == -1:
            return
        db = DB()
        dialog = QDialog(self)
        layout = QVBoxLayout()
        dialog.setWindowTitle('Добавление записи')

        self.name_input = QLineEdit(dialog)
        layout.addWidget(QLabel("Name:"))
        layout.addWidget(self.name_input)

        self.address_input = QLineEdit(dialog)
        layout.addWidget(QLabel("Address:"))
        layout.addWidget(self.address_input)

        self.pass_input = QLineEdit(dialog)
        layout.addWidget(QLabel("Password:"))
        layout.addWidget(self.pass_input)

        layout.addWidget(QLabel("License type:"))
        self.license_combo = QComboBox(dialog)
        layout.addWidget(self.license_combo)
        for l in db.get_license_list():
            self.license_combo.addItem(l)

        self.user_input = QLineEdit(dialog)
        layout.addWidget(QLabel("User:"))
        layout.addWidget(self.user_input)

        self.rep_input = QLineEdit(dialog)
        layout.addWidget(QLabel("Report type:"))
        layout.addWidget(self.rep_input)

        self.video_input = QLineEdit(dialog)
        layout.addWidget(QLabel("Video path:"))
        layout.addWidget(self.video_input)

        self.date_input = QLineEdit(dialog)
        layout.addWidget(QLabel("Date expire"))
        layout.addWidget(self.date_input)

        # Заполните начальные значения из выбранной строки:
        self.name_input.setText(self.item(row, 1).text())
        self.address_input.setText(self.item(row, 2).text())
        self.pass_input.setText(self.item(row, 3).text())
        self.user_input.setText(self.item(row, 5).text())
        self.rep_input.setText(self.item(row, 6).text())
        self.video_input.setText(self.item(row, 7).text())
        self.date_input.setText(self.item(row, 8).text())
        # Добавьте аналогичные виджеты для всех других полей

        submit_button = QPushButton("Применить", dialog)
        submit_button.clicked.connect(dialog.accept)
        layout.addWidget(submit_button)

        dialog.setLayout(layout)

        result = dialog.exec_()
        if result == QDialog.Accepted:
            name = self.name_input.text()
            address = self.address_input.text()
            passw = self.pass_input.text()
            if len(passw) == 0:
                passw = generate_password(5, True, False)

            license = self.license_combo.currentText().split(' ')[1]
            license_id = db.get_license_id_by_name(license)

            user = self.user_input.text()
            rep_input = self.rep_input.text()
            video_input = self.video_input.text()
            date_input = self.date_input.text()

            user_id = db.get_user_id_by_tg_id(user)
            if user_id is None:
                self.show_error_message('Пользователь не найден')
                return

            # Обновление записи в таблице ESTABLISHMENTS
            establishment_id = int(
                self.item(row, 0).text())
            db.cur.execute(
                f"UPDATE ESTABLISHMENTS SET \"NAME\" = '{name}', ADDRESS = '{address}', PASS = '{passw}', LICENSE_ID = '{license_id}', OWNER_ID = '{user_id}', REPORT_TYPE = '{rep_input}', VIDEO_PATH = '{video_input}', datelicense_expire = '{date_input}'  WHERE ESTABLISHMENTS_ID = {establishment_id} ")
            db.con.commit()
            self.refresh_table()

    def delete_record(self):
        db = DB()
        row = self.currentRow()
        if row == -1:
            return

        establishment_id = int(self.item(row, 0).text())

        db.cur.execute(f"DELETE FROM ESTABLISHMENTS WHERE ESTABLISHMENTS_ID = {establishment_id}")
        db.con.commit()
        self.refresh_table()

    def send_auth(self):
        db = DB()
        dialog = QDialog(self)
        layout = QVBoxLayout()
        dialog.setWindowTitle('Отправить данные авторизации в бот OKOAI')
        self.text_input = QTextEdit(dialog)

        row = self.currentRow()
        if row == -1:
            return

        user_login = db.get_user_login_tg_id(self.item(row, 5).text())
        if is_valid_email(user_login) is False:
            print("ОШИБКА: Логин не является валидным email")
            return
        layout.addWidget(QLabel("Текст сообщения пользователю: " + user_login))
        layout.addWidget(self.text_input)
        if self.item(row, 5).text() is None or self.item(row, 5).text() is None:
            print("Не установлено имя заведения или пароль")
            return

        message_template = f"""
Ласково просимо до системи OKOAI.

    Ваша назва_закладу та пароль для підписки у боті ОКОАІ:
        
    Заклад: {self.item(row, 1).text()}
    Пароль: {self.item(row, 3).text()}

    Посилання на бота в телеграмі https://t.me/OKOAIbot

    Ви можете передати інформацію особам, які також зацікавлені в отриманні аналітики ОКОАІ по цьому закладу
    
    
    З повагою,
        Команда OKOAI.
        """
        self.text_input.setText(message_template)

        dialog.setLayout(layout)

        submit_button = QPushButton("Применить", dialog)
        submit_button.clicked.connect(dialog.accept)
        layout.addWidget(submit_button)

        dialog.setLayout(layout)

        result = dialog.exec_()
        if result == QDialog.Accepted:
            send_email(user_login, self.text_input.toPlainText())
            print("Сообщение отправлено")



class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("OKO AI Database Viewer")
        self.resize(1000, 600)
        # Tab widget
        self.tab_widget = QTabWidget(self)
        self.setCentralWidget(self.tab_widget)

        self.establishments_widget = EstablishmentsTableWidget(self)
        self.tab_widget.addTab(self.establishments_widget, "Establishments")

        self.users_widget = UsersTableWidget(self)
        self.tab_widget.addTab(self.users_widget, "Users")

        self.reports_widget = ReportsTableWidget(self)
        self.tab_widget.addTab(self.reports_widget, "Reports")



app = QApplication(sys.argv)
window = MainWindow()
window.show()
app.exec_()