import eel
import threading
from time import sleep
import random
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import string


chrome_drivers = {}
uid_to_pass = {}
stop_flag = False
running_threads = []
global_index_counter = 0
index_lock = threading.Lock()  # Thêm lock để đồng bộ index
# Danh sách UID đã xử lý xong (thành công, lỗi, hoặc bị tắt Chrome)
processed_uids = set()

def get_next_index():
    global global_index_counter
    with index_lock:
        current_index = global_index_counter
        global_index_counter += 1
        return current_index

def reset_all():
    global stop_flag, global_index_counter, chrome_drivers, uid_to_pass, running_threads
    stop_flag = True
    # Đóng tất cả chrome drivers hiện tại
    for uid, driver in list(chrome_drivers.items()):
        try:
            driver.quit()
        except:
            pass
    chrome_drivers.clear()
    # Clear other globals
    uid_to_pass.clear()
    running_threads.clear()
    # KHÔNG xóa processed_uids để không chạy lại các UID đã xử lý
    # Reset index counter
    global_index_counter = 0
    
class main:
    def __init__(self, data_change_pass):
        self.index = get_next_index()  # Sử dụng hàm thread-safe
        self.stop_flag = False
        options = Options()
        self.auto_get_cookie = data_change_pass.get('auto_get_cookie', True)

        # Chrome options
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-software-rasterizer")
        options.add_argument("--disable-infobars")
        options.add_argument("--start-maximized")
        options.add_argument("--window-size=375,812")
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36")

        prefs = {
            "profile.default_content_setting_values.notifications": 2,
            "credentials_enable_service": False,
            "profile.password_manager_enabled": False
        }
        options.add_experimental_option("prefs", prefs)

        self.driver = webdriver.Chrome(options=options)

        # Window positioning
        SCREEN_WIDTH = 1920
        WINDOW_WIDTH = 400
        WINDOW_HEIGHT = 600
        COLUMNS = SCREEN_WIDTH // WINDOW_WIDTH
        row = self.index // COLUMNS
        col = self.index % COLUMNS
        x = col * WINDOW_WIDTH
        y = row * WINDOW_HEIGHT
        self.driver.set_window_position(x, y)

        def tao_mat_khau(do_dai=12, co_ky_tu_dac_biet=True):
            ky_tu = string.ascii_letters + string.digits
            if co_ky_tu_dac_biet:
                ky_tu += string.punctuation
            return ''.join(random.choice(ky_tu) for _ in range(do_dai))
        
        self.generated_pass = (
            tao_mat_khau() if data_change_pass['type_password'] == 2 else data_change_pass['password']
        )

    def wait_and_click(self, xpath, timeout=20):
        # Kiểm tra stop flag trước khi thực hiện
        if stop_flag or self.stop_flag:
            raise Exception("Process stopped by user")
            
        element = WebDriverWait(self.driver, timeout).until(
            EC.element_to_be_clickable((By.XPATH, xpath))
        )
        element.click()
        sleep(1.5)

    def wait_and_send_keys(self, xpath, keys, timeout=20):
        # Kiểm tra stop flag trước khi thực hiện
        if stop_flag or self.stop_flag:
            raise Exception("Process stopped by user")
            
        def human_typing(element, text, delay_range=(0.1, 0.3)):
            for char in text:
                if stop_flag or self.stop_flag:
                    raise Exception("Process stopped by user")
                element.send_keys(char)
                sleep(random.uniform(*delay_range))

        element = WebDriverWait(self.driver, timeout).until(
            EC.presence_of_element_located((By.XPATH, xpath))
        )
        human_typing(element, keys)
    
    def wait_and_get_text(self, xpath, timeout=20):
        # Kiểm tra stop flag trước khi thực hiện
        if stop_flag or self.stop_flag:
            raise Exception("Process stopped by user")
            
        element = WebDriverWait(self.driver, timeout).until(
            EC.presence_of_element_located((By.XPATH, xpath))
        )
        return element.text
    
    def status(self, message, color):
        uid = self.account.get("uid", "")
        eel.updateAccountStatus(uid, message, color)

    def get_cookies(self):
        return self.driver.get_cookies()
    
    def changepass(self, account):
        try:
            # Kiểm tra stop flag ngay từ đầu
            if stop_flag or self.stop_flag:
                print(f"Process stopped for {account['uid']}")
                eel.updateAccountStatus(account['uid'], "🔴 Đã dừng", "#f44747")
                self.driver.quit()
                chrome_drivers.pop(account['uid'], None)
                return False, "", []
            
            self.driver.get(f"https://www.facebook.com/recover/password/?u={account['uid']}&n={account['code']}&fl=default_recover&sih=0&msgr=0")
            
            try:
                self.wait_and_click("/html/body/div[3]/div/div/div/div/div/div[3]/div[2]/div/div[2]/div[1]/div")
            except:
                pass
            
            # Kiểm tra stop flag trước các bước quan trọng
            if stop_flag:
                self.status("🔴 Đã dừng", "#f44747")
                return False, "", []
                
            self.wait_and_send_keys("/html/body/div[1]/div[1]/div[1]/div/div[2]/form/div/div[2]/div[2]/div[1]/div/input", self.generated_pass)
            
            if stop_flag:
                self.status("🔴 Đã dừng", "#f44747")
                return False, "", []
                
            self.wait_and_click("/html/body/div[1]/div[1]/div[1]/div/div[2]/form/div/div[3]/div/div[1]/button")
            self.driver.execute_script(f"document.title = 'Chrome {self.index + 1}'")
            
            if self.auto_get_cookie:
                # Kiểm tra stop flag trong quá trình sleep với vòng lặp nhỏ hơn
                for i in range(20):
                    if stop_flag:
                        self.status("🔴 Đã dừng", "#f44747")
                        return False, "", []
                    sleep(1)
                    
                cookies = self.get_cookies()
                eel.onGetCookie(account['uid'], self.generated_pass, cookies)
                self.driver.quit()
                chrome_drivers.pop(account['uid'], None)
                return True, self.generated_pass, cookies
            else:
                eel.updateAccountStatus(account['uid'], "🟢 Đã đổi pass, chờ lấy cookie", "#4ec9b0")
                return True, self.generated_pass, []
                
        except Exception as e:
            error_msg = str(e)
            if "Process stopped by user" in error_msg:
                print(f"Process stopped for {account['uid']}")
                eel.updateAccountStatus(account['uid'], "🔴 Đã dừng", "#f44747")
            else:
                print("Lỗi đổi mật khẩu:", e)
                eel.updateAccountStatus(account['uid'], "❌ Lỗi đổi pass", "#f44747")
            
            # Cleanup
            try:
                self.driver.quit()
            except:
                pass
            chrome_drivers.pop(account['uid'], None)
            return False, self.generated_pass, []



