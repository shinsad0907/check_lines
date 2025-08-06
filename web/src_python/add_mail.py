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


thread_lock = threading.Lock()
is_running = False
class main_add_mail:
    def __init__(self, data_add_mail, index):
        # ...existing code...
        self.email = data_add_mail['email']  # Store the source email
        self.password = data_add_mail['password']  # Store the password
        scale = 0.5

        options = webdriver.ChromeOptions()
        options.add_argument(f"--force-device-scale-factor={scale}")
        options.add_argument("--disable-infobars")
        options.add_argument("--disable-extensions")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)

        self.driver = webdriver.Chrome(options=options)
        screen_width = 3840
        screen_height = 2160

        # Cấu hình scale

        # Tính số cột và hàng cần
        cols = 5
        rows = 4  # 5 x 4 = 20 cửa sổ

        # Kích thước cửa sổ thực tế = chia màn hình ra, rồi chia thêm theo scale
        window_width = int((screen_width / cols) * (1 / scale))
        window_height = int((screen_height / rows) * (1 / scale))
        # Vị trí cửa sổ
        col = index % cols
        row = index // cols
        x = int((screen_width / cols) * col)
        y = int((screen_height / rows) * row)

        # Đặt kích thước và vị trí
        self.driver.set_window_size(window_width, window_height)
        self.driver.set_window_position(x, y)

        self.driver.get("https://konto.onet.pl/en/signin?")

        # Thêm các hàm helper
    def click_first_available(self, xpaths, timeout=10):
        """Click vào element đầu tiên tìm thấy từ danh sách xpath"""
        for xpath in xpaths:
            try:
                element = WebDriverWait(self.driver, timeout).until(
                    EC.element_to_be_clickable((By.XPATH, xpath))
                )
                element.click()
                time.sleep(1)  # Chờ sau mỗi click
                return True
            except:
                continue
        return False

    def input_text_to_first_available(self, xpaths, text, timeout=10):
        """Nhập text vào element đầu tiên tìm thấy từ danh sách xpath"""
        for xpath in xpaths:
            try:
                element = WebDriverWait(self.driver, timeout).until(
                    EC.presence_of_element_located((By.XPATH, xpath))
                )
                element.clear()
                element.send_keys(text)
                time.sleep(1)  # Chờ sau khi nhập
                return True
            except:
                continue
        return False

    def wait_for_url_change(self, timeout=10):
        """Chờ đợi URL thay đổi"""
        try:
            WebDriverWait(self.driver, timeout).until(
                lambda driver: "ustawienia.poczta.onet.pl" in driver.current_url
            )
            return True
        except:
            return False
    def wait_and_click(self, xpath, timeout=10):
        """Đợi và click vào element"""
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.element_to_be_clickable((By.XPATH, xpath))
            )
            element.click()
            time.sleep(1)
            return True
        except Exception as e:
            print(f"Không thể click element: {xpath}")
            print(f"Error: {str(e)}")
            return False

    def wait_and_send_keys(self, xpath, text, timeout=10):
        """Đợi và nhập text vào element"""
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((By.XPATH, xpath))
            )
            element.clear()
            element.send_keys(text)
            time.sleep(1)
            return True
        except Exception as e:
            print(f"Không thể nhập text vào element: {xpath}")
            print(f"Error: {str(e)}")
            return False

    def wait_and_get_text(self, xpath, timeout=10):
        """Đợi và lấy text từ element"""
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((By.XPATH, xpath))
            )
            return element.text
        except Exception as e:
            print(f"Không thể lấy text từ element: {xpath}")
            print(f"Error: {str(e)}")
            return ""

    def login(self, mail, password):
        # try:
        print(f"Đang đăng nhập với email: {mail}")
        
        # 1. Xử lý nút Accept cookie nếu có
        cookie_buttons = [
            "//button[contains(text(), 'Accept')]",
            "//button[contains(text(), 'ACCEPT')]",
            "//button[contains(@class, 'cookie-accept')]",
            "/html/body/div[5]/div/div[2]/div/div[6]/button[2]",
            "/html/body/div[4]/div/div[2]/div/div[6]/button[2]",
            "/html/body/div[3]/div/div[2]/div/div[6]/button[2]"
        ]
        
        self.click_first_available(cookie_buttons)

        # 2. Nhập email
        email_fields = [
            "//input[@type='email']",
            "//input[@name='email']", 
            "//input[contains(@placeholder, 'email')]",
            "/html/body/div[1]/main/div/div[1]/div[1]/div/div[1]/div/div[2]/form/div[1]/div/div[2]/div[1]/input"
        ]
        
        if not self.input_text_to_first_available(email_fields, mail):
            raise Exception("Không thể nhập email")

        # 3. Click nút Next/Continue sau khi nhập email
        next_buttons = [
            "//button[contains(text(), 'Next')]",
            "//button[contains(text(), 'Continue')]",
            "//button[@type='submit']",
            "/html/body/div[1]/main/div/div[1]/div[1]/div/div[1]/div/div[2]/form/div[2]/div/button"
        ]
        
        if not self.click_first_available(next_buttons):
            raise Exception("Không thể click nút Next")

        # 4. Nhập password 
        password_fields = [
            "//input[@type='password']",
            "//input[@name='password']",
            "/html/body/div[1]/main/div/div[1]/div[1]/div/div[1]/div/div[2]/form/div[3]/div[2]/div[1]/input"
        ]
        
        if not self.input_text_to_first_available(password_fields, password):
            raise Exception("Không thể nhập password")

        # 5. Click nút Login/Sign in
        login_buttons = [
            "//button[contains(text(), 'Login')]",
            "//button[contains(text(), 'Sign in')]", 
            "//button[@type='submit']",
            "/html/body/div[1]/main/div/div[1]/div[1]/div/div[1]/div/div[2]/form/div[4]/div/button"
        ]
        
        if not self.click_first_available(login_buttons):
            raise Exception("Không thể click nút Login")

        # # 6. Verify login success
        # time.sleep(3)  # Chờ redirect
        # if "ustawienia.poczta.onet.pl" not in self.driver.current_url:
        #     raise Exception("Login không thành công")

        return True

        # except Exception as e:
        #     print(f"Lỗi đăng nhập: {str(e)}")
        #     return False
    def check_add(self):
        if "Nie" in self.wait_and_get_text("/html/body/div[2]/div/div[3]/div/div/div/div[2]").split():
            return False, 'Alias'
        elif "Alias" in self.wait_and_get_text("/html/body/div[2]/div/div[3]/div/div/div/div[2]").split():
            return False, "Alias"
        return True, "Success"
    def navigate_to_settings(self):
        """Navigate to mail settings page after login"""
        try:
            self.driver.get("https://ustawienia.poczta.onet.pl/Konto/AlternatywneAdresy") 
            self.driver.get("https://ustawienia.poczta.onet.pl/Konto/AlternatywneAdresy") 
            self.driver.get("https://ustawienia.poczta.onet.pl/Konto/AlternatywneAdresy") 
            return True
        except:
            return False
    def add_mail(self, mail):
        try:
            # Click nút Add Mail ngay lập tức
            xpath_options = [
                "/html/body/div[2]/div/div[2]/div/div/section/div/div[2]/button",
                "/html/body/div[2]/div/div[2]/div/div/section/div/div[3]/button", 
                "/html/body/div[2]/div/div[2]/div/div/section/div/div[4]/button",
            ]
            
            # Tìm và click nút add mail không cần delay
            click_success = False
            for xpath in xpath_options:
                try:
                    element = WebDriverWait(self.driver, 2).until(
                        EC.element_to_be_clickable((By.XPATH, xpath))
                    )
                    element.click()
                    click_success = True
                    break
                except:
                    continue

            if not click_success:
                return None, "Không thể click nút Add Mail"

            # Nhập mail mới không cần delay
            input_xpath = "/html/body/div[2]/div/div[2]/div/div/section/div/form/div[2]/div/div[1]/div/div/div/input"
            try:
                element = WebDriverWait(self.driver, 2).until(
                    EC.presence_of_element_located((By.XPATH, input_xpath))
                )
                element.clear()
                element.send_keys(mail)
            except:
                return None, "Không thể nhập mail"

            # Click nút Add ngay lập tức
            add_button_xpath = "/html/body/div[2]/div/div[2]/div/div/section/div/form/div[2]/div/div[2]/div/div[2]/button"
            try:
                element = WebDriverWait(self.driver, 2).until(
                    EC.element_to_be_clickable((By.XPATH, add_button_xpath))
                )
                element.click()
            except:
                return None, "Không thể click nút Add"
            
            # Kiểm tra kết quả nhanh
            check_result, message = self.check_add()
            if check_result:
                print("Đã thêm mail thành công:", mail)
                return mail, message
            else:
                print("Thêm mail thất bại:", mail, "- Lỗi:", message) 
                return None, message
                    
        except Exception as e:
            print(f"Lỗi khi add mail: {str(e)}")
            return None, str(e)
    def close(self):
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
            
    def __del__(self):
        self.close()

    def main(self):
        pass

