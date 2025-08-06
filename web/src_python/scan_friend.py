# Thêm biến để quản lý trạng thái scanning
import threading
import time
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import eel

# Biến global để quản lý trạng thái và threads
chrome_drivers = {}
scan_threads = []
stop_scanning = False  # Flag để dừng scanning

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

# Lớp xử lý scan friend
class main_scan_friend:
    def __init__(self, data_scan_friend, index):
        self.index = index
        options = Options()
        options.add_argument("--window-size=800,600")
        options.add_argument("--force-device-scale-factor=0.5")
        options.add_argument("--high-dpi-support=1")
        options.add_argument("--disable-infobars")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-software-rasterizer")
        options.add_argument("--disable-infobars")
        options.add_argument("--start-maximized")
        prefs = {
            "profile.default_content_setting_values.notifications": 2,
            "credentials_enable_service": False,
            "profile.password_manager_enabled": False
        }
        options.add_experimental_option("prefs", prefs)
        
        SCREEN_WIDTH = 1920
        SCREEN_HEIGHT = 1080
        WINDOW_WIDTH = 480
        WINDOW_HEIGHT = 400
        COLUMNS = SCREEN_WIDTH // WINDOW_WIDTH
        MARGIN = 0

        row = self.index // COLUMNS
        col = self.index % COLUMNS

        x = col * (WINDOW_WIDTH + MARGIN)
        y = row * (WINDOW_HEIGHT + MARGIN)
        
        self.driver = webdriver.Chrome(options=options)
        self.driver.set_window_position(x, y)
        self.driver.get("https://www.facebook.com")

    def login(self, cookie):
        c_user = get_cookie_value(cookie, 'c_user')
        chrome_drivers[c_user] = self.driver
        for c in cookie:
            c["domain"] = ".facebook.com"
            self.driver.add_cookie(c)
        self.driver.refresh()

    def wait_and_get_text(self, xpath, timeout=10):
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((By.XPATH, xpath))
            )
            return element.text
        except:
            return None
        
    def wait_and_click(self, xpath, timeout=30):
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.element_to_be_clickable((By.XPATH, xpath))
            )
            element.click()
        except Exception as e:
            print(f"Lỗi khi click vào {xpath}: {e}")

    def open_friend_list(self, uid):
        print(f"Đang mở danh sách bạn bè của UID: {uid}")
        self.driver.get(f"https://www.facebook.com/{uid}")

    def get_sources(self, uid=None):
        page_source = self.driver.page_source
        return page_source

    def get_friend_from_source(self, source):
        try:
            return source.split('[{"length":1,"offset":0,"inline_style":"BOLD"}],"aggregated_ranges":[],"ranges":[],"color_ranges":[],"text":"')[1].split(' znajomi"}')[0]
        except:
            return "UNKNOWN"

# Hàm chính scan với cải tiến
@eel.expose
def thread_scan_friend(data_scan_friend):
    global stop_scanning, scan_threads, chrome_drivers
    
    # Reset trạng thái
    stop_scanning = False
    scan_threads = []
    
    print("Data nhận được:", data_scan_friend)

    accounts = data_scan_friend['account']
    uid_list = data_scan_friend['uidList']
    delay = data_scan_friend.get('delay', 1000) / 1000  # ms -> s
    max_threads = min(data_scan_friend.get('thread', 3), len(accounts))

    # Phân chia UID theo số account (luồng)
    uid_chunks = [[] for _ in range(max_threads)]
    for i, uid in enumerate(uid_list):
        uid_chunks[i % max_threads].append(uid)

    # Hàm chạy từng luồng với kiểm tra stop_scanning
    def scan_uid_list(uid_sublist, acc, idx):
        global stop_scanning
        
        print(f"[Thread {idx}] Bắt đầu với {len(uid_sublist)} UID bằng account UID={acc['uid']}")
        instance = None
        
        try:
            instance = main_scan_friend(data_scan_friend, idx)

            # Đăng nhập nếu có cookie
            if acc.get('cookie'):
                cookies = convert_cookie_string_to_list(acc['cookie'])
                instance.login(cookies)

            for uid in uid_sublist:
                # Kiểm tra flag stop trước khi xử lý UID tiếp theo
                if stop_scanning:
                    print(f"[Thread {idx}] Đã nhận lệnh dừng, thoát khỏi vòng lặp")
                    break
                    
                try:
                    print(f"[Thread {idx}] Đang mở bạn bè UID: {uid}")
                    instance.open_friend_list(uid)
                    # Kiểm tra stop_scanning sau mỗi bước
                    if stop_scanning:
                        break
                        
                    # Kiểm tra trang die
                    check_xpath = "/html/body/div[1]/div/div[1]/div/div[3]/div/div/div[1]/div[1]/div/div/div[1]/div[2]/div[1]/h2/span"
                    text_check = instance.wait_and_get_text(check_xpath, timeout=5)

                    if text_check == "Te materiały nie są teraz dostępne":
                        eel.statusscan(uid, '956', "#f44747")  # Profile die
                        continue
                    
                    check_xpath = "/html/body/div[1]/div/div[1]/div/div[3]/div/div/div[1]/div[1]/div/div/div[1]/div[2]/div/div/div[1]/div[3]/div/div/div[2]/span/a/strong"
                    text_friend = instance.wait_and_get_text(check_xpath, timeout=0.1)

                    if text_friend == None:
                        eel.statusscan(uid, '000', "#4ec9b0")  # Không có bạn bè
                    else:
                        eel.statusscan(uid, text_friend, "#4ec9b0")

                    # # Delay giữa các UID
                    # if delay > 0:
                    #     time.sleep(delay)

                except Exception as e:
                    print(f"[Thread {idx}] Lỗi xử lý UID {uid}: {e}")
                    eel.statusscan(uid, 'ERR', "#f44747")

        except Exception as e:
            print(f"[Thread {idx}] Lỗi khởi tạo: {e}")
        finally:
            # Đảm bảo driver được đóng khi thread kết thúc
            if instance and hasattr(instance, 'driver'):
                try:
                    instance.driver.quit()
                    print(f"[Thread {idx}] Đã đóng Chrome driver")
                except:
                    pass
        try:
            eel.onScanComplete()
        except:
            pass

    # Tạo luồng ứng với mỗi account
    for i in range(max_threads):
        acc = accounts[i]
        t = threading.Thread(target=scan_uid_list, args=(uid_chunks[i], acc, i))
        t.start()
        scan_threads.append(t)

    # Chờ tất cả threads kết thúc
    for t in scan_threads:
        t.join()
    
    print("Tất cả threads đã kết thúc")

@eel.expose
def stop_all_selenium_scan():
    global stop_scanning, scan_threads, chrome_drivers
    
    print("Đang dừng tất cả Chrome Selenium scan...")
    
    # Đặt flag để dừng tất cả threads
    stop_scanning = True
    
    # Đóng tất cả Chrome drivers
    for uid, driver in list(chrome_drivers.items()):
        try:
            driver.quit()
            print(f"Đã đóng Chrome cho {uid}")
        except Exception as e:
            print(f"Lỗi đóng Chrome cho {uid}: {e}")
    
    # Xóa dictionary
    chrome_drivers.clear()
    
    # Chờ tất cả threads kết thúc (với timeout)
    for t in scan_threads:
        if t.is_alive():
            t.join(timeout=5)  # Chờ tối đa 5 giây
    
    scan_threads.clear()
    
    print("Đã dừng tất cả quá trình scan")
    
    # Cập nhật UI
    try:
        eel.statusscan("SYSTEM", "Đã dừng tất cả Chrome", "#f44747")
    except:
        pass