@eel.expose
def thread(data_change_pass):
    global stop_flag, processed_uids
    reset_all()
    stop_flag = False

    accounts = data_change_pass['account']
    max_threads = data_change_pass['thread']

    # Tạo dict uid -> account để dễ lọc
    uid_to_account = {acc['uid']: acc for acc in accounts}

    while True:
        if stop_flag:
            print("Stopping all processes...")
            force_stop_all_drivers()
            break

        # Lọc ra các account chưa xử lý
        pending_accounts = [acc for acc in accounts if acc['uid'] not in processed_uids]
        if not pending_accounts:
            break

        # Reset lại index về 0 trước mỗi batch mới để Chrome luôn sắp xếp lại từ đầu
        global global_index_counter
        global_index_counter = 0

        # Lấy batch mới
        batch = pending_accounts[:max_threads]
        batch_threads = []

        for acc in batch:
            if stop_flag:
                force_stop_all_drivers()
                break
            t = threading.Thread(target=run_change_pass, args=(acc, data_change_pass))
            t.daemon = True
            batch_threads.append(t)
            running_threads.append(t)
            t.start()

        # Wait for all threads in current batch to complete
        for t in batch_threads:
            if stop_flag:
                force_stop_all_drivers()
                break
            try:
                t.join(timeout=0.5)  # Thêm timeout để có thể kiểm tra stop_flag thường xuyên hơn
            except:
                pass

        # Clean up finished threads from tracking
        running_threads[:] = [t for t in running_threads if t.is_alive()]

    print("[✅] Tất cả threads đã kết thúc.")


