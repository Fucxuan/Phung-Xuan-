import threading
import time
import sqlite3
from datetime import datetime, timedelta
import socket


import tkinter as tk
from tkinter import ttk, filedialog, messagebox, Tk
from PIL import Image, ImageTk, ImageOps

from reportlab.platypus import SimpleDocTemplate, Paragraph, TableStyle
from reportlab.platypus import Table as ReportLabTable
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet

from model.table import Table
from model.cafeitem import CafeItem
from model.client import Client
from model.fee import Fee

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
def upload_image(label):
    root = Tk()
    root.withdraw()  # Ẩn cửa sổ gốc
    file_path = filedialog.askopenfilename(filetypes=[("Image Files", ".png .jpg .jpeg .gif")])
    root.destroy()  # Hủy cửa sổ gốc

    if file_path:
        label.config(text=file_path)

def save_table(name, type, fee, image_path, window, table_tree):
    try:
        fee = int(fee)
        new_table = Table(name, type, False, fee, 0, 0, 0, image_path, 0)
        new_table.save_to_db()
        tables.append(new_table)
        print("BÀN", tables)
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
        print("BÀN", table)
        open_close_status = "Mở" if table.open_close else "Đóng"
        if table.image_path:
            img = Image.open(table.image_path)
            img = img.convert("RGBA")  # Đảm bảo hình ảnh ở định dạng RGBA

            # Thay đổi kích thước và bảo toàn độ trong suốt
            img = ImageOps.fit(img, (100, 100), Image.Resampling.LANCZOS)
            
            photo = ImageTk.PhotoImage(img)
            image_refs[table.name] = photo
            table_tree.insert('', 'end', image=photo, values=(table.name, table.type, table.feePerMinute, table.duration/60, table.fee, open_close_status))
            print("BÀN-Hình", tables)
        else:
            table_tree.insert('', 'end', values=(table.name, table.type, table.feePerMinute, table.duration/60, table.fee, open_close_status))
            print("BÀN-Không hình", tables)


def delete_selected_table(table_tree: ttk.Treeview):
    selected_item = table_tree.selection()
    if selected_item:
        # Lấy tên bàn từ mục đã chọn
        item_values = table_tree.item(selected_item, 'values')
        table_name = item_values[0]  # Giả sử giá trị đầu tiên là tên

        # Xóa mục đã chọn khỏi treeview
        table_tree.delete(selected_item)

        # Xóa đối tượng bàn tương ứng từ cơ sở dữ liệu
        Table.delete_table(table_name)
        tables.pop([table.name for table in tables].index(table_name))  # Xóa đối tượng bàn khỏi danh sách 'tables'

def customize_window(table, table_tree: ttk.Treeview):
    # Tạo một cửa sổ mới
    customization_window = tk.Toplevel()
    customization_window.title("Tùy chỉnh bàn")

    customization_window.configure(bg="#464646")

    # Trường nhập loại
    ttk.Label(customization_window, text="Loại").grid(row=0, column=0)
    type_entry = ttk.Entry(customization_window)
    type_entry.grid(row=0, column=1)
    type_entry.insert(0, table.type)

    # Trường nhập phí
    ttk.Label(customization_window, text="Giá tiền 1 phút").grid(row=1, column=0)
    fee_entry = ttk.Entry(customization_window)
    fee_entry.grid(row=1, column=1)
    fee_entry.insert(0, table.feePerMinute)

    # Nút gửi
    submit_button = ttk.Button(customization_window, text="Cập nhật", command=lambda: update_table(customization_window, table, type_entry.get(), fee_entry.get(), table_tree))
    submit_button.grid(row=2, column=1)

def open_customize_window(table_tree: ttk.Treeview):
    selected_item = table_tree.selection()
    if selected_item:
        item_values = table_tree.item(selected_item, 'values')
        table_name = item_values[0]

        # Tìm đối tượng bàn đã chọn
        selected_table = next((table for table in tables if table.name == table_name), None)
        if selected_table:
            customize_window(selected_table, table_tree)

def update_table(window, table, new_type, new_fee, table_tree: ttk.Treeview):
    try:
        new_fee = int(new_fee)
        table.type = new_type
        table.feePerMinute = new_fee
        new_table = Table(table.name, new_type, table.open_close, new_fee, table.image_path)
        new_table.update_db()
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
                print("Mở")
            else:
                # Nếu bàn đang đóng, dừng đếm thời gian, tính tổng phí và loại bỏ màu xanh
                stop_timer(selected_table, table_tree)
                print("Đóng")
 
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


def reset_table(table_tree: ttk.Treeview):
    selected_item = table_tree.selection()
    if selected_item:
        item_values = table_tree.item(selected_item, 'values')
        table_name = item_values[0]

        selected_table = next((table for table in tables if table.name == table_name), None)
        if selected_table:
            selected_table.duration = 0
            selected_table.fee = 0
            selected_table.feeFromCafe = 0 
            selected_table.feeFromDuration = 0 
            update_treeview(table_tree)

