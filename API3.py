import random
import time
import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from typing import Dict, List
import requests

# 配置日志
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 初始化IP池
def init_ip_pool(pool_num: int) -> List[str]:
    proxies = [
        "114.130.86.145:5443",
        "206.81.31.215:80",
        "27.79.252.95:16000",
        "27.79.251.38:16000",
        "27.79.146.35:16000"
    ]
    logger.debug(f"Initializing IP pool with {pool_num} IPs.")
    ip_pool = random.sample(proxies, pool_num)  # 随机选择指定数量的代理
    logger.info(f"IP pool initialized with {len(ip_pool)} IPs.")
    return ip_pool

# 从IP池中随机选择一个代理
def get_random_proxy(ip_pool: List[str]) -> Dict[str, str]:
    proxy = random.choice(ip_pool)
    logger.debug(f"Selected proxy: {proxy}")
    return {
        "http": f"http://{proxy}",
        "https": f"https://{proxy}"
    }

# 构造请求数据
def construct_payload(dict_info: Dict[str, str]) -> Dict[str, str]:
    from_city = dict_info.get('出发地', '')
    to_city = dict_info.get('目的地', '')
    departure_date = dict_info.get('出发日期', '')
    return_date = dict_info.get('返回日期', '无')
    flight_type = "2" if return_date != "无" else "1"  # 单程为1，往返为2

    payload = {
        "from": "PEK",
        "to": "SHA",
        "FlightType": flight_type,
        "sc": from_city,
        "ec": to_city,
        "sd": "2025-01-03",
        "too": "0",
    }
    logger.debug(f"Payload constructed: {payload}")
    return payload

# 解析HTML并提取航班信息
def parse_flight_info(html):
    # 使用 BeautifulSoup 解析 HTML 内容
    soup = BeautifulSoup(html, 'html.parser')

    flight_info = []

    # 找到航班列表（ul class="newstyledetails1"）
    flight_list = soup.find_all('ul', class_='newstyledetails1')
    
    if not flight_list:
        return None

    # 解析每个航班的信息
    for flight in flight_list:
        # 起飞时间和到达时间
        time_from = flight.find('strong', class_='time_from').text.strip()
        time_to = flight.find('span', class_='time_to').text.strip()
        
        # 出发和到达城市
        scity = flight.get('scity', '')
        ecity = flight.get('ecity', '')
        
        # 航空公司和航班号
        airline = flight.get('airline', '')
        flight_no = flight.find('span', class_='flight_airline').text.strip()

        # 机型
        aircraft = flight.find('span', class_='base_txtdiv')
        if aircraft:
            aircraft_model = aircraft.text.strip()
        else:
            aircraft_model = 'N/A'

        # 价格信息
        price = flight.find('span', class_='base_price01')
        if price:
            price_amount = price.find('strong').text.strip()
            price_currency = price.find('dfn').text.strip()  # 货币单位
        else:
            price_amount = 'N/A'
            price_currency = 'N/A'

        # 将信息加入到列表
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

    # 如果没有找到航班信息，返回 None
    if not flight_info:
        return None
    
    return flight_info




# 主程序
def fetch_flight_info(dict_info):
    url = "http://www.9935china-air.com/tools/query.aspx"
    params = {
        't': '0.22513796453290214',  # 动态时间戳或生成的参数
        'sc': 'PEK',#dict_info.get('出发地', 'PEK'),
        'ec': 'SHA',#dict_info.get('目的地', 'SHA'),
        'sd': '2025-01-03', #dict_info.get('出发日期', '2025-01-03'),
        'too': '0'
    }
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:133.0) Gecko/20100101 Firefox/133.0',
        'Accept': 'text/javascript, text/html, application/xml, text/xml, */*',
        'Accept-Encoding': 'gzip, deflate',
        'Accept-Language': 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2',
        'Connection': 'keep-alive',
        'Cookie': 'ASP.NET_SessionId=lnu5ktrcth1m3v141k52yamb; __51uvsct__Jn302wXovbjjqrnI=4; __51vcke__Jn302wXovbjjqrnI=31a5ddf7-361a-5b0a-a6cc-f2fda6cf184e; __51vuft__Jn302wXovbjjqrnI=1735552735700; Hm_lvt_9ea32919b3e2178a03dde3a5bf551e0f=1735552740,1735613051; Hm_lpvt_9ea32919b3e2178a03dde3a5bf551e0f=1735614318; HMACCOUNT=D38C091F0AD77D3C',  # 更新 Cookie
        'Referer': 'http://www.9935china-air.com/flight/showfarefirst_PEK_SHA_2025-01-03_1.htm',
        'X-Requested-With': 'XMLHttpRequest',
    }

    try:
        response = requests.get(url, params=params, headers=headers)
        if response.status_code == 200:
            logger.info(f"Received data: {response.text}...")  # 打印前100个字符
            return parse_flight_info(response.text)
        else:
            logger.error(f"Request failed with status code {response.status_code}")
    except Exception as e:
        logger.error(f"Error fetching data: {e}")

    return None