# Thêm biến global để lưu kết quả
results = []

def login_thread(source_mail, index):
    """Thread function để xử lý login cho từng instance"""
    global browser_instances, mail_status
    try:
        instance = main_add_mail(source_mail, index)
        with thread_lock:
            browser_instances.append(instance)
        
        login_success = instance.login(source_mail['email'], source_mail['password'])
        if login_success:
            instance.navigate_to_settings()
            print(f"Đăng nhập và mở trang settings thành công: {source_mail['email']}")
        
        with thread_lock:
            mail_status[source_mail['email']] = {
                'status': 'Success' if login_success else 'Failed',
                'message': 'Đăng nhập thành công' if login_success else 'Lỗi đăng nhập'
            }
            
            # Update UI
            eel.updateAddMailProgress({
                'processed': len(mail_status),
                'success': sum(1 for status in mail_status.values() if status['status'] == 'Success'),
                'failed': sum(1 for status in mail_status.values() if status['status'] == 'Failed'),
                'mailStatus': mail_status
            })
    except Exception as e:
        print(f"Error in login_thread for {source_mail['email']}: {str(e)}")
        with thread_lock:
            mail_status[source_mail['email']] = {
                'status': 'Failed',
                'message': str(e)
            }
def add_mail_thread(instance, mails, mail_status):
    global is_running, results
    try:
        total_processed = 0
        success = 0
        failed = 0
        current_results = []
        
        for mail in mails:
            if not is_running:
                break
            
            try:
                result, message = instance.add_mail(mail['email'])
                total_processed += 1
                
                if result:
                    success += 1
                    current_results.append({
                        'email': mail['email'],
                        'password': mail['password'],
                        'message': message,
                        'source_mail': instance.email  # Now this will work
                    })
                else:
                    failed += 1
                    current_results.append({
                        'email': mail['email'],
                        'error': message,
                        'source_mail': instance.email
                    })
                
                # Update UI progress
                with thread_lock:
                    eel.updateAddMailProgress({
                        'processed': total_processed,
                        'success': success,
                        'failed': failed,
                        'results': current_results,
                        'mailStatus': mail_status
                    })
            except Exception as e:
                print(f"Error processing mail {mail['email']}: {str(e)}")
                failed += 1
                current_results.append({
                    'email': mail['email'],
                    'error': str(e),
                    'source_mail': getattr(instance, 'email', 'Unknown')
                })
            
            time.sleep(0.05)
            
    except Exception as e:
        print(f"Error in add_mail_thread: {str(e)}")
