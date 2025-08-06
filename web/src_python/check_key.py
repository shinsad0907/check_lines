from datetime import datetime
import base64
import os
import json
import supabase

base_url = "https://cgogqyorfzpxaiotscfp.supabase.co"
token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImNnb2dxeW9yZnpweGFpb3RzY2ZwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDc5ODMyMzcsImV4cCI6MjA2MzU1OTIzN30.enehR9wGHJf1xKO7d4XBbmjfdm80EvBKzaaPO3NPVAM'
supabase_client = supabase.create_client(base_url, token)

def decode(key):
    decoded = base64.urlsafe_b64decode(key.encode()).decode()
    data = json.loads(decoded)
    return data["secret"], data["user"], data["rand"]

def check_version(key, id_product, version_client):
    res = supabase_client.table("PRODUCTS").select("*").execute()
    for data in res.data:
        if data['id'] == id_product:
            return data['version_client'] == version_client
    return False

def get_mac():
    import psutil
    for interface, addrs in psutil.net_if_addrs().items():
        for addr in addrs:
            if addr.family.name == 'AF_LINK':
                mac = addr.address
                if mac and mac != '00:00:00:00:00:00' and not interface.lower().startswith(('lo', 'vir', 'vm', 'docker')):
                    return mac
    return None

def check_key(key, version_client=''):
    try:
        secret, user_id, rand = decode(key)
    except Exception:
        return {"status": False, "message": "Key không hợp lệ (decode lỗi)!"}
    
    res = supabase_client.table("data_user").select("*").execute()
    today = datetime.today().date()
    
    for data in res.data:
        if data['username'] == user_id:
            purchases = data['purchases']
            uid_mac = data['ip_mac']
            for data_purchase in purchases:
                if data_purchase['key'] == key:
                    date_key_part = data_purchase.get('date_key_part')
                    id_product = data_purchase.get('product_id')
                    
            
                    if not date_key_part:
                        return {"status": False, "message": "Không tìm thấy ngày hết hạn trong key!"}
                    
                    try:
                        expire_date = datetime.strptime(date_key_part, "%Y-%m-%d").date()
                    except Exception:
                        return {"status": False, "message": f"Không đọc được ngày hết hạn! (Giá trị: {date_key_part})"}
                    
                    if expire_date < today:
                        return {"status": False, "message": "Key đã hết hạn sử dụng!"}
                    
                    if check_version(key, id_product, version_client):
                        current_mac = get_mac()
                        if uid_mac is None:
                            supabase_client.table("data_user").update({"ip_mac": current_mac}).eq("username", user_id).execute()
                            return {"status": True, "message": "Key đã được kích hoạt thành công!"}
                        elif uid_mac == current_mac:
                            return {"status": True, "message": "Key đã được kích hoạt thành công!"}
                        else:
                            return {"status": False, "message": "Key đã được kích hoạt trên thiết bị khác!"}
                    else:
                        return {"status": False, "message": "Phiên bản client không tương thích với key!"}
    
    return {"status": False, "message": "Key không hợp lệ!"}

# def get_or_create_key():
#     key_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), r"data/key.json")
#     key = None
    
#     if os.path.exists(key_path):
#         try:
#             with open(key_path, "r", encoding="utf-8") as f:
#                 data = json.load(f)
#                 key = data.get("key")
#             result = check_key(key)
#             if result["status"]:
#                 return key
#             else:
#                 os.remove(key_path)
#                 return None
#         except Exception:
#             key = None
    
#     return None  # Key not found or invalid, return None for further processing

