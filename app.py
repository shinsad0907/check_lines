import eel
import time
import threading
import json
from web.src_python.change_pass import thread
from web.src_python.scan_friend import thread_scan_friend
import os
from web.src_python.check_key import check_key
from web.src_python.get2fa import start_2fa_process
from web.src_python.add_mail import add_mail_process
import tkinter as tk
from tkinter import filedialog
import datetime



eel.init('web')  # Folder chứa file HTML
KEY_FILE = r'data/key.json'
VERSION_CLIENT_PATH = r'data/version_client.json'

@eel.expose
def save_config_json(data):
    try:
        print("Dữ liệu nhận được:", data)
        with open(r'data\config_change_pass.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        return True
    except Exception as e:
        print("Lỗi khi lưu file:", e)
        return False

@eel.expose
def start_change_password_process(data):
    start_2fa_process(data)

@eel.expose
def start_scan_friend_process(data):
    thread_scan_friend(data)

@eel.expose
def start_get_2fa_process(data):
    start_2fa_process(data)

@eel.expose
def run_add_mail(data):
    add_mail_process(data)

def is_key_activated():
    if not os.path.exists(KEY_FILE):
        return {"status": False, "message": "Chưa kích hoạt key!"}
    try:
        with open(KEY_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        with open(VERSION_CLIENT_PATH, 'r', encoding='utf-8-sig') as f:
            version_client_data = json.load(f)
        data_check_key = check_key(data.get("key", ""),version_client_data.get('version_client', ''))
        return data_check_key
    except Exception as e:
        return {"status": False, "message": f"Lỗi kiểm tra key: {e}"}

@eel.expose
def check_activation_key(key):
    with open(VERSION_CLIENT_PATH, 'r', encoding='utf-8-sig') as f:
        version_client_data = json.load(f)
    data_check_key = check_key(key,version_client_data.get('version_client', ''))
    if data_check_key["status"]:
        os.makedirs('data', exist_ok=True)
        with open(KEY_FILE, 'w', encoding='utf-8') as f:
            json.dump({"activated": True, "key": key}, f)
    return data_check_key

@eel.expose
def reload_main():
    eel.start('index.html', size=(1400, 900), block=False)
@eel.expose
def save_exported_accounts(lines):
    print("Lưu danh sách tài khoản vào file...")
    try:
        # Tạo tên file mặc định
        now = time.localtime()
        file_name = time.strftime("export_%Y-%m-%d_%H-%M-%S.txt", now)

        # Mở hộp thoại chọn nơi lưu
        root = tk.Tk()
        root.withdraw()
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt")],
            initialfile=file_name,
            title="Chọn nơi lưu file xuất"
        )
        root.destroy()
        if not file_path:
            return {"success": False, "cancelled": True}

        # Ghi file
        with open(file_path, "w", encoding="utf-8") as f:
            f.write('\n'.join(lines))
        return {"success": True}
    except Exception as e:
        print("Lỗi khi lưu file export:", e)
        return {"success": False}
    
@eel.expose
def get_key_info():
    try:
        import datetime
        from supabase import create_client

        # Đọc key từ file
        with open('data/key.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        with open('data/config.json', 'r', encoding='utf-8') as f:
            config_data = json.load(f)
        id_config = config_data.get("id", "")
        key = data.get("key", "")
        print(f"Key: {key}, ID Config: {id_config}")
        # Nếu không có key thì trả về luôn
        if not key:
            return {"key": "", "expiry": "Chưa có key"}

        # Kết nối Supabase
        base_url = "https://cgogqyorfzpxaiotscfp.supabase.co"
        token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImNnb2dxeW9yZnpweGFpb3RzY2ZwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDc5ODMyMzcsImV4cCI6MjA2MzU1OTIzN30.enehR9wGHJf1xKO7d4XBbmjfdm80EvBKzaaPO3NPVAM'
        supabase = create_client(base_url, token)
        res = supabase.table("data_user").select("*").execute()

        # Kiểm tra response
        if not res or not hasattr(res, 'data') or not isinstance(res.data, list) or not res.data:
            return {"key": key, "expiry": "Không có dữ liệu"}

        # Tìm key trong purchases
        for user in res.data:
            purchases = user.get('purchases', [])
            if not isinstance(purchases, list):
                continue
            for purchase in purchases:
                if int(purchase['product_id']) == int(id_config) :
                    expire_date = purchase.get('date_key_part')
                    if expire_date:
                        try:
                            expiry = datetime.datetime.strptime(expire_date, "%Y-%m-%d").date()
                            days_left = (expiry - datetime.datetime.now().date()).days
                            if days_left < 0:
                                return {"key": key, "expiry": "Đã hết hạn"}
                            return {"key": key, "expiry": f"{days_left} ngày"}
                        except Exception:
                            return {"key": key, "expiry": "Ngày không hợp lệ"}
        return {"key": key, "expiry": "Key không hợp lệ"}
    except Exception as e:
        return {"key": key, "expiry": f"Lỗi: {e}"}

if __name__ == '__main__':
    result = is_key_activated()
    if result.get("status"):
        eel.start('index.html', size=(1400, 900))
    else:
        eel.start('key.html', size=(500, 320))