browser_instances = []

@eel.expose 
def add_mail_process(data):
    global is_running, browser_instances
    try:
        print("Received data:", data)
        source_mails = data['data']['sourceMails']
        input_mails = data['data']['inputMails'] 
        config = data['data']['config']
        thread_count = config['threadCount']  # Lấy số thread từ config
        
        # Initialize counters
        processed = 0
        success = 0
        failed = 0
        mail_status = {}

        # Nếu là lệnh login mới
        if not input_mails:
            browser_instances = []
            threads = []
            
            # Sử dụng đúng số thread được cấu hình
            for i in range(thread_count):
                if i < len(source_mails):  # Chỉ tạo thread nếu còn mail nguồn
                    thread = threading.Thread(
                        target=login_thread,
                        args=(source_mails[i], i)
                    )
                    threads.append(thread)
                    thread.start()

            # Đợi tất cả thread hoàn thành
            for thread in threads:
                thread.join()

            return {
                'success': True,
                'mailStatus': mail_status
            }

        # Nếu là lệnh add mail
        is_running = True
        results = []
        
        # Phân chia mail cần add cho các instance
        if len(input_mails) > 0 and browser_instances:
            mail_chunks = [input_mails[i::len(browser_instances)] for i in range(len(browser_instances))]
            
            threads = []
            for i, instance in enumerate(browser_instances):
                if i < len(mail_chunks):
                    thread = threading.Thread(
                        target=add_mail_thread,
                        args=(instance, mail_chunks[i], mail_status)
                    )
                    threads.append(thread)
                    thread.start()

            # Đợi tất cả thread hoàn thành
            for thread in threads:
                thread.join()

        return {
            'success': True,
            'mailStatus': mail_status,
            'results': results
        }
        
    except Exception as e:
        print(f"Error in add_mail_process: {str(e)}")
        return {
            'success': False,
            'message': str(e)
        }
    finally:
        # Chỉ set is_running = False, KHÔNG đóng browser
        is_running = False