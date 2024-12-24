import json
from seleniumwire import webdriver
import cv2
import numpy as np
from paddlex import create_pipeline
import ocr
import time


class WebDriverManager:
    def __init__(self, url="http://zhjw.scu.edu.cn/login", config_path="config.json"):
        self.driver = None
        self.url = url
        self.captcha_result = None
        self.captcha_image = None
        self.username = None
        self.password = None
        # 需要抢的课程（列表）
        self.courses = None
        self.course_type = None
        self.load_config(config_path)

    def load_config(self, config_path):
        """从配置文件加载用户名和密码"""
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
                self.username = config.get("username")
                self.password = config.get("password")
                self.courses = config.get("courses")
                self.course_type = config.get("course_type")
        except Exception as e:
            print(f"读取配置文件失败: {str(e)}")
            raise
        # 否则交互式输入
        if not self.username:
            print("请输入用户名:")
            self.username = input()
        if not self.password:
            print("请输入密码:")
            self.password = input()
        if not self.courses:
            courses = []
            print("请输入需要抢的课程界面:")
            print("1. 方案选课")
            print("2. 系任选课")
            print("3. 校任选课")
            print("4. 自由选课")
            print("5. 重修选课")
            print("6. 复修选课")
            self.course_type = input()
            while True:
                course = input("请输入需要抢的课程编号:")
                course_number = input("请输入需要抢的课程序号:")
                courses.append(
                    {
                        "course": course,
                        "course_number": course_number,
                    }
                )
                print("是否继续添加课程？(y/n)")
                if input() != "y":
                    self.courses = courses
                    break

    def initialize_driver(self):
        """初始化Edge浏览器驱动"""
        self.driver = webdriver.Edge()
        self.driver.implicitly_wait(10)
        self.driver.get(self.url)

    def capture_and_process_captcha(self):
        """捕获并处理验证码"""
        for request in self.driver.requests:
            if request.response and request.url.endswith("captcha.jpg"):
                self.captcha_image = cv2.imdecode(
                    np.frombuffer(request.response.body, np.uint8), cv2.IMREAD_COLOR
                )
                cv2.imwrite("captcha.png", self.captcha_image)
                self.captcha_result = ocr.ocr_image(self.captcha_image)
                return True
        return False

    def verify_captcha(self):
        """验证码人工确认"""
        print("请验证识别是否正确:", self.captcha_result)
        print("更正请输入验证码，否则请按回车键继续")
        user_captcha_result = input()
        if user_captcha_result:
            self.captcha_result = user_captcha_result

    def input_captcha(self):
        """输入验证码"""
        try:
            captcha_input_element = self.driver.find_element(
                by="id", value="input_checkcode"
            )
            captcha_input_element.send_keys(self.captcha_result)
        except Exception as e:
            print(f"输入验证码时出错: {str(e)}")

    def input_credentials(self):
        """输入用户名和密码"""
        try:
            username_element = self.driver.find_element(by="id", value="input_username")
            password_element = self.driver.find_element(by="id", value="input_password")

            username_element.send_keys(self.username)
            password_element.send_keys(self.password)
        except Exception as e:
            print(f"输入账号密码时出错: {str(e)}")
            raise

    def click_login(self):
        """点击登录按钮"""
        try:
            login_button = self.driver.find_element(by="id", value="loginButton")
            login_button.click()
        except Exception as e:
            print(f"点击登录按钮时出错: {str(e)}")
            raise

    def check_login(self):
        """检查是否登录成功"""
        try:
            self.driver.find_element(by="id", value="loginButton")
            return False
        except:
            return True

    def navigate_to_course_selection(self):
        """导航到选课界面"""
        try:
            course_register = self.driver.find_element(by="id", value="1002000000")
            course_register.click()
            course_register = self.driver.find_element(by="id", value="1002001002")
            course_register.click()
            element_id = None
            switcher = {
                "1": "faxk",
                "2": "xirxk",
                "3": "xarxk",
                "4": "zyxk",
                "5": "cxxk",
                "6": "fxxk",
            }
            element_id = switcher.get(self.course_type)
            course_register = self.driver.find_element(by="id", value=element_id)
            course_register.click()
        except Exception as e:
            print(f"导航到选课界面时出错: {str(e)}")
            raise

    def switch_to_course_frame(self):
        """切换到选课iframe"""
        try:
            self.driver.switch_to.frame("ifra")
        except Exception as e:
            print(f"切换到选课iframe时出错: {str(e)}")
            raise

    def switch_to_main_frame(self):
        """切换到主iframe"""
        try:
            self.driver.switch_to.default_content()
        except Exception as e:
            print(f"切换到主iframe时出错: {str(e)}")
            raise

    def capture_and_find_course(self):
        """捕获并查找课程"""
        for request in self.driver.requests:
            if request.response and request.url.endswith("courseList"):
                course_list = json.loads(request.response.body)
                course_list = course_list.get("rwXarxkZlList")
                for course in course_list:
                    kch = course.get("kch")
                    kxh = course.get("kxh")
                    for m_course in self.courses:
                        if (
                            m_course["course"] == kch
                            and m_course["course_number"] == kxh
                        ):
                            bkskyl = course.get("bkskyl")
                            print(f"找到课程: {kch}_{kxh}，剩余名额: {bkskyl}")
                            if bkskyl != 0:
                                return True
        return False

    def select_course(self) -> bool:
        """选择课程"""
        result = False
        try:
            for course in self.courses:
                try:
                    print(
                        f"选择课程: {course['course']}_{course['course_number']}\n查找中..."
                    )
                    course_id = f"{course['course']}_{course['course_number']}"
                    xpath = f"//input[starts-with(@id, '{course_id}')]"
                    course_checkbox = self.driver.find_element(by="xpath", value=xpath)
                    course_checkbox.click()
                    result = True
                except:
                    continue
        except Exception as e:
            print(f"选择课程时出错: {str(e)}")
            raise
        return result

    def submit(self):
        """提交选课"""
        print("提交选课")
        try:
            submit_button = self.driver.find_element(by="id", value="submitButton")
            submit_button.click()
        except Exception as e:
            print(f"提交选课时出错: {str(e)}")
            raise

    def refresh(self):
        """刷新列表"""
        print("刷新列表")
        try:
            refresh_button = self.driver.find_element(by="id", value="queryButton")
            refresh_button.click()
        except Exception as e:
            print(f"提交选课时出错: {str(e)}")
            raise

    def run(self):
        """执行完整流程"""
        try:
            self.initialize_driver()
            while not self.check_login():
                self.input_credentials()
                if self.capture_and_process_captcha():
                    self.verify_captcha()
                    self.input_captcha()
                    self.click_login()
            self.navigate_to_course_selection()
            self.switch_to_course_frame()
            while True:
                if not self.capture_and_find_course():
                    self.refresh()
                    continue
                if self.select_course():
                    self.switch_to_main_frame()
                    self.submit()
                    break
                else:
                    self.refresh()

        except Exception as e:
            print(f"执行过程中出错: {str(e)}")
            raise
        finally:
            self.close()

    def close(self):
        """关闭浏览器"""
        if self.driver:
            input("按回车键关闭浏览器")
            self.driver.quit()


# 使用示例
if __name__ == "__main__":
    manager = WebDriverManager()
    try:
        manager.run()
    finally:
        manager.close()
