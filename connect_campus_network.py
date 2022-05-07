import argparse
import subprocess
import time
import msvcrt
import logging
import schedule
import requests
import urllib.parse
# import os
# from selenium import webdriver
# from selenium.webdriver.chrome.options import Options

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
    return backinfo == 0

  def get_info(self):
      redirect_host = 'http://123.123.123.123'
      headers = {
          "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
          "Accept-Encoding": "gzip, deflate",
          "Accept-Language": "zh-CN,zh;q=0.9,tr;q=0.8,en-US;q=0.7,en;q=0.6",
          "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36",
          "Upgrade-Insecure-Requests": "1",
          "Host": "123.123.123.123",
          "Proxy-Connection": "keep-alive"
      }
      info = {}
      res = requests.get(redirect_host, headers=headers).content.decode()
      info["url"] = res[res.find('http:'):res.find('eportal')]
      info["querystr"] = res[(res.find("wlanuserip")):(res.find("'</script>"))]
      if not info["querystr"]:
          logging.info("网络似乎正常.")
      # 需要进行encodeURI编码
      info["querystr"] = urllib.parse.quote(info["querystr"])
      return info

  def relogin(self):
      info = self.get_info()
      url = info["url"] + "eportal/InterFace.do?method=login"
      headers = {
          "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.45 Safari/537.36",
          "Content-Type": "application/x-www-form-urlencoded",
          "charset": "UTF-8",
      }
      data = "userId=%s&password=%s&service=&queryString=%s&operatorPwd=&operatorUserId=&validcode=&passwordEncrypt=false" % (self.userId, self.password, info["querystr"])

      session = requests.session()
      req = session.post(url=url, headers=headers, data=data).json()
      return req["result"] == "success"

  # def reconnect_network(self):
  #   campus_network_url = "http://192.168.50.3:8080/"  # 校园网登录页面
  #   chromedriver = "./chromedriver.exe"  # chromedriver.exe文件所在位置
  #   os.environ["webdriver.chrome.driver"] = chromedriver
  #   options = Options()
  #   # 取消DevTools listening on ws://127.0.0.1...提示
  #   options.add_experimental_option('excludeSwitches', ['enable-logging'])
  #   options.add_argument("--headless")                             # 以无窗口模式运行chromedriver程序
  #   browser = webdriver.Chrome(chromedriver, options=options)      # 模拟打开浏览器
  #   reconnect_res = False
  #   try:
  #     browser.get(campus_network_url)                                # 打开校园网登录页面
  #     browser.find_element_by_id("username").send_keys(self.userId)  # 输入账号
  #     time.sleep(1)
  #     browser.find_element_by_id("pwd_tip").click()                  # 点击登录显示隐藏密码输入框
  #     time.sleep(1)
  #     browser.find_element_by_id("pwd").send_keys(self.password)     # 输入密码
  #     time.sleep(1)
  #     browser.find_element_by_id("loginLink_div").click()            # 点击连接按钮
  #     time.sleep(2)
  #     reconnect_res = browser.title == "登录成功"
  #   except Exception as e:
  #     print(e)
  #   finally:
  #     browser.quit()
  #   return reconnect_res

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
        reconnect_res = self.relogin()
        # reconnect_res = self.reconnect_network()  # 使用chromium模拟登录
        time.sleep(3)  # 等待3秒钟再判断是否登录成功
        if reconnect_res and self.ping_network(ping_baidu):
          print("校园网已使用账户%s重新登录." % self.userId)
          logging.info("校园网已使用账户%s重新登录." % self.userId)
        else:
          print("校园网未登录成功, 请检查账号密码是否输入正确!")
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
  parser.add_argument('--uid', type=str, default='', help='userId')
  parser.add_argument('--pwd', type=str, default='', help='password')
  args = parser.parse_args()
  userId = args.uid
  password = args.pwd
  if userId == '' or password == '':
    print("请输入校园网账号密码!")
    userId = input("用户名: ")
    password = input_pwd("密  码: ")

  network = Network(userId, password)
  network()