def run_change_pass(acc, data_change_pass):
    global stop_flag, processed_uids
    # Đánh dấu UID đã xử lý NGAY KHI BẮT ĐẦU, để dù có tắt Chrome giữa chừng cũng không chạy lại
    processed_uids.add(acc['uid'])
    try:
        if stop_flag:
            eel.updateAccountStatus(acc['uid'], "🔴 Đã dừng", "#f44747")
            return

        instance = main(data_change_pass)
        chrome_drivers[acc['uid']] = instance.driver

        success = False
        try:
            success, new_pass, cookies = instance.changepass(acc)
            if success:
                uid_to_pass[acc['uid']] = new_pass
        finally:
            if not success:
                try:
                    instance.driver.quit()
                except:
                    pass
                chrome_drivers.pop(acc['uid'], None)

    except Exception as e:
        print(f"[THREAD ERROR] {acc['uid']}: {e}")
        eel.updateAccountStatus(acc['uid'], f"❌ Lỗi: {str(e)}", "#f44747")
    finally:
        if acc['uid'] in chrome_drivers:
            try:
                chrome_drivers[acc['uid']].quit()
            except:
                pass
            chrome_drivers.pop(acc['uid'])

@eel.expose
def get_cookie_by_uid(uid):
    driver = chrome_drivers.get(uid)
    if driver:
        try:
            cookies = driver.get_cookies()
            new_pass = uid_to_pass.get(uid, "")
            eel.onGetCookie(uid, new_pass, cookies)
            driver.quit()
            chrome_drivers.pop(uid, None)
            eel.updateAccountStatus(uid, "✅ Đã lấy cookie", "#4ec9b0")
            print(f"Cookies for {uid}: {cookies}")
            return cookies
        except Exception as e:
            print(f"Lỗi lấy cookie cho {uid}: {e}")
            eel.updateAccountStatus(uid, "❌ Lỗi lấy cookie", "#f44747")
            return []
    else:
        eel.updateAccountStatus(uid, "❌ Không tìm thấy Chrome", "#ce1126")
        return []

@eel.expose
def close_chrome_by_uid(uid):
    driver = chrome_drivers.get(uid)
    if driver:
        try:
            driver.quit()
            chrome_drivers.pop(uid, None)
            eel.updateAccountStatus(uid, "🔴 Đã đóng Chrome", "#f44747")
            print(f"Đã đóng Chrome cho {uid}")
            return True
        except Exception as e:
            print(f"Lỗi đóng Chrome cho {uid}: {e}")
            return False
    else:
        eel.updateAccountStatus(uid, "❌ Không tìm thấy Chrome", "#ce1126")
        return False

def force_stop_all_drivers():
    """Hàm này sẽ đóng tất cả các driver ngay lập tức"""
    global chrome_drivers, uid_to_pass
    
    for uid, driver in list(chrome_drivers.items()):
        try:
            driver.quit()
            print(f"Force đóng Chrome cho {uid}")
            eel.updateAccountStatus(uid, "🔴 Đã dừng", "#f44747")
        except Exception as e:
            print(f"Lỗi khi đóng Chrome cho {uid}: {e}")
        chrome_drivers.pop(uid, None)
    
    uid_to_pass.clear()

def force_stop_all_threads():
    """Hàm này sẽ dừng tất cả các thread đang chạy"""
    global running_threads
    
    for thread in running_threads:
        if thread.is_alive():
            try:
                thread.join(timeout=0.1)  # Giảm timeout xuống rất thấp
            except:
                pass
    running_threads.clear()

@eel.expose
def stop_all_selenium():
    """Hàm dừng tất cả process ngay lập tức"""
    print("Đang dừng tất cả tiến trình...")
    
    global stop_flag
    stop_flag = True
    
    # Force stop all drivers first
    force_stop_all_drivers()
    # Force stop all threads
    force_stop_all_threads()
    # Then reset everything
    reset_all()
    
    # Thông báo UI
    eel.updateAccountStatus("ALL", "🔴 Đã dừng tất cả", "#f44747")
    print("Đã dừng tất cả process")
    return True