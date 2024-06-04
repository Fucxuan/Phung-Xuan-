import tkinter as tk
from tkinter import *
from tkinter import ttk
from ttkthemes import ThemedTk

from controller.main_page_controller import *

def mainPage():
    #PHẦN THIẾT KẾ

    # Tạo cửa sổ chính
    app = ThemedTk(theme="equilux")
    app.title("VJU CYBER")
    app.geometry("1280x720")
    app.resizable(width=False, height=False)

    # Tạo một kiểu
    style = ttk.Style(app)
    style.configure('TLabel', foreground='white', font=("Roboto", 14))
    style.configure('TEntry', font=("Roboto", 14))
    style.configure('TButton', foreground='white', font=("Roboto", 14))
    style.configure('TNotebook.Tab', font=("Roboto", 14), padding=[10, 10], foreground='white')
    style.configure('Treeview', font=("Roboto", 14),rowheight=120, foreground="white")

    # Tạo một tab control (notebook)
    tab_control = ttk.Notebook(app)

    # Tạo các tab
    tab1 = ttk.Frame(tab_control)
    tab2 = ttk.Frame(tab_control)
    tab3 = ttk.Frame(tab_control)
    tab4 = ttk.Frame(tab_control)
    
    # Thêm các tab vào notebook
    tab_control.add(tab1, text='Trang Chính')
    tab_control.add(tab2, text='Menu Bàn')
    tab_control.add(tab3, text='Menu Quán Cà Phê')
    tab_control.add(tab4, text='nạp tiền')
    tab_control.pack(expand=1, fill='both')

    logo_image = tk.PhotoImage(file="assets/VJU (1).png")
    logo_label = ttk.Label(tab1, image=logo_image)
    logo_label.pack(pady=20)

    # Tạo một nhãn chào mừng
    last_registered_user = get_last_registered_user()
    welcome_message = f"Chào mừng {last_registered_user}!" if last_registered_user else "Chào mừng!"
    welcome_label = ttk.Label(tab1, text=welcome_message, style='TLabel')
    welcome_label.pack()

    style.configure("Red.TLabel", background="#373737", foreground="white", font=("Roboto", 12))

    # Khối Cập nhật
    update_frame = ttk.Frame(tab1)
    update_frame.pack(fill="both", expand=True, padx=20, pady=20)

    update_note = "Cập Nhật Gần Đây:\n\n- Cải thiện hiệu suất\n- Sửa lỗi\n- Thêm các tính năng mới\n- Nói chuyện khách hàng"
    update_label = ttk.Label(update_frame, text=update_note, style="Red.TLabel")
    update_label.pack(fill="x", anchor="n", padx=20, pady=20)

    # TAB MENU BÀN
    

    # Khung cho các nút
    button_frame = ttk.Frame(tab2)
    button_frame.pack(side=tk.LEFT, padx=10, pady=10, fill=tk.Y)
    
    # Nút Mở/Đóng Bàn 
    open_close_button = ttk.Button(button_frame, text="Mở/Đóng Bàn", command=lambda: toggle_open_close(table_tree))
    open_close_button.pack(pady=5)

    # Nút In Phí
    print_fee_button = ttk.Button(button_frame, text="In Phí", command=lambda: print_fee(table_tree))
    print_fee_button.pack(pady=5)


    # Treeview cho các bàn
    table_tree = ttk.Treeview(tab2, columns=('Name', 'Type', 'Fee per Minute', 'Duration', 'Total Fee', 'Open/Close'))
    table_tree.heading('#0', text='Hình Ảnh')
    table_tree.heading('Name', text='Tên')
    table_tree.heading('Type', text='Loại')
    table_tree.heading('Fee per Minute', text='Phí mỗi Phút')
    table_tree.heading('Duration', text='Thời Gian')  # Cột mới cho Thời Gian
    table_tree.heading('Total Fee', text='Tổng Phí')
    table_tree.heading('Open/Close', text='Mở/Đóng')
    table_tree.column('#0', stretch=tk.NO, width=140)
    table_tree.column('Name', stretch=tk.YES, width=100)
    table_tree.column('Type', stretch=tk.YES, width=100)
    table_tree.column('Fee per Minute', stretch=tk.YES, width=100)
    table_tree.column('Duration', stretch=tk.YES, width=100)  # Thiết lập chiều rộng cho Thời Gian
    table_tree.column('Total Fee', stretch=tk.YES, width=100)
    table_tree.column('Open/Close', stretch=tk.YES, width=100)
    table_tree.pack(fill='both', expand=True)


    # TAB MENU QUÁN CÀ PHÊ
    # Khung cho các nút
    button_frame = ttk.Frame(tab3)
    button_frame.pack(side=tk.LEFT, padx=10, pady=10, fill=tk.Y)

    
    # Nút Thêm Mặt Hàng Quán Cà Phê vào Bàn 
    add_cafeitem_to_table_button = ttk.Button(button_frame, text="Thêm Mặt Hàng Quán Cà Phê vào Bàn", command=lambda: add_cafeitem_to_table(cafeitems_tree, table_tree))
    add_cafeitem_to_table_button.pack(pady=5)


    # Treeview cho các mặt hàng quán cà phê
    cafeitems_tree = ttk.Treeview(tab3, columns=('Name', 'Type', 'Description','Cost'))
    cafeitems_tree.heading('#0', text='Hình Ảnh')
    cafeitems_tree.heading('Name', text='Tên')
    cafeitems_tree.heading('Type', text='Loại')
    cafeitems_tree.heading('Description', text='Mô tả')
    cafeitems_tree.heading('Cost', text='Giá')
    cafeitems_tree.column('#0', stretch=tk.NO, width=140)
    cafeitems_tree.column('Name', stretch=tk.YES, width=100)
    cafeitems_tree.column('Type', stretch=tk.YES, width=100)
    cafeitems_tree.column('Description', stretch=tk.YES, width=100)
    cafeitems_tree.column('Cost', stretch=tk.YES, width=100)
    cafeitems_tree.pack(fill='both', expand=True)

    # Tải các mặt hàng quán cà phê từ cơ sở dữ liệu
    load_cafeitems_from_db(cafeitems_tree)
    load_tables_from_db(table_tree)


    # TAB nạp tiền
    button_frame = ttk.Frame(tab4)
    button_frame.pack(side=tk.LEFT, padx=10, pady=10, fill=tk.Y)

    add_money_clint= ttk.Button(button_frame, text="nạp tiền ", command=lambda:add_money)
    add_money_clint.pack(pady=1)

    app.mainloop()
