import re
import json
import time
import random
import redis
import requests
from Tools.Yundama_Http import Yundama
from fake_useragent import UserAgent
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import WebDriverException, TimeoutException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from Tools.Account_Into_Redis import user_pass_item


class CookiesGenerator(object):
    def __init__(self):
        # options = webdriver.ChromeOptions()
        # options.add_argument("--proxy-server=http://{0}".format(ip))
        self.db_account = redis.StrictRedis(host='127.0.0.1', port=6379, db=3, decode_responses=True)
        self.db_cookie = redis.StrictRedis(host='127.0.0.1', port=6379, db=4, decode_responses=True)
        self.browser = webdriver.Chrome(executable_path="A:/PythonVirtualenv/spider-env/chromedriver.exe")
        # self.browser = webdriver.Chrome(executable_path="A:/PythonVirtualenv/spider-env/chromedriver.exe",
        #                                 chrome_options=options)

    def run(self):
        for info in user_pass_item():
            username = info[0]
            password = info[1]
            itemname = info[2]
            cookie = self.get_cookie(username, password)
            if cookie:
                self.save_cookie(cookie, username, itemname)
                print('Generator Run Finished')

    def get_cookie(self, username, password):
        raise NotImplementedError

    def save_cookie(self, cookie, username, itemname):
        self.db_cookie.set("{0}:{1}:{2}".format("cookie", itemname, username), cookie)

    def close(self):
        try:
            print('Closing Browser')
            self.browser.close()
            del self.browser
        except TypeError:
            print('Browser not opened')


class DianpingCookiesGenerator(CookiesGenerator):
    def __init__(self):
        CookiesGenerator.__init__(self)
        YUNDAMA_USERNAME = 'username'
        YUNDAMA_PASSWORD = 'password'
        YUNDAMA_APP_ID = "appId"
        YUNDAMA_APP_KEY = 'appkey'
        YUNDAMA_API_URL = 'http://api.yundama.com/api.php'
        self.ydm = Yundama(YUNDAMA_USERNAME, YUNDAMA_PASSWORD, YUNDAMA_APP_ID, YUNDAMA_APP_KEY, YUNDAMA_API_URL)

    def check_login(self):
        mycenter = WebDriverWait(driver=self.browser, timeout=20).until(
            EC.presence_of_element_located((By.XPATH, '//a[@class="item left-split username J-user-trigger"]'))
        )
        if mycenter:
            print('登录成功')
            self.browser.find_element_by_xpath('//*[@id="top-nav"]/div/div[2]/span[2]/a[1]').click()
            time.sleep(1)
            print("获取cookie:", self.browser.get_cookies())
            cookies = {}
            for cookie in self.browser.get_cookies():
                cookies[cookie['name']] = cookie['value']
            print("获取cookie成功:", json.dumps(cookies))
            return json.dumps(cookies)

    def get_cookie(self, username, password):
        try:
            self.browser.delete_all_cookies()
            self.browser.get('https://account.dianping.com/login?redir=http://www.dianping.com')
            time.sleep(1)
            iframe = self.browser.find_element_by_xpath('/html/body/div[3]/div/div/div/div/iframe')
            self.browser.switch_to.frame(iframe)
            self.browser.find_element_by_class_name('icon-pc').click()
            self.browser.find_element_by_id('tab-account').click()
            self.browser.find_element_by_id('account-textbox').send_keys(username)
            self.browser.find_element_by_id('password-textbox').send_keys(password)
            self.browser.find_element_by_class_name('login-button').click()
            try:
                cookie = self.check_login()
                if cookie:
                    return cookie
            except TimeoutException:
                print('出现验证码，开始识别验证码')
                captcha = WebDriverWait(driver=self.browser, timeout=20).until(
                    EC.visibility_of_element_located((By.XPATH, '//div[@id="captcha-account-container"]/div[2]/img'))
                )
                captcha_url = captcha.get_attribute('src')
                headers = {
                    'User-Agent': UserAgent().random
                }

                response = requests.get(captcha_url, headers=headers)
                result = self.ydm.identify(stream=response.content)
                if not result:
                    print('验证码识别失败, 跳过识别')
                    return
                text_box = WebDriverWait(driver=self.browser, timeout=20).until(
                    EC.presence_of_element_located((By.XPATH, '//input[@id="captcha-textbox-account"]'))
                )
                text_box.send_keys(result)
                self.browser.find_element_by_class_name('login-button').click()
                result = self.check_login()
                if result:
                    return result

        except WebDriverException as e:
            print(e.args)


