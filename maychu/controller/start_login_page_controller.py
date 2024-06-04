from ttkthemes import ThemedTk

import view.main_page as main_page  # import main_page.py
import view.register_page as register_page  # import register_page.py

from model.account import Account  # import account.py

def login(name_entry, password_entry, app):
    username = name_entry.get()
    password = password_entry.get()

    account = Account(username, password)
    if account.check_password():
        print("Đăng nhập thành công!")
        open_main_page(app)
    else:
        print("Tên đăng nhập hoặc mật khẩu không hợp lệ.")

def open_register_page(app: ThemedTk):
    app.destroy()  # Đóng cửa sổ đăng nhập
    register_page.clickCreateAccount()  # Bắt đầu register_page.py của bạn

def open_main_page(app: ThemedTk):
    app.destroy()  # Đóng cửa sổ đăng nhập
    main_page.mainPage()  # Bắt đầu main_page.py của bạn
