import eel
import time
import threading
import json
from web.src_python.change_pass import thread
from web.src_python.get2fa import start_2fa_process   # Import the correct function
import os
from web.src_python.check_key import check_key
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
    thread(data)


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

if __name__ == '__main__':
    result = is_key_activated()
    if result.get("status"):
        eel.start('index.html', size=(1400, 900))
    else:
        eel.start('key.html', size=(500, 320))