def load_tables_from_db(table_tree: ttk.Treeview):
    print("Đang tải bàn từ cơ sở dữ liệu...")
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
            print("Khoảng thời gian: ", selected_table.duration)
            print("Phí khoản thời gian: ", feeFromDuration)
            print("Gía nước: ", selected_table.feeFromCafe)
            print("Tổng: ", selected_table.fee)
            feemodel = Fee(selected_table.name, selected_table.fee, selected_table.duration)
            feemodel.save_to_db()


    # Dữ liệu mà chúng ta sẽ hiển thị dưới dạng bảng
    utc_now = datetime.utcnow()
    utc_3 = utc_now + timedelta(hours=3)
    formatted_date = utc_3.strftime("%d/%m/%Y %H:%M:%S")
    tableData = [

    [formatted_date, "Tên Phí", "Số tiền"],
        ["", "Phí từ thời gian", feeFromDuration],
        ["", "Phí từ quán cà phê", selected_table.feeFromCafe],
        ["", "Tổng phí", selected_table.fee]
    ]
    # Tạo một cấu trúc Tài liệu với kích thước trang A4
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
    print("Đang tải mặt hàng quán cà phê từ cơ sở dữ liệu...")
    global cafeitems_array
    cafeitems_array = CafeItem.get_all_cafeitems()
    print("MẢNG MẶT HÀNG CÀ PHÊ", cafeitems_array)
    update_cafeitems_treeview(cafeitems_tree)


def save_cafeitem(name, cafeitem_type, description, cost, image_path, window, cafeitems_tree):
    try:
        cost = float(cost)
        new_cafeitem = CafeItem(name, cafeitem_type, cost, description, image_path)
        new_cafeitem.save_to_db()
        cafeitems_array.append(new_cafeitem)
        update_cafeitems_treeview(cafeitems_tree)
        window.destroy()
    except ValueError:
        messagebox.showerror("Lỗi", "Dữ liệu phí không hợp lệ. Vui lòng nhập một số hợp lệ.")


def customize_cafeitem_window(cafeitem: CafeItem, cafeitems_tree: ttk.Treeview):
    customization_window = tk.Toplevel()
    customization_window.title("Tùy chỉnh Mặt hàng Quán cà phê")
    customization_window.configure(bg="#464646")
    # Trường loại
    ttk.Label(customization_window, text="Loại:").grid(row=0, column=0)
    type_entry = ttk.Entry(customization_window)
    type_entry.grid(row=0, column=1)
    type_entry.insert(0, cafeitem.type)

    # Trường phí
    ttk.Label(customization_window, text="Giá:").grid(row=1, column=0)
    cost_entry = ttk.Entry(customization_window)
    cost_entry.grid(row=1, column=1)
    cost_entry.insert(0, cafeitem.cost)

    # Trường mô tả
    ttk.Label(customization_window, text="Mô tả:").grid(row=2, column=0)
    description_entry = ttk.Entry(customization_window)
    description_entry.grid(row=2, column=1)
    description_entry.insert(tk.END, cafeitem.description)

    # Nút gửi
    submit_button = ttk.Button(customization_window, text="Cập nhật Mặt hàng Quán cà phê", command=lambda: update_cafeitem(cafeitem, type_entry.get(), cost_entry.get(), description_entry.get(), customization_window, cafeitems_tree))
    submit_button.grid(row=3, column=1, pady=10)

def update_cafeitem(cafeitem, new_type, new_cost, new_description, window, cafeitems_tree):
    try:
        new_cost = float(new_cost)
        cafeitem.type = new_type
        cafeitem.cost = new_cost
        cafeitem.description = new_description
        CafeItem.update_cafeitem(cafeitem.name, new_type, new_cost, new_description, cafeitem.image_path)
        update_cafeitems_treeview(cafeitems_tree)
        window.destroy()
    except ValueError:
        messagebox.showerror("Lỗi", "Dữ liệu phí không hợp lệ. Vui lòng nhập một số hợp lệ.")


cafeitem_image_refs = {}

