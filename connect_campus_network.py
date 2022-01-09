import argparse
import os
import subprocess
import time
import msvcrt
import logging
import schedule
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


class Network:
  def __init__(self, userId, password):
    super(Network, self).__init__()
    self.userId = userId      # 校园网账号
    self.password = password  # 校园网密码
    logging.basicConfig(filename='./network_reconnect.log',
                        level=logging.INFO,  # 定义输出log的类型
                        format='%(asctime)s %(filename)s : %(levelname)s %(message)s',  # 定义输出log的格式
                        datefmt='%Y-%m-%d %A %H:%M:%S',
                        filemode='w')

  def __call__(self):
    self.run_loop() # 第一次执行
    # 十分钟后判断是否需要重连
    schedule.every(10).minutes.do(self.run_loop)
    while True:
      schedule.run_pending()

  def ping_network(self, ip_or_domain):
    """
    Input: ip_or_domain, ip地址或者域名
    return: True or False, 网络连通性, True表示网络可连通
    """
    ping_cmd = 'ping %s -n 1' % ip_or_domain
    backinfo = subprocess.call(ping_cmd,
                               shell=True,
                               stdin=subprocess.PIPE,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE)
    # 0: 网络可连通, 1: 网络不可达
    ret = True if backinfo == 0 else False
    return ret

  def reconnect_network(self):
    campus_network_url = "http://192.168.50.3:8080/"  # 校园网登录页面
    chromedriver = "./chromedriver.exe"  # chromedriver.exe文件所在位置
    os.environ["webdriver.chrome.driver"] = chromedriver
    options = Options()
    # 取消DevTools listening on ws://127.0.0.1...提示
    options.add_experimental_option('excludeSwitches', ['enable-logging'])
    options.add_argument("--headless")                             # 以无窗口模式运行chromedriver程序
    browser = webdriver.Chrome(chromedriver, options=options)      # 模拟打开浏览器
    browser.get(campus_network_url)                                # 打开校园网登录页面
    browser.find_element_by_id("username").send_keys(self.userId)  # 输入账号
    time.sleep(1)
    browser.find_element_by_id("pwd_tip").click()                  # 点击登录显示隐藏密码输入框
    time.sleep(1)
    browser.find_element_by_id("pwd").send_keys(self.password)     # 输入密码
    time.sleep(1)
    browser.find_element_by_id("loginLink_div").click()            # 点击连接按钮
    time.sleep(2)
    reconnect_res = browser.title == "登录成功"
    browser.quit()
    return reconnect_res

  def run_loop(self):
    ping_baidu = 'www.baidu.com'  # 百  度
    ping_campus = '192.168.50.3'  # 校园网
    if self.ping_network(ping_baidu):
      print("校园网连接正常.")
      # logging.info("校园网连接正常")
    else:
      print("校园网未登录, 尝试重连中...")
      logging.info("校园网未登录, 尝试重连中...")
      if self.ping_network(ping_campus):
        reconnect_res = self.reconnect_network()
        if reconnect_res and self.ping_network(ping_baidu):
          print("校园网已使用账户%s重新登录." % self.userId)
          logging.info("校园网已使用账户%s重新登录." % self.userId)
        else:
          print("校园网未登录成功, 请检查账号密码是否输入正确!")
          print("您输入的用户名是: %s 密码: %s" % (self.userId, self.password))
          logging.info("校园网未登录成功, 请检查账号密码是否输入正确!")
      else:
        print("无法访问校园网登录页面, 请检查是否连接网络!")


def input_pwd(hint_word):
  print(hint_word, end='', flush=True)
  pwd = []
  while True:
    ch = msvcrt.getch()
    # 回车
    if ch == b'\r':
      msvcrt.putch(b'\n')
      break
    # 退格
    elif ch == b'\x08':
      if pwd:
        pwd.pop()
        msvcrt.putch(b'\b')
        msvcrt.putch(b' ')
        msvcrt.putch(b'\b')
    # Esc
    elif ch == b'\x1b':
      break
    else:
      pwd.append(ch)
      msvcrt.putch(b'*')
  return b''.join(pwd).decode()


if __name__ == '__main__':
  # 输入校园网帐号和密码
  parser = argparse.ArgumentParser(description='校园网断开自动重连')
  parser.add_argument('--user', type=str, default='', help='userId')
  parser.add_argument('--pwd', type=str, default='', help='password')
  args = parser.parse_args()
  userId = args.user
  password = args.pwd
  if userId == '' or password == '':
    print("请输入校园网账号密码!")
    userId = input("用户名: ")
    password = input_pwd("密  码: ")

  network = Network(userId, password)
  network()