class TwitterCookiesGenerator(CookiesGenerator):

    def get_cookie(self, username, password):
        try:
            self.browser.delete_all_cookies()
            self.browser.get('https://mobile.twitter.com/login')
            WebDriverWait(driver=self.browser, timeout=20).until(
                EC.presence_of_element_located((By.XPATH, '//h1[@role="heading"]')))
            self.browser.find_element_by_xpath('//input[contains(@placeholder, "电话、邮件地址或用户名")]').send_keys(username)
            time.sleep(random.uniform(1, 2))
            self.browser.find_element_by_xpath('//input[contains(@placeholder, "密码")]').send_keys(password)
            time.sleep(random.uniform(1, 2))
            self.browser.find_element_by_xpath('//div[@data-testid="login-button"]').click()
            success = WebDriverWait(self.browser, 20).until(
                EC.presence_of_element_located((By.XPATH, '//div[contains(@class, "rn-15d164r rn-bcqeeo")]')))
            if success:
                print("登陆成功！")
                print("获取cookie:", self.browser.get_cookies())
                cookies = {}
                for cookie in self.browser.get_cookies():
                    cookies[cookie['name']] = cookie['value']
                print("获取cookie成功:", json.dumps(cookies))
                return json.dumps(cookies)
        except TimeoutException:
            print('请求超时')


class _36krCookiesGenerator(CookiesGenerator):

    def __init__(self):
        CookiesGenerator.__init__(self)
        self.headers = {
            "User-Agent": "36kr-Tou-iOS/3.0.1 (iPhone6S) (UID:-1); iOS 9.3.2; Scale/2.0",
            "Host": "rong.36kr.com"
        }
        self.login_url = "https://rong.36kr.com/api/passport/v1/ulogin"

    def get_cookie(self, username, password):
        print(f"开始登录,账号:username={username},password={password}")
        formdata = {
            "email": username,
            "password": password,
            "type": "EMAIL"
        }
        response = requests.post(url=self.login_url, data=formdata, headers=self.headers)
        text_json = json.loads(response.text)
        cookie = self.check_login(text_json, username, response)
        if cookie:
            return cookie

    def check_login(self, text, username, response):
        if "成功" in text.get('msg') and response.status_code == 200:
            print(f"账号:username={username}登录成功")
            cookies = response.cookies.get_dict()
            print(f"cookies:cookies={cookies}")
            return json.dumps(cookies)


class ItOrangeCookiesGenerator(CookiesGenerator):
    def get_cookie(self, username, password):
        try:
            self.browser.delete_all_cookies()
            self.browser.get('https://www.itjuzi.com/user/login')
            WebDriverWait(driver=self.browser, timeout=20).until(
                EC.presence_of_element_located((By.XPATH, '//button[@id="login_btn"]'))
            )
            self.browser.find_element_by_name('identity').send_keys(username)
            self.browser.find_element_by_name('password').send_keys(password)
            self.browser.find_element_by_id('login_btn').click()
            cookie = self.check_login()
            if cookie:
                return cookie
        except TimeoutException as e:
            print(e)

    def check_login(self):
        mycenter = WebDriverWait(driver=self.browser, timeout=20).until(
            EC.presence_of_element_located((By.XPATH, '//a[@id="loginurl"]'))
        )
        if mycenter:
            print('登录成功')
            print("获取cookie:", self.browser.get_cookies())
            cookies = {}
            for cookie in self.browser.get_cookies():
                cookies[cookie['name']] = cookie['value']
            print("获取cookie成功:", json.dumps(cookies))
            return json.dumps(cookies)


class WeibocnCookieGenerator(CookiesGenerator):
    def __init__(self):
        CookiesGenerator.__init__(self)
        self.login_url = 'https://passport.weibo.cn/signin/login?entry=mweibo&r=https://weibo.cn/'

    def get_cookie(self, username, password):
        try:
            self.browser.delete_all_cookies()
            self.browser.get(self.login_url)
            username_btn = WebDriverWait(driver=self.browser, timeout=30).until(
                EC.presence_of_element_located((By.ID, 'loginName')))
            password_btn = WebDriverWait(driver=self.browser, timeout=30).until(
                EC.presence_of_element_located((By.ID, 'loginPassword')))
            submit = WebDriverWait(driver=self.browser, timeout=30).until(
                EC.element_to_be_clickable((By.ID, 'loginAction')))
            username_btn.send_keys(username)
            password_btn.send_keys(password)
            submit.click()

            WebDriverWait(self.browser, 30).until(
                EC.title_is('我的首页')
            )

            cookies = {}
            for cookie in self.browser.get_cookies():
                cookies[cookie['name']] = cookie['value']
            print("获取cookie成功:", json.dumps(cookies))
            return json.dumps(cookies)

        except WebDriverException as e:
            print(e.args)


if __name__ == '__main__':
    # Generator = DianpingCookiesGenerator()
    # Generator = TwitterCookiesGenerator()
    # Generator = _36krCookiesGenerator()
    Generator = WeibocnCookieGenerator()
    Generator.run()
