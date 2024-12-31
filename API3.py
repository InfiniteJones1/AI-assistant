from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import random
import time
import logging
from bs4 import BeautifulSoup
from typing import List, Dict
import pandas as pd

# 配置日志
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 初始化IP池
def init_ip_pool(pool_num: int) -> List[str]:
    proxies = [
        "15.236.106.236:3128", "206.81.31.215:80", "27.79.234.235:16000", 
        "27.79.133.199:16000", "3.78.92.159:3128", "27.76.102.235:16000", 
        "27.79.236.9:16000", "47.251.122.81:8888", "198.23.126.113:3128",
        "144.76.18.229:3128", "49.51.68.122:3128", "5.134.240.96:3128",
        "178.62.193.19:3128", "92.205.20.177:3128"
    ]
    logger.debug(f"Initializing IP pool with {pool_num} IPs.")
    ip_pool = random.sample(proxies, pool_num)  # 随机选择指定数量的代理
    logger.info(f"IP pool initialized with {len(ip_pool)} IPs.")
    return ip_pool

# 从IP池中随机选择一个代理并应用
def get_random_proxy(ip_pool: List[str]) -> Dict[str, str]:
    proxy = random.choice(ip_pool)
    logger.debug(f"Selected proxy: {proxy}")
    return {
        "http": f"http://{proxy}",
        "https": f"https://{proxy}"
    }

# 解析HTML并提取航班信息
def parse_flight_info(html):
    soup = BeautifulSoup(html, 'html.parser')
    flight_info = []
    flight_list = soup.find_all('ul', class_='newstyledetails1')
    
    if not flight_list:
        return None

    for flight in flight_list:
        time_from = flight.find('strong', class_='time_from').text.strip()
        time_to = flight.find('span', class_='time_to').text.strip()
        scity = flight.get('scity', '')
        ecity = flight.get('ecity', '')
        airline = flight.get('airline', '')
        flight_no = flight.find('span', class_='flight_airline').text.strip()
        aircraft = flight.find('span', class_='base_txtdiv')
        aircraft_model = aircraft.text.strip() if aircraft else 'N/A'
        price = flight.find('span', class_='base_price01')
        price_amount = price.find('strong').text.strip() if price else 'N/A'
        price_currency = price.find('dfn').text.strip() if price else 'N/A'

        flight_info.append({
            'time_from': time_from,
            'time_to': time_to,
            'scity': scity,
            'ecity': ecity,
            'airline': airline,
            'flight_no': flight_no,
            'aircraft_model': aircraft_model,
            'price': f'{price_currency}{price_amount}',
        })

    if not flight_info:
        return None
    return flight_info

# 模拟用户行为：加入随机延时
def random_sleep(min_sleep=2, max_sleep=5):
    sleep_time = random.uniform(min_sleep, max_sleep)
    time.sleep(sleep_time)


def findcode(city):
    """ 用来找到城市对应的三字码 """
    try:
        # 读取Excel文件，假设包含城市名称和三字码
        df = pd.read_excel("city3code.xlsx")
        # 假设Excel文件有“城市”列和“三字码”列
        citycode = df.loc[df['城市'] == city, '三字码'].values
        if citycode.size > 0:
            return citycode[0]  # 返回找到的三字码
        else:
            print("没有找到对应的城市三字码")
            return None
    except Exception as e:
        print(f"读取Excel文件时出错: {e}")
        return None

# 使用Selenium模拟完整的浏览器行为（如果需要处理JavaScript动态加载）
def fetch_flight_info_with_selenium(dict_info):
    fromcity = dict_info['出发地']
    tocity = dict_info['目的地']
    date = f"2025-{dict_info['出发日期']}"
    fromcitycode = findcode(fromcity)
    tocitycode = findcode(tocity)

    # 获取当前日期 (格式化为YYYYMMDD)
    currenttime = time.strftime("%Y%m%d")

    url = f"http://www.9935china-air.com/flight/showfarefirst.aspx?from={fromcitycode}&to={tocitycode}&__today__={currenttime}&FlightType=1&fc={fromcity}&tc={tocity}&date={date}"
    
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # 无头模式
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("window-size=1200x600")

    # 使用 webdriver-manager 来管理 Chrome 驱动并传递 options
    try:
        service = Service(ChromeDriverManager().install())  # 创建 Service 对象
        driver = webdriver.Chrome(service=service, options=chrome_options)  # 使用 Service 对象初始化 WebDriver
        logger.info("Chrome WebDriver initialized successfully.")
    except Exception as e:
        logger.error(f"Error initializing WebDriver: {e}")
        return None

    # 设置代理
    ip_pool = init_ip_pool(5)  # 需要定义这个函数
    proxy = get_random_proxy(ip_pool)  # 需要定义这个函数
    chrome_options.add_argument(f'--proxy-server={proxy["http"]}')  # 设置代理

    # 配置代理并打开 URL
    try:
        driver.get(url)
        logger.info(f"Navigated to {url}.")
    except Exception as e:
        logger.error(f"Error navigating to the page: {e}")
        driver.quit()
        return None

    try:
        # 打开页面后，模拟人工操作
        random_sleep(2, 5)  # 需要定义这个函数

        time.sleep(10)  # 增加等待时间以确保页面完全渲染

        # 获取页面源代码
        html = driver.page_source
        logger.debug(f"Page HTML: {html[:500]}...")  # 仅显示前500个字符，避免过长
        
        # 检查页面标题
        page_title = driver.title
        logger.debug(f"Page Title: {page_title}")

        flight_info = parse_flight_info(html)  # 需要定义这个函数

        if not flight_info:
            logger.error("No flight information found.")

        logger.info(f"Fetched {len(flight_info)} flight(s) information.")

        # 关闭浏览器
        driver.quit()

        return flight_info

    except Exception as e:
        logger.error(f"Error fetching data with Selenium: {e}")
        driver.quit()
        return None