def update_cafeitems_treeview(cafeitems_tree: ttk.Treeview):
    global cafeitem_image_refs
    cafeitem_image_refs.clear()  # Xóa các tham chiếu hình ảnh hiện có

    for i in cafeitems_tree.get_children():
        cafeitems_tree.delete(i)  # Xóa treeview

    for item in cafeitems_array:
        print("MẶT HÀNG", item)
        if item.image_path:
            # Tải và thay đổi kích thước hình ảnh
            img = Image.open(item.image_path)
            img = img.resize((100, 100), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            cafeitem_image_refs[item.name] = photo  # Lưu tham chiếu đến hình ảnh
            cafeitems_tree.insert('', 'end', image=photo, values=(item.name, item.type, item.description, item.cost))
        else:
            cafeitems_tree.insert('', 'end', values=(item.name, item.type, item.description, item.cost))

def delete_selected_cafeitem(cafeitems_tree: ttk.Treeview):
    selected_item = cafeitems_tree.selection()
    if selected_item:
        item_values = cafeitems_tree.item(selected_item, 'values')
        cafeitem_name = item_values[0]

        # Xóa mục đã chọn khỏi treeview
        cafeitems_tree.delete(selected_item)

        # Xóa mặt hàng quán cà phê tương ứng từ danh sách 'cafeitems'
        CafeItem.delete_cafeitem(cafeitem_name)
        cafeitems_array.pop([item.name for item in cafeitems_array].index(cafeitem_name))  # Xóa đối tượng mặt hàng quán cà phê từ danh sách 'cafeitems'

def open_customize_cafeitem_window(cafeitems_tree: ttk.Treeview):
    selected_item = cafeitems_tree.selection()
    if selected_item:
        item_values = cafeitems_tree.item(selected_item, 'values')
        cafeitem_name = item_values[0]

        # Tìm đối tượng mặt hàng quán cà phê đã chọn
        selected_cafeitem = next((item for item in cafeitems_array if item.name == cafeitem_name), None)
        if selected_cafeitem:
            customize_cafeitem_window(selected_cafeitem, cafeitems_tree)


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

        submit_button = ttk.Button(table_window, text="Thêm", command=lambda: update_table_fee(table_name_entry.get(), cafeitem_cost, table_window,table_tree))
        submit_button.grid(row=1, column=1, pady=10)

def update_table_fee(table_name, cafeitem_cost, window, table_tree):
    for table in tables:
        if table.name == table_name:
            table.feeFromCafe += cafeitem_cost
            table.fee = table.feeFromCafe + table.feeFromDuration
            print("PHÍ BÀN", table.fee)
            update_treeview(table_tree)  # Cập nhật treeview trong tab Quản lý Bàn
            break
    window.destroy()
#---------------------Quản lý khách hàng khách hàng--------------------------------------------------

def connect_to_server(self):
    server_host = 'localhost'  # Địa chỉ IP hoặc tên miền của máy chủ
    server_port = 12345        # Cổng của máy chủ

    self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        self.client_socket.connect((server_host, server_port))
        self.text_area.insert(tk.END, "Đã kết nối đến máy chủ.\n")
        threading.Thread(target=self.receive_messages).start()
    except Exception as e:
        self.text_area.insert(tk.END, f"Lỗi khi kết nối đến máy chủ: {str(e)}\n")
def load_client_from_db(client_tree: ttk.Treeview):
    print("Đang tải bàn từ cơ sở dữ liệu...")
    global clients
    clients = Client.get_all_client()
    update_treeview(client_tree)

def delete_selected_client(client_tree: ttk.Treeview):
    selected_item = client_tree.selection()
    if selected_item:
        # Lấy tên bàn từ mục đã chọn
        item_values = client_tree.item(selected_item, 'values')
        table_client = item_values[0]  # Giả sử giá trị đầu tiên là tên

        # Xóa mục đã chọn khỏi treeview
        client_tree.delete(selected_item)

        # Xóa đối tượng bàn tương ứng từ cơ sở dữ liệu
        Client.delete_table(table_client)
        clients.pop([table.name for table in clients].index(table_client))  # Xóa đối tượng bàn khỏi danh sách 'clients'
def update_client(client_window, client, new_name, new_age, new_CCCD,client_tree: ttk.Treeview):
    try:
        client.name = new_name
        client.age = new_age
        client.CCCD = new_CCCD
        new_client = Client(client.name, new_age, new_CCCD)
        new_client.update_db()
        update_treeview(client_tree)  # Làm mới cây
        client_window.destroy()
    except ValueError:
        messagebox.showerror("Lỗi", "Dữ liệu phí không hợp lệ. Vui lòng nhập một số hợp lệ.")
      
def save_client(name, age, CCCD, client_tree, client_window):
    try:
        new_client = Client(name, age, CCCD)
        new_client.save_to_db()
        clients.append(new_client)
        print("KHÁCH HÀNG", clients)
        update_treeview(client_tree)
        client_window.destroy()
    except ValueError:
        messagebox.showerror("Lỗi", "Dữ liệu không hợp lệ ở một hoặc nhiều trường")

def customize_client(client, client_tree: ttk.Treeview):
    # Tạo một cửa sổ mới
    customization_client = tk.Toplevel()
    customization_client.title("Tùy chỉnh tài khoản khách hàng")

    customization_client.configure(bg="#464646")

    # Trường nhập name
    ttk.Label(customization_client, text="tên").grid(row=0, column=0)
    name_entry = ttk.Entry(customization_client)
    name_entry.grid(row=0, column=1)
    name_entry.insert(0, client.name)
    
    # Trường nhập age
    ttk.Label(customization_client, text="tuổi").grid(row=0, column=0)
    age_entry = ttk.Entry(customization_client)
    age_entry.grid(row=0, column=1)
    age_entry.insert(0, client.age)

    # Trường nhập CCCD
    ttk.Label(customization_client, text="CCCD").grid(row=1, column=0)
    CCCD_entry = ttk.Entry(customization_client)
    CCCD_entry.grid(row=1, column=1)
    CCCD_entry.insert(0, client.CCCD)

    # Nút gửi
    submit_button = ttk.Button(customization_client, text="Cập nhật", command=lambda: update_client(customization_client,  name_entry.get(), age_entry.get(),CCCD_entry.get(), client_tree))
    submit_button.grid(row=2, column=1)

