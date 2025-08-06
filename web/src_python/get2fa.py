# Thêm biến để quản lý trạng thái scanning
import threading
import time
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import requests
import eel
from typing import Dict, List
import tempfile
import shutil


# Khởi tạo biến để kiểm soát luồng
chrome_drivers = {}
is_running = False
thread_lock = threading.Lock()
active_threads = []  # Thêm list để theo dõi các thread đang chạy

# Hàm chuyển cookie string thành danh sách dict
def convert_cookie_string_to_list(cookie_str):
    cookies = []
    for part in cookie_str.split(';'):
        if '=' in part:
            name, value = part.strip().split('=', 1)
            cookies.append({'name': name.strip(), 'value': value.strip()})
    return cookies

def get_cookie_value(cookies_list, key):
    for cookie in cookies_list:
        if cookie['name'] == key:
            return cookie['value']
    return None

class Get2FA:
    def __init__(self, window_index):
        self.window_index = window_index
        self.driver = None
        self.setup_driver()
        
    def setup_driver(self):
        try:
            profile_path = os.path.join(tempfile.gettempdir(), f"chrome_profile_{self.window_index}")
            if os.path.exists(profile_path):
                shutil.rmtree(profile_path)
                print(f"Deleted existing Chrome profile: {profile_path}")
        except Exception as e:
            print(f"Error deleting existing Chrome profile: {e}")
        options = Options()
        
        # Tắt các tính năng phát hiện automation
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        # Fake User Agent thực tế
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36 Edg/135.0.0.0",
        ]
        import random
        # options.add_argument(f"--user-agent={random.choice(user_agents)}")
        
        # Tạo profile người dùng riêng (quan trọng!)
        # import os
        # profile_path = os.path.join(tempfile.gettempdir(), f"chrome_profile_{self.window_index}")
        # options.add_argument(f"--user-data-dir={profile_path}")
        
        # Các tùy chọn để giả lập trình duyệt thực
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-software-rasterizer")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-plugins")
        options.add_argument("--disable-images")  # Tắt hình ảnh để tăng tốc
        options.add_argument("--disable-javascript")  # Có thể bỏ nếu cần JS
        options.add_argument("--window-size=400,600")
        
        # Fake thêm thông tin trình duyệt
        options.add_argument("--disable-default-apps")
        options.add_argument("--no-first-run")
        options.add_argument("--disable-sync")
        options.add_argument("--disable-background-timer-throttling")
        options.add_argument("--disable-backgrounding-occluded-windows")
        options.add_argument("--disable-renderer-backgrounding")
        options.add_argument("--disable-features=TranslateUI")
        options.add_argument("--lang=pl-PL")
        
        # Cấu hình preferences chi tiết
        prefs = {
            "profile.default_content_setting_values": {
                "notifications": 2,
                "media_stream": 2,
                "geolocation": 2
            },
            "credentials_enable_service": False,
            "profile.password_manager_enabled": False,
            "profile.default_content_settings.popups": 0,
            "managed_default_content_settings.images": 2,
            "profile.managed_default_content_settings.media_stream": 2,
            # Thêm các tùy chọn mới để xóa dữ liệu
            "profile.clear_data": {
                "browsing_history": True,
                "download_history": True,
                "passwords": True,
                "form_data": True,
                "cache": True,
                "cookies": True
            },
            "profile.clear_data_on_exit": True,
            "profile.default_content_settings.cookies": 2,
            "profile.exit_type": "Normal"
        }
        options.add_experimental_option("prefs", prefs)
        
        # Tính toán vị trí cửa sổ
        SCREEN_WIDTH = 1920
        SCREEN_HEIGHT = 1080
        WINDOW_WIDTH = 400
        WINDOW_HEIGHT = 600
        
        COLUMNS = SCREEN_WIDTH // WINDOW_WIDTH
        ROWS = SCREEN_HEIGHT // WINDOW_HEIGHT
        
        row = self.window_index // COLUMNS
        col = self.window_index % COLUMNS
        
        if row >= ROWS:
            row = row % ROWS
        
        x = col * WINDOW_WIDTH
        y = row * WINDOW_HEIGHT
        
        if x + WINDOW_WIDTH > SCREEN_WIDTH:
            x = SCREEN_WIDTH - WINDOW_WIDTH
        if y + WINDOW_HEIGHT > SCREEN_HEIGHT:
            y = SCREEN_HEIGHT - WINDOW_HEIGHT
        
        print(f"Tạo cửa sổ {self.window_index} tại vị trí ({x}, {y})")
        
  
        self.driver = webdriver.Chrome(options=options)
        
        # Thiết lập vị trí và kích thước
        self.driver.set_window_position(x, y)
        self.driver.set_window_size(WINDOW_WIDTH, WINDOW_HEIGHT)
        
        # Script để ẩn dấu hiệu WebDriver (QUAN TRỌNG!)
        self.driver.execute_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
            });
            
            // Fake chrome object
            window.chrome = {
                runtime: {},
                loadTimes: function() {},
                csi: function() {},
                app: {}
            };
            
            // Fake plugins
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5],
            });
            
            // Fake languages
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en'],
            });
            
            // Fake permissions
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                Promise.resolve({ state: Notification.permission }) :
                originalQuery(parameters)
            );
        """)
        
        # Thêm delay và random behavior
        time.sleep(random.uniform(1, 3))
        
        # Đi đến Facebook với delay tự nhiên
        self.driver.get("https://www.facebook.com")
        time.sleep(random.uniform(2, 4))
      
    def meta_2FA(self,account):
        self.driver.get("https://auth.meta.com/")
        self.wait_and_click("/html/body/div[3]/div[1]/div/div[2]/div/div/div/div/div/div/div[4]/div/div/div/div/div/div[1]/div[2]/div/div")
        self.wait_and_click("/html/body/div[1]/div/div/div/div/div/div/div[1]/div[1]/div/div[1]/div/div[2]/div[1]/div/div/div/div/div[2]/div/div/div")
        self.wait_and_click("/html/body/div[1]/div/div/div/div/div/div/div[1]/div[1]/div/div[2]/div/div/div/div[2]/div/div[1]/div[1]/div/div")
        self.wait_and_click("/html/body/div[1]/div/div/div/div/div/div/div[1]/div[1]/div/div/div[1]/div[2]/div/div/div[4]/label/div[1]/input")
        self.wait_and_click("/html/body/div[1]/div/div/div/div/div/div/div[1]/div[1]/div/div/div[1]/div[3]/div/div/div[2]/div/div[1]/div[1]/div/div")
        eel.update2FAResult(account['uid'], "meta", "✅ Thành công tạo meta")()
        error_xpath_options = [
            "/html/body/div/div[2]/div/div[2]/main/h2",
            "/html/body/div/div[2]/div/div[2]/main/div/div/div[1]/div/div/div[1]/div/div[1]/span",
        ]
        
        # Try each xpath until we find text or run out of options
        for xpath in error_xpath_options:
            check = self.wait_and_get_text(xpath, timeout=5)
            eel.update2FAResult(account['uid'], "meta", "✅ Thành công tạo meta")()
            self.driver.get("https://accountscenter.facebook.com/password_and_security")
            # if self.check_login(account):
            #     print("Login check passed, continuing...")
            # else:
            #     print("Login check failed, stopping process")
            #     if self.driver:
            #         self.driver.quit()
            #         self.driver = None
            #     return False
            
            # Thử các xpath khác nhau để click vào 2FA settings
            click_success = False
            xpath_options = [
                "/html/body/div[1]/div/div/div/div/div[1]/div/div/div[1]/div[1]/div/div[1]/div[1]/div[2]/div/div/div/div[2]/div/main/div/div/div[2]/div[1]/div[2]/div/div/div[2]/div/div[1]",
                "/html/body/div[1]/div/div/div/div[1]/div/div/div[1]/div[1]/div/div[1]/div[1]/div[2]/div/div/div/div[2]/div/main/div/div/div[2]/div[1]/div[2]/div/div/div[2]/div/div[1]"
            ]
            
            for xpath in xpath_options:
                try:
                    # Kiểm tra flag dừng
                    with thread_lock:
                        if not is_running:
                            print(f"Thread bị dừng, bỏ qua account: {account['uid']}")
                            return False
                    
                    self.wait_and_click(xpath, timeout=5)
                    click_success = True
                    break
                except:
                    continue
            
            # Thử các xpath để setup 2FA
            setup_xpath_options = [
                "/html/body/div[1]/div/div/div/div/div[3]/div/div/div[2]/div/div/div/div/div/div/div/div[4]/div[2]/div[1]/div/div/div[2]/div/div/div[1]",
                "/html/body/div[1]/div/div/div/div/div[3]/div/div/div[2]/div/div/div/div/div/div/div/div[4]/div[2]/div[1]/div/div/div[2]/div/div[1]/div[1]",
                "/html/body/div[1]/div/div/div/div[3]/div/div/div[2]/div/div/div/div/div/div[2]/div/div[5]/div/div/div/div/div/div/div/div/div",
                "/html/body/div[1]/div/div/div/div[3]/div/div/div[2]/div/div/div/div/div/div[1]/div/div[4]/div[2]/div[1]/div/div/div[2]/div/div/div[1]/div",
            ]
            
            setup_success = False
            for xpath in setup_xpath_options:
                try:
                    # Kiểm tra flag dừng
                    with thread_lock:
                        if not is_running:
                            print(f"Thread bị dừng, bỏ qua account: {account['uid']}")
                            return False
                    
                    self.wait_and_click(xpath, timeout=5)
                    
                    # Check for error messages after clicking setup button
                    if not self.check_code(account):
                        print(f"Lỗi xác thực cho {account['uid']}, bỏ qua account này")
                        return False  # Return false to stop processing this account
                    
                    setup_success = True
                    break
                except:
                    continue

            print("Không thể setup 2FA, thử lại...")
        
            # Click để tiếp tục setup
            continue_xpath_options = [
                "/html/body/div[1]/div/div/div/div/div[3]/div/div/div[2]/div/div/div/div/div/div[2]/div/div[5]/div/div/div/div/div/div/div/div",
                "/html/body/div[1]/div/div/div/div/div[3]/div/div/div[2]/div/div/div/div/div/div[2]/div/div[3]/div/div/div/div/div/div/div/div/div",
                "/html/body/div[1]/div/div/div/div/div[3]/div/div/div[2]/div/div/div/div/div/div[2]/div/div[2]/div/div/div/div/div/div/div/div/div",
                "/html/body/div[1]/div/div/div/div/div[3]/div/div/div[2]/div/div/div/div/div/div[2]/div/div[4]/div/div/div/div/div/div/div/div/div",
                "/html/body/div[1]/div/div/div/div/div[3]/div/div/div[2]/div/div/div/div/div/div[2]/div/div[5]/div/div/div/div/div/div/div/div/div",
            ]
            
            for xpath in continue_xpath_options:
                try:
                    # Kiểm tra flag dừng
                    with thread_lock:
                        if not is_running:
                            print(f"Thread bị dừng, bỏ qua account: {account['uid']}")
                            return False
                    
                    self.wait_and_click(xpath, timeout=5)
                    break
                except:
                    continue
            
            time.sleep(10)
            # Lấy mã 2FA
            ma_2fa = self.wait_and_get_text("/html/body/div[1]/div/div/div/div/div[3]/div/div/div[2]/div/div/div/div/div/div[3]/div/div[4]/div[2]/div[1]/div/div/div[4]/div[2]/div/div/div/div[1]/span")
            if not ma_2fa:
                raise Exception("Không thể lấy mã 2FA")
            
            print(f"Đã lấy mã 2FA: {ma_2fa}")
            eel.update2FAResult(account['uid'], ma_2fa, "⏳ Đang xử lý...")()
            
            # Lấy code từ API
            code_2fa = self.get_code_2fa(ma_2fa)
            if not code_2fa:
                raise Exception("Không thể lấy code 2FA từ API")
            
            # Kiểm tra flag dừng
            with thread_lock:
                if not is_running:
                    print(f"Thread bị dừng, bỏ qua account: {account['uid']}")
                    return False
            
            # Click tiếp tục
            self.wait_and_click("/html/body/div[1]/div/div/div/div/div[3]/div/div/div[2]/div/div/div/div/div/div[3]/div/div[5]/div/div/div/div/div/div/div/div/div")
            # Nhập code 2FA
            self.wait_and_send_keys("/html/body/div[1]/div/div/div/div/div[3]/div/div/div[2]/div/div/div/div/div/div[4]/div/div[4]/div[2]/div[1]/div/div/div[2]/div/div/div[1]/input", code_2fa)
            # Click xác nhận
            self.wait_and_click("/html/body/div[1]/div/div/div/div/div[3]/div/div/div[2]/div/div/div/div/div/div[4]/div/div[5]/div/div/div/div/div/div/div/div/div")
            # Nhập password để xác nhận
            eel.update2FAResult(account['uid'], ma_2fa, "✅ Thành công")()
            password_xpath_options = [
                "/html/body/div[6]/div[1]/div/div[2]/div/div/div/div/div/div/div[4]/div[2]/div[1]/div/div/div[3]/div/div/div/div[1]/input",
                "/html/body/div[7]/div[1]/div/div[2]/div/div/div/div/div/div/div[4]/div[2]/div[1]/div/div/div[3]/div/div/div/div[1]/input",
                "/html/body/div[8]/div[1]/div/div[2]/div/div/div/div/div/div/div[4]/div[2]/div[1]/div/div/div[3]/div/div/div/div[1]/input",
                "/html/body/div[9]/div[1]/div/div[2]/div/div/div/div/div/div/div[4]/div[2]/div[1]/div/div/div[3]/div/div/div/div[1]/input",
            ]
            
            password_entered = False
            for xpath in password_xpath_options:
                try:
                    # Kiểm tra flag dừng
                    with thread_lock:
                        if not is_running:
                            print(f"Thread bị dừng, bỏ qua account: {account['uid']}")
                            return False
                    
                    self.wait_and_send_keys(xpath, account['pass'], timeout=5)
                    password_entered = True
                    break
                except:
                    continue
            
            if not password_entered:
                raise Exception("Không thể nhập password")
            
            # Click xác nhận password
            confirm_xpath_options = [
                "/html/body/div[6]/div[1]/div/div[2]/div/div/div/div/div/div/div[4]/div[2]/div[1]/div/div/div[4]/div/div/div/div/div",
                "/html/body/div[7]/div[1]/div/div[2]/div/div/div/div/div/div/div[4]/div[2]/div[1]/div/div/div[4]/div/div/div/div/div",
                "/html/body/div[8]/div[1]/div/div[2]/div/div/div/div/div/div/div[4]/div[2]/div[1]/div/div/div[4]/div/div/div/div/div",
                "/html/body/div[9]/div[1]/div/div[2]/div/div/div/div/div/div/div[4]/div[2]/div[1]/div/div/div[4]/div/div/div/div/div"
            ]
            
            for xpath in confirm_xpath_options:
                try:
                    # Kiểm tra flag dừng
                    with thread_lock:
                        if not is_running:
                            print(f"Thread bị dừng, bỏ qua account: {account['uid']}")
                            return False
                    
                    self.wait_and_click(xpath, timeout=5)
                    break
                except:
                    continue
            
            
            # Kiểm tra kết quả
            success_text = self.wait_and_get_text("/html/body/div[1]/div/div[1]/div/div/div[3]/div/div/div[2]/div/div/div/div/div/div[5]/div/div[4]/div[2]/div[1]/div/div/div/div/h2/span")
            
            if success_text:
                print(f"✅ Setup 2FA thành công cho {account['uid']}")
                eel.update2FAResult(account['uid'], ma_2fa, "✅ Thành công")()
                
                # Chạy xóa email
                self.run_delete_maiil()
                return True
            else:
                print(f"✅ Setup 2FA có thể thành công cho {account['uid']} (không tìm thấy text xác nhận)")
                eel.update2FAResult(account['uid'], ma_2fa, "✅ Thành công")()
                
                # Chạy xóa email
                self.run_delete_maiil()
                return True
           

        
# tạo tài khoản 
# 
# /html/body/div[1]/div/div/div/div[3]/div/div/div[2]/div/div/div/div/div/div/div/div[4]/div[2]/div[1]/div/div/div[2]/div/div[1]/div[1]
# /html/body/div[1]/div/div/div/div/div[3]/div/div/div[2]/div/div/div/div/div/div/div/div[4]/div[2]/div[1]/div/div/div[2]/div/div[1]/div[1]
# /html/body/div[1]/div/div/div/div/div[3]/div/div/div[2]/div/div/div/div/div/div[2]/div/div[5]/div/div/div/div/div/div/div/div/div
# 2fa /html/body/div[1]/div/div/div/div/div[3]/div/div/div[2]/div/div/div/div/div/div[3]/div/div[4]/div[2]/div[1]/div/div/div[4]/div[2]/div/div/div/div[1]/span
# /html/body/div[1]/div/div/div/div/div[3]/div/div/div[2]/div/div/div/div/div/div[3]/div/div[5]/div/div/div/div/div/div/div/div/div

    def check_code(self, account):
        retry_count = 0
        max_retries = 2
        
        while retry_count < max_retries:
            try:
                # Check for OK text in multiple possible xpaths
                polish_text = self.wait_and_get_text("/html/body/div[1]/div/div/div/div/div[3]/div/div/div[2]/div/div/div/div/div/div[2]/div/div[4]/div[2]/div[1]/div/div/div[2]/div/div/div[2]/div/div/label[1]/div[1]/div/div[1]/div/div/div/div/div[1]", timeout=5)
                
                if polish_text:
                    print("Found Polish verification text, continuing with the process...")
                    return True
                error_text = None
                error_xpath_options = [
                    "/html/body/div[8]/div[1]/div/div[2]/div/div/div/div/div/div/div[4]/div[2]/div[1]/div/div/div[1]/div/h2/span",
                    "/html/body/div[7]/div[1]/div/div[2]/div/div/div/div/div/div/div[4]/div[2]/div[1]/div/div/div[1]/div/h2/span",
                    "/html/body/div[6]/div[1]/div/div[2]/div/div/div/div/div/div/div[4]/div[2]/div[1]/div/div/div[1]/div/h2/span",
                    "/html/body/div[9]/div[1]/div/div[2]/div/div/div/div/div/div/div[4]/div[2]/div[1]/div/div/div[1]/div/h2/span"
                ]
                
                # Try each xpath until we find text or run out of options
                for xpath in error_xpath_options:
                    error_text = self.wait_and_get_text(xpath, timeout=5)
                    if error_text:
                        print(f"Found error text at {xpath}: {error_text}")
                        break
                if error_text and "możesz" in error_text:
                    print(f"Found 'ok' error message, retrying... Attempt {retry_count + 1}/{max_retries}")
                    
                    # Close current driver and restart everything
                    self.driver.quit()
                    self.driver = None
                    self.setup_driver()
                    self.login(account['cookie'])
                    
                    # Navigate to security page
                    self.driver.get("https://accountscenter.facebook.com/password_and_security")
                    
                    # Click 2FA settings
                    click_success = False
                    for xpath in [
                        "/html/body/div[1]/div/div/div/div/div[1]/div/div/div[1]/div[1]/div/div[1]/div[1]/div[2]/div/div/div/div[2]/div/main/div/div/div[2]/div[1]/div[2]/div/div/div[2]/div/div[1]",
                        "/html/body/div[1]/div/div/div/div[1]/div/div/div[1]/div[1]/div/div[1]/div[1]/div[2]/div/div/div/div[2]/div/main/div/div/div[2]/div[1]/div[2]/div/div/div[2]/div/div[1]"
                    ]:
                        try:
                            self.wait_and_click(xpath, timeout=5)
                            click_success = True
                            break
                        except:
                            continue
                            
                    if not click_success:
                        print("Không thể click vào 2FA settings")
                        retry_count += 1
                        continue
                            
                    # Click setup 2FA
                    setup_success = False
                    for xpath in [
                        "/html/body/div[1]/div/div/div/div/div[3]/div/div/div[2]/div/div/div/div/div/div/div/div[4]/div[2]/div[1]/div/div/div[2]/div/div/div[1]",
                        "/html/body/div[1]/div/div/div/div[3]/div/div/div[2]/div/div/div/div/div/div[2]/div/div[5]/div/div/div/div/div/div/div/div/div"
                    ]:
                        try:
                            self.wait_and_click(xpath, timeout=5)
                            setup_success = True
                            break
                        except:
                            continue
                            
                    if not setup_success:
                        print("Không thể click vào setup 2FA")
                        retry_count += 1
                        continue
                        
                    retry_count += 1
                    continue
                
                # Check second xpath for Polish text
                
                
                # If neither condition is met
                print("Verification required via email or WhatsApp")
                self.meta_2FA(account)
                # eel.update2FAResult(account['uid'], "mail whatsapp", "⚠️ Verification required via email or WhatsApp")()
                # if self.driver:
                #     self.driver.quit()
                #     self.driver = None
                # return False
                
            except Exception as e:
                print(f"Error during code check: {e}")
                retry_count += 1
                
                # Check second xpath for Polish text
                polish_text = self.wait_and_get_text("/html/body/div[1]/div/div/div/div/div[3]/div/div/div[2]/div/div/div/div/div/div[2]/div/div[4]/div[2]/div[1]/div/div/div[1]/div/h2/span", timeout=5)
                
                if polish_text and "Pomóż chronić swoje konto" in polish_text:
                    print("Found Polish verification text, continuing with the process...")
                    return True
                
                # If neither condition is met
                print("Verification required via email or WhatsApp")
                self.meta_2FA(account)
                # eel.update2FAResult(account['uid'], "", "⚠️ Verification required via email or WhatsApp")()
                # if self.driver:
                #     # self.driver.quit()
                #     self.driver = None
                # return False
                
            except Exception as e:
                print(f"Error during code check: {e}")
                retry_count += 1
                
        if retry_count >= max_retries:
            print("Maximum retry attempts reached")
            # eel.update2FAResult(account['uid'], "", "❌ Maximum retry attempts reached")()
            if self.driver:
                self.driver.quit()
                self.driver = None
            return False
            
    def check_login(self,account):
        try:
            current_url = self.driver.current_url
            print(f"Current URL: {current_url}")
            
            if "956" in current_url:
                print("Checkpoint 956 detected")
                eel.update2FAResult(account['uid'], "956", "❌ Checkpoint 956")()
                return False
            elif current_url == "https://accountscenter.facebook.com/password_and_security":
                print("Login successful")
                return True
            else:
                print("Checkpoint 282 detected")
                eel.update2FAResult(account['uid'], "282", "❌ Checkpoint 282")()
                return False
        except Exception as e:
            print(f"Error checking login status: {e}")
            return False
            
    def login(self, cookie_str):
        try:
            self.wait_and_click("/html/body/div[3]/div/div/div/div/div/div[3]/div[2]/div/div[2]/div[1]/div")
        except:
            pass
            
        # Chuyển đổi cookie string thành list of dictionaries
        cookie_list = convert_cookie_string_to_list(cookie_str)
        
        c_user = get_cookie_value(cookie_list, 'c_user')
        chrome_drivers[c_user] = self.driver
        
        for cookie in cookie_list:
            cookie["domain"] = ".facebook.com"
            self.driver.add_cookie(cookie)
        self.driver.refresh()

    def wait_and_get_text(self, xpath, timeout=10):
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((By.XPATH, xpath))
            )
            return element.text
        except:
            return None
        
    def wait_and_send_keys(self, xpath, keys, timeout=20):
        element = WebDriverWait(self.driver, timeout).until(
            EC.presence_of_element_located((By.XPATH, xpath))
        )
        element.clear()  # Thêm clear để đảm bảo không có text cũ
        element.send_keys(keys)
        
    def wait_and_click(self, xpath, timeout=10):
        element = WebDriverWait(self.driver, timeout).until(
            EC.element_to_be_clickable((By.XPATH, xpath))
        )
        element.click()

    def get_code_2fa(self, code):
        fa = code.replace(' ', '')
        cookies = {
            '_gcl_au': '1.1.2020426435.1752513024',
            '_gid': 'GA1.2.1424787188.1752513024',
            '_ga_R2SB88WPTD': 'GS2.1.s1752513024$o1$g0$t1752513024$j60$l0$h0',
            '_ga': 'GA1.1.1110160292.1752513024',
        }

        headers = {
            'accept': '*/*',
            'accept-language': 'vi-VN,vi;q=0.9,fr-FR;q=0.8,fr;q=0.7,en-US;q=0.6,en;q=0.5',
            'priority': 'u=1, i',
            'referer': 'https://2fa.live/',
            'sec-ch-ua': '"Not)A;Brand";v="8", "Chromium";v="138", "Google Chrome";v="138"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36',
            'x-requested-with': 'XMLHttpRequest',
        }

        try:
            response = requests.get(f'https://2fa.live/tok/{fa}', cookies=cookies, headers=headers, timeout=10)
            response.raise_for_status()
            return response.json()['token']
        except Exception as e:
            print(f"Lỗi khi lấy mã 2FA: {e}")
            return None
    
    def run_delete_maiil(self):
        try:
            self.driver.get("https://accountscenter.facebook.com/personal_info/contact_points")
            
            self.wait_and_click("/html/body/div[1]/div/div/div/div/div[3]/div/div/div[2]/div/div/div/div/div/div/div/div[4]/div[2]/div[1]/div/div/div[2]/div/div/div/div/div[2]/div/div[1]")
            # Đợi và click vào n
            # /html/body/div[1]/div/div/div/div/div[3]/div/div/div[2]/div/div/div/div/div/div/div/div[4]/div[2]/div[1]/div/div/div[2]/div[2]/div/div/div/div[2]/div/div[1]
            xpath_options = [
                "/html/body/div[1]/div/div/div/div/div[3]/div/div/div[2]/div/div/div/div/div/div/div/div[4]/div[2]/div[1]/div/div/div[2]/div[2]/div/div/div/div[2]/div/div[1]",
                "/html/body/div[1]/div/div/div/div/div[3]/div/div/div[2]/div/div/div/div/div/div/div/div[4]/div[2]/div[1]/div/div/div[2]/div[2]/div/div/div/div/div/div[1]"
            ]
            
            for xpath in xpath_options:
                try:
                    # Kiểm tra flag dừng
                    with thread_lock:
                        if not is_running:
                            return False
                    
                    self.wait_and_click(xpath, timeout=5)
                    click_success = True
                    break
                except:
                    continue
            self.wait_and_click("/html/body/div[6]/div[1]/div/div[2]/div/div/div/div[3]/div[2]/div/div/div")
            
            if self.wait_and_get_text("/html/body/div[1]/div/div/div/div/div[3]/div/div/div[2]/div/div/div/div/div/div[2]/div/div[4]/div[2]/div[1]/div/div/div[1]/div/h2/span"):
                self.wait_and_click("/html/body/div[1]/div/div/div/div/div[3]/div/div/div[2]/div/div/div/div/div/div[2]/div/div[5]/div/div/div/div/div/div/div/div/div")
                print("Đã xóa email thành công")
            else:
                print("Không thể xóa email, vui lòng kiểm tra lại")
        except Exception as e:
            print(f"Lỗi khi xóa email: {e}")

        
    def run_change_2fa(self, account):
        print(f"Bắt đầu xử lý account: {account['uid']}")
        
        try:
            # Kiểm tra flag dừng trước khi bắt đầu
            with thread_lock:
                if not is_running:
                    print(f"Thread bị dừng, bỏ qua account: {account['uid']}")
                    return False
            
            self.login(account['cookie'])
            
            
            # Kiểm tra flag dừng
            with thread_lock:
                if not is_running:
                    print(f"Thread bị dừng, bỏ qua account: {account['uid']}")
                    return False
                    
      
            # Load trang security
            self.driver.get("https://accountscenter.facebook.com/password_and_security")
            if self.check_login(account):
                print("Login check passed, continuing...")
            else:
                print("Login check failed, stopping process")
                if self.driver:
                    self.driver.quit()
                    self.driver = None
                return False
            
            # Thử các xpath khác nhau để click vào 2FA settings
            click_success = False
            xpath_options = [
                "/html/body/div[1]/div/div/div/div/div[1]/div/div/div[1]/div[1]/div/div[1]/div[1]/div[2]/div/div/div/div[2]/div/main/div/div/div[2]/div[1]/div[2]/div/div/div[2]/div/div[1]",
                "/html/body/div[1]/div/div/div/div[1]/div/div/div[1]/div[1]/div/div[1]/div[1]/div[2]/div/div/div/div[2]/div/main/div/div/div[2]/div[1]/div[2]/div/div/div[2]/div/div[1]"
            ]
            
            for xpath in xpath_options:
                try:
                    # Kiểm tra flag dừng
                    with thread_lock:
                        if not is_running:
                            print(f"Thread bị dừng, bỏ qua account: {account['uid']}")
                            return False
                    
                    self.wait_and_click(xpath, timeout=5)
                    click_success = True
                    break
                except:
                    continue
            
            # Thử các xpath để setup 2FA
            setup_xpath_options = [
                "/html/body/div[1]/div/div/div/div/div[3]/div/div/div[2]/div/div/div/div/div/div/div/div[4]/div[2]/div[1]/div/div/div[2]/div/div/div[1]",
                "/html/body/div[1]/div/div/div/div/div[3]/div/div/div[2]/div/div/div/div/div/div/div/div[4]/div[2]/div[1]/div/div/div[2]/div/div[1]/div[1]",
                "/html/body/div[1]/div/div/div/div[3]/div/div/div[2]/div/div/div/div/div/div[2]/div/div[5]/div/div/div/div/div/div/div/div/div",
                "/html/body/div[1]/div/div/div/div[3]/div/div/div[2]/div/div/div/div/div/div[1]/div/div[4]/div[2]/div[1]/div/div/div[2]/div/div/div[1]/div",
            ]
            
            setup_success = False
            for xpath in setup_xpath_options:
                try:
                    # Kiểm tra flag dừng
                    with thread_lock:
                        if not is_running:
                            print(f"Thread bị dừng, bỏ qua account: {account['uid']}")
                            return False
                    
                    self.wait_and_click(xpath, timeout=5)
                    
                    # Check for error messages after clicking setup button
                    if not self.check_code(account):
                        print(f"Lỗi xác thực cho {account['uid']}, bỏ qua account này")
                        return False  # Return false to stop processing this account
                    
                    setup_success = True
                    break
                except:
                    continue

            print("Không thể setup 2FA, thử lại...")
        
            # Click để tiếp tục setup
            continue_xpath_options = [
                "/html/body/div[1]/div/div/div/div/div[3]/div/div/div[2]/div/div/div/div/div/div[2]/div/div[5]/div/div/div/div/div/div/div/div",
                "/html/body/div[1]/div/div/div/div/div[3]/div/div/div[2]/div/div/div/div/div/div[2]/div/div[3]/div/div/div/div/div/div/div/div/div",
                "/html/body/div[1]/div/div/div/div/div[3]/div/div/div[2]/div/div/div/div/div/div[2]/div/div[2]/div/div/div/div/div/div/div/div/div",
                "/html/body/div[1]/div/div/div/div/div[3]/div/div/div[2]/div/div/div/div/div/div[2]/div/div[4]/div/div/div/div/div/div/div/div/div",
                "/html/body/div[1]/div/div/div/div/div[3]/div/div/div[2]/div/div/div/div/div/div[2]/div/div[5]/div/div/div/div/div/div/div/div/div",
            ]
            
            for xpath in continue_xpath_options:
                try:
                    # Kiểm tra flag dừng
                    with thread_lock:
                        if not is_running:
                            print(f"Thread bị dừng, bỏ qua account: {account['uid']}")
                            return False
                    
                    self.wait_and_click(xpath, timeout=5)
                    break
                except:
                    continue
            
            time.sleep(10)
            # Lấy mã 2FA
            ma_2fa = self.wait_and_get_text("/html/body/div[1]/div/div/div/div/div[3]/div/div/div[2]/div/div/div/div/div/div[3]/div/div[4]/div[2]/div[1]/div/div/div[4]/div[2]/div/div/div/div[1]/span")
            if not ma_2fa:
                raise Exception("Không thể lấy mã 2FA")
            
            print(f"Đã lấy mã 2FA: {ma_2fa}")
            eel.update2FAResult(account['uid'], ma_2fa, "⏳ Đang xử lý...")()
            
            # Lấy code từ API
            code_2fa = self.get_code_2fa(ma_2fa)
            if not code_2fa:
                raise Exception("Không thể lấy code 2FA từ API")
            
            # Kiểm tra flag dừng
            with thread_lock:
                if not is_running:
                    print(f"Thread bị dừng, bỏ qua account: {account['uid']}")
                    return False
            
            # Click tiếp tục
            self.wait_and_click("/html/body/div[1]/div/div/div/div/div[3]/div/div/div[2]/div/div/div/div/div/div[3]/div/div[5]/div/div/div/div/div/div/div/div/div")
            # Nhập code 2FA
            self.wait_and_send_keys("/html/body/div[1]/div/div/div/div/div[3]/div/div/div[2]/div/div/div/div/div/div[4]/div/div[4]/div[2]/div[1]/div/div/div[2]/div/div/div[1]/input", code_2fa)
            # Click xác nhận
            self.wait_and_click("/html/body/div[1]/div/div/div/div/div[3]/div/div/div[2]/div/div/div/div/div/div[4]/div/div[5]/div/div/div/div/div/div/div/div/div")
            # Nhập password để xác nhận
            eel.update2FAResult(account['uid'], ma_2fa, "✅ Thành công")()
            password_xpath_options = [
                "/html/body/div[6]/div[1]/div/div[2]/div/div/div/div/div/div/div[4]/div[2]/div[1]/div/div/div[3]/div/div/div/div[1]/input",
                "/html/body/div[7]/div[1]/div/div[2]/div/div/div/div/div/div/div[4]/div[2]/div[1]/div/div/div[3]/div/div/div/div[1]/input",
                "/html/body/div[8]/div[1]/div/div[2]/div/div/div/div/div/div/div[4]/div[2]/div[1]/div/div/div[3]/div/div/div/div[1]/input",
                "/html/body/div[9]/div[1]/div/div[2]/div/div/div/div/div/div/div[4]/div[2]/div[1]/div/div/div[3]/div/div/div/div[1]/input",
            ]
            
            password_entered = False
            for xpath in password_xpath_options:
                try:
                    # Kiểm tra flag dừng
                    with thread_lock:
                        if not is_running:
                            print(f"Thread bị dừng, bỏ qua account: {account['uid']}")
                            return False
                    
                    self.wait_and_send_keys(xpath, account['pass'], timeout=5)
                    password_entered = True
                    break
                except:
                    continue
            
            if not password_entered:
                raise Exception("Không thể nhập password")
            
            # Click xác nhận password
            confirm_xpath_options = [
                "/html/body/div[6]/div[1]/div/div[2]/div/div/div/div/div/div/div[4]/div[2]/div[1]/div/div/div[4]/div/div/div/div/div",
                "/html/body/div[7]/div[1]/div/div[2]/div/div/div/div/div/div/div[4]/div[2]/div[1]/div/div/div[4]/div/div/div/div/div",
                "/html/body/div[8]/div[1]/div/div[2]/div/div/div/div/div/div/div[4]/div[2]/div[1]/div/div/div[4]/div/div/div/div/div",
                "/html/body/div[9]/div[1]/div/div[2]/div/div/div/div/div/div/div[4]/div[2]/div[1]/div/div/div[4]/div/div/div/div/div"
            ]
            
            for xpath in confirm_xpath_options:
                try:
                    # Kiểm tra flag dừng
                    with thread_lock:
                        if not is_running:
                            print(f"Thread bị dừng, bỏ qua account: {account['uid']}")
                            return False
                    
                    self.wait_and_click(xpath, timeout=5)
                    break
                except:
                    continue
            
            
            # Kiểm tra kết quả
            success_text = self.wait_and_get_text("/html/body/div[1]/div/div[1]/div/div/div[3]/div/div/div[2]/div/div/div/div/div/div[5]/div/div[4]/div[2]/div[1]/div/div/div/div/h2/span")
            
            if success_text:
                print(f"✅ Setup 2FA thành công cho {account['uid']}")
                eel.update2FAResult(account['uid'], ma_2fa, "✅ Thành công")()
                
                # Chạy xóa email
                self.run_delete_maiil()
                return True
            else:
                print(f"✅ Setup 2FA có thể thành công cho {account['uid']} (không tìm thấy text xác nhận)")
                eel.update2FAResult(account['uid'], ma_2fa, "✅ Thành công")()
                
                # Chạy xóa email
                self.run_delete_maiil()
                return True
                
        except Exception as e:
            error_message = f"Lỗi khi xử lý 2FA: {str(e)}"
            print(f"❌ {account['uid']}: {error_message}")
            # eel.update2FAResult(account['uid'], "", f"❌ {error_message}")()
            return False
        finally:
            # Đảm bảo đóng driver
            try:
                if self.driver:
                    self.driver.quit()
            except:
                pass

    def cleanup(self):
        """Hàm cleanup để đóng driver và xóa profile"""
        import shutil
        try:
            if self.driver:
                self.driver.quit()
                self.driver = None
                # Delete Chrome profile directory
                profile_path = os.path.join(tempfile.gettempdir(), f"chrome_profile_{self.window_index}")
                try:
                    import shutil
                    if os.path.exists(profile_path):
                        shutil.rmtree(profile_path)
                        print(f"Deleted Chrome profile: {profile_path}")
                except Exception as e:
                    print(f"Error deleting Chrome profile: {e}")
        except:
            pass

# Hàm xử lý thread được cải thiện - sắp xếp lại window index
def process_accounts_thread(accounts, thread_id, start_window_index):
    """
    Xử lý accounts trong thread với window index được sắp xếp lại từ đầu
    """
    global is_running
    
    print(f"Thread {thread_id} bắt đầu xử lý {len(accounts)} accounts từ window index {start_window_index}")
    
    for i, account in enumerate(accounts):
        # Kiểm tra flag dừng
        with thread_lock:
            if not is_running:
                print(f"Thread {thread_id} đã dừng")
                break
        
        get2fa = None
        try:
            print(f"Thread {thread_id} - Xử lý account {i+1}/{len(accounts)}: {account['uid']}")
            
            # Tính window index cho account này - luôn bắt đầu từ 0
            current_window_index = start_window_index + i
            
            # Tạo instance với window index được tính từ đầu
            get2fa = Get2FA(current_window_index)
            
            # Thêm delay để tránh các thread khởi động cùng lúc
            time.sleep(thread_id * 2)
            
            # Gọi hàm run_change_2fa
            success = get2fa.run_change_2fa(account)
            
            if success:
                print(f"✅ Thành công: {account['uid']}")
            else:
                print(f"❌ Thất bại: {account['uid']}")
                
        except Exception as e:
            print(f"❌ Lỗi xử lý {account['uid']}: {e}")
            # Cập nhật UI với lỗi
            # eel.update2FAResult(account['uid'], "", f"❌ Lỗi: {str(e)}")()
        # finally:
        #     # Đảm bảo cleanup driver
        #     if get2fa:
        #         get2fa.cleanup()
        
        # Nghỉ giữa các account
        time.sleep(3)
    
    print(f"Thread {thread_id} hoàn thành")

@eel.expose
def start_2fa_process(data):
    global is_running, active_threads
    
    try:
        # Kiểm tra input
        if not isinstance(data, dict):
            return {"success": False, "message": "Dữ liệu không hợp lệ"}
        
        accounts = data.get('accounts', [])
        thread_count = int(data.get('thread_count', 1))
        
        if not accounts:
            return {"success": False, "message": "Không có account nào"}
        
        if thread_count <= 0:
            thread_count = 1
        
        # Giới hạn số thread tối đa
        if thread_count > 20:
            thread_count = 20
        
        # Kiểm tra xem có đang chạy không
        with thread_lock:
            if is_running:
                return {"success": False, "message": "Đang có tiến trình chạy"}
            is_running = True
            active_threads = []  # Reset active threads
        
        print(f"Bắt đầu xử lý {len(accounts)} accounts với {thread_count} threads")
        print("Window index sẽ được sắp xếp lại từ đầu (0, 1, 2, 3...)")
        
        # Chia accounts cho các thread và tính window index từ đầu
        accounts_per_thread = len(accounts) // thread_count
        remainder = len(accounts) % thread_count
        
        start_index = 0
        window_start_index = 0  # Bắt đầu từ 0 mỗi lần chạy
        
        for i in range(thread_count):
            # Tính số accounts cho thread này
            current_thread_accounts = accounts_per_thread + (1 if i < remainder else 0)
            
            if current_thread_accounts > 0:
                # Lấy accounts cho thread này
                thread_accounts = accounts[start_index:start_index + current_thread_accounts]
                
                # Tạo thread với window start index được tính từ đầu
                thread = threading.Thread(
                    target=process_accounts_thread,
                    args=(thread_accounts, i, window_start_index),
                    name=f"Thread-{i}"
                )
                active_threads.append(thread)
                thread.start()
                
                print(f"Thread {i} được gán window index từ {window_start_index} đến {window_start_index + current_thread_accounts - 1}")
                
                start_index += current_thread_accounts
                window_start_index += current_thread_accounts  # Tăng window index liên tục
                
                # Thêm delay nhỏ giữa các thread
                time.sleep(0.5)
        
        # Tạo thread để theo dõi các thread worker
        def monitor_threads():
            for thread in active_threads:
                thread.join()
            
            with thread_lock:
                global is_running
                is_running = False
                active_threads.clear()
            
            print("Tất cả threads đã hoàn thành. Lần chạy tiếp theo sẽ sắp xếp lại window index từ đầu.")
        
        monitor_thread = threading.Thread(target=monitor_threads, name="Monitor-Thread")
        monitor_thread.start()
        
        return {"success": True, "message": f"Đã khởi động {len(active_threads)} threads với window index từ 0"}
        
    except Exception as e:
        with thread_lock:
            is_running = False
            active_threads.clear()
        return {"success": False, "message": f"Lỗi: {str(e)}"}

@eel.expose
def stop_2fa_process():
    global is_running, active_threads
    
    print("Đang dừng tiến trình 2FA...")
    
    with thread_lock:
        is_running = False
    
    # Đóng tất cả chrome drivers
    for driver in chrome_drivers.values():
        try:
            driver.quit()
        except:
            pass
    
    chrome_drivers.clear()
    
    # Chờ tất cả threads kết thúc (với timeout)
    for thread in active_threads:
        if thread.is_alive():
            thread.join(timeout=5)  # Chờ tối đa 5 giây
    
    with thread_lock:
        active_threads.clear()
    
    print("Đã dừng tiến trình 2FA. Lần chạy tiếp theo sẽ sắp xếp lại window index từ đầu.")
    return {"success": True, "message": "Đã dừng tiến trình"}

@eel.expose
def get_process_status():
    with thread_lock:
        return {
            "is_running": is_running,
            "active_threads": len(active_threads)
        }