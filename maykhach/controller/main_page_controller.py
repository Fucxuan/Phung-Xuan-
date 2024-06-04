import threading
import time
import sqlite3
from datetime import datetime, timedelta

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk, ImageOps

from reportlab.platypus import SimpleDocTemplate, Paragraph, TableStyle
from reportlab.platypus import Table as ReportLabTable
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet

from model.table import Table
from model.cafeitem import CafeItem
from model.fee import Fee
from model.account import Account

#----------------PHẦN PHƯƠNG THỨC----------------

#----------------Phương thức đăng nhập----------------
def get_last_registered_user():
    conn = sqlite3.connect('database.sqlite')
    c = conn.cursor()
    c.execute('SELECT username FROM accounts ORDER BY rowid DESC LIMIT 1')
    last_registered_user = c.fetchone()
    conn.commit()
    conn.close()
    return last_registered_user[0] if last_registered_user else None

#----------------Phương thức Bàn--------------------

def save_table(name, type, fee, image_path, window, table_tree):
    try:
        fee = int(fee)
        new_table = Table(name, type, False, fee, 0, 0, 0, image_path, 0)
        new_table.save_to_db()
        tables.append(new_table)
        update_treeview(table_tree)
        window.destroy()
    except ValueError:
        messagebox.showerror("Lỗi", "Dữ liệu không hợp lệ ở một hoặc nhiều trường")

# Một từ điển để giữ các tham chiếu đến hình ảnh
image_refs = {}

def update_treeview(table_tree: ttk.Treeview):
    global image_refs
    image_refs.clear()  # Xóa các tham chiếu hình ảnh hiện có

    for i in table_tree.get_children():
        table_tree.delete(i)

    for table in tables:
        open_close_status = "Mở" if table.open_close else "Đóng"
        if table.image_path:
            img = Image.open(table.image_path)
            img = img.convert("RGBA")  # Đảm bảo hình ảnh ở định dạng RGBA

            # Thay đổi kích thước và bảo toàn độ trong suốt
            img = ImageOps.fit(img, (100, 100), Image.Resampling.LANCZOS)
            
            photo = ImageTk.PhotoImage(img)
            image_refs[table.name] = photo
            table_tree.insert('', 'end', image=photo, values=(table.name, table.type, table.feePerMinute, table.duration/60, table.fee, open_close_status))
        else:
            table_tree.insert('', 'end', values=(table.name, table.type, table.feePerMinute, table.duration/60, table.fee, open_close_status))
           
def update_table(window, table, new_type, new_fee, table_tree: ttk.Treeview):
    try:
        new_fee = int(new_fee)
        table.type = new_type
        table.feePerMinute = new_fee
        table.update_db()
        update_treeview(table_tree)  # Làm mới cây
        window.destroy()
    except ValueError:
        messagebox.showerror("Lỗi", "Dữ liệu phí không hợp lệ. Vui lòng nhập một số hợp lệ.")

def toggle_open_close(table_tree: ttk.Treeview):
    selected_item = table_tree.selection()
    if selected_item:
        item_values = table_tree.item(selected_item, 'values')
        table_name = item_values[0]

        selected_table = next((table for table in tables if table.name == table_name), None)
        if selected_table:
            # Chuyển đổi trạng thái mở/đóng
            selected_table.open_close = not selected_table.open_close

            if selected_table.open_close:
                # Nếu bàn đang mở, bắt đầu đếm thời gian và thay đổi màu hàng thành màu xanh
                start_timer(selected_table, table_tree)
            else:
                # Nếu bàn đang đóng, dừng đếm thời gian, tính tổng phí và loại bỏ màu xanh
                stop_timer(selected_table, table_tree)
 
            update_treeview(table_tree)

def start_timer(table, table_tree: ttk.Treeview):
    def timer():
        update_counter = 0
        while getattr(table, "timer_running", False):
            time.sleep(1)
            table.duration += 1
            update_counter += 1
            if update_counter >= 60:  # Mỗi 60 giây,
                update_treeview(table_tree)  # Cập nhật treeview
                update_counter = 0  # Đặt lại bộ đếm

    table.timer_running = True
    t = threading.Thread(target=timer)
    t.start()

def stop_timer(table, table_tree: ttk.Treeview):
    timerFee = table.duration/60 * table.feePerMinute
    table.fee += round(timerFee, 2)
    table.timer_running = False
    update_treeview(table_tree)

def load_tables_from_db(table_tree: ttk.Treeview):
    global tables
    tables = Table.get_all_tables()
    update_treeview(table_tree)

