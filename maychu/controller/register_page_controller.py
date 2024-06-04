from ttkthemes import ThemedTk
import view.main_page as main_page  # import main_page.py
from model.account import Account  # import account.py

def register(name_entry, password_entry, app):
    username = name_entry.get()
    password = password_entry.get()

    account = Account(username, password)
    if account.check_if_account_exists():
        print("Tài khoản đã tồn tại!")
    else:
        account.save_to_db()
        open_main_page(app)
        print("Tạo tài khoản thành công!")

def open_main_page(app: ThemedTk):
    app.destroy()  # Đóng cửa sổ đăng nhập
    main_page.mainPage()  # Bắt đầu main_page.py của bạn