def print_fee(table_tree: ttk.Treeview):
    selected_item = table_tree.selection()
    if selected_item:
        item_values = table_tree.item(selected_item, 'values')
        table_name = item_values[0]

        selected_table = next((table for table in tables if table.name == table_name), None)
        if selected_table:
            feeFromDuration = selected_table.duration/60 * selected_table.feePerMinute
            feeFromDuration = round(feeFromDuration, 2)
            selected_table.fee = feeFromDuration + selected_table.feeFromCafe
            feemodel = Fee(selected_table.name, selected_table.fee, selected_table.duration)
            feemodel.save_to_db()

            utc_now = datetime.utcnow()
            utc_3 = utc_now + timedelta(hours=3)
            formatted_date = utc_3.strftime("%d/%m/%Y %H:%M:%S")
            tableData = [
                [formatted_date, "Tên Phí", "Số tiền"],
                ["", "Phí từ thời gian", feeFromDuration],
                ["", "Phí từ quán cà phê", selected_table.feeFromCafe],
                ["", "Tổng phí", selected_table.fee]
            ]

            invoice_name = "Hóa đơn-" + selected_table.name + ".pdf"
            docu = SimpleDocTemplate(invoice_name, pagesize=A4)

            styles = getSampleStyleSheet()

            doc_style = styles["Heading1"]
            doc_style.alignment = 1

            title = Paragraph("HÓA ĐƠN BÀN", doc_style)
            style = TableStyle([
                ("BOX", (0, 0), (-1, -1), 1, colors.black),
                ("GRID", (0, 0), (4, 4), 1, colors.chocolate),
                ("BACKGROUND", (0, 0), (3, 0), colors.skyblue),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
            ])
            table = ReportLabTable(tableData, style=style)
            docu.build([title, table])

#---------------------Phương thức Quản lý Mặt hàng Cà phê-----------------------------
def load_cafeitems_from_db(cafeitems_tree: ttk.Treeview):
    global cafeitems_array
    cafeitems_array = CafeItem.get_all_cafeitems()
    

def add_cafeitem_to_table(cafeitems_tree: ttk.Treeview, table_tree: ttk.Treeview):
    selected_cafeitem = cafeitems_tree.selection()
    if selected_cafeitem:
        # Lấy thông tin mặt hàng quán cà phê đã chọn
        cafeitem_values = cafeitems_tree.item(selected_cafeitem, 'values')
        cafeitem_cost = float(cafeitem_values[3])  # Giả sử giá là cột thứ tư

        # Mở một cửa sổ mới để lấy tên bàn
        table_window = tk.Toplevel()
        table_window.title("Thêm vào Bàn")
        table_window.configure(bg="#464646")

        ttk.Label(table_window, text="Tên Bàn:").grid(row=0, column=0)
        table_name_entry = ttk.Entry(table_window)
        table_name_entry.grid(row=0, column=1)

        submit_button = ttk.Button(table_window, text="Thêm", command=lambda: update_table_fee(table_name_entry.get(), cafeitem_cost, table_window, table_tree))
        submit_button.grid(row=1, column=1, pady=10)

def update_table_fee(table_name, cafeitem_cost, window, table_tree):
    selected_table = next((table for table in tables if table.name == table_name), None)
    if selected_table:
        selected_table.feeFromCafe += cafeitem_cost
        selected_table.update_db()
        update_treeview(table_tree)
        window.destroy()
    else:
        messagebox.showerror("Lỗi", "Không tìm thấy bàn với tên đã nhập.")

#---------------------Phương thức nạp tiền-----------------------------

def add_money(account_name, amount):
    selected_account = next((account for account in Account if account.name == account_name), None)
    if selected_account:
        try:
            amount = float(amount)
            selected_account.balance += amount
            selected_account.update_db()
            messagebox.showinfo("Thành công", f"Đã thêm {amount} vào tài khoản {account_name}.")
        except ValueError:
            messagebox.showerror("Lỗi", "Số tiền không hợp lệ.")
    else:
        messagebox.showerror("Lỗi", "Không tìm thấy tài khoản với tên đã nhập.")

def on_submit():
    account_name = account_entry.get()
    amount = amount_entry.get()
    add_money(account_name, amount)

root = tk.Tk()
root.title("Thêm tiền vào tài khoản")

account_label = tk.Label(root, text="Tên tài khoản:")
account_label.pack()
account_entry = tk.Entry(root)
account_entry.pack()

amount_label = tk.Label(root, text="Số tiền:")
amount_label.pack()
amount_entry = tk.Entry(root)
amount_entry.pack()

submit_button = tk.Button(root, text="Thêm tiền", command=on_submit)
submit_button.pack()


