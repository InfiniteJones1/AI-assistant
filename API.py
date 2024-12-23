from openai import OpenAI
import requests
import logging
import pandas as pd
import os
import json
from config import CONFIG
import datetime
from bs4 import BeautifulSoup
import re
from datetime import datetime
from API2 import get_station_code, validate_input, fetch_train_info, load_city_data, print_train_info, train_ticket_query

logging.basicConfig(
    filename='API.log',  # 日志文件名
    level=logging.INFO,  # 日志级别
    format='%(asctime)s - %(levelname)s - %(message)s',  # 日志格式
)

username = CONFIG['12306username']
password = CONFIG["12306password"]

#API 调用
def generate_itinerary(dict_info, other_info):
    if not other_info:
        logging.error("解析后的信息为空，无法生成行程计划。")
        return "行程解析失败，请检查输入或稍后重试。"
    
    API_key = CONFIG["MOONSHOT_API_KEY"]
    client = OpenAI(
        api_key=API_key,
        base_url="https://api.moonshot.cn/v1",
    )
    
    try:
        prompt = f"""信息：{dict_info}。补充信息：{other_info}。
        根据以上信息和补充信息生成一个详细的行程计划。
        """
        response = client.chat.completions.create(
            model="moonshot-v1-8k",
            messages=[{"role": "user", "content": prompt}],
            temperature = 0.3
        )
        logging.info(f"成功生成计划。生成内容：{response.choices[0].message.content}")
        return response.choices[0].message.content
    
    except KeyError as e:
        logging.error(f"解析内容缺少关键字段：{e}")
        return "行程信息不完整，请重新输入。"


# 完善行程计划的外部服务
def enrich_itinerary(dict_info):
    other_info={}
    # 添加天气信息
    weather = get_weather(dict_info["目的地"])
    other_info["目的地天气"]=weather

    # 查询机票
    train = train_ticket_query(dict_info, load_city_data("city12306.json"))
    other_info["火车票信息"]=train

    logging.info(f"补充信息：{other_info}")
    return other_info


#天气API-高德
#查找地点对应adcode
def get_adcode(location_name, excel_file):
    """
    从 Excel 表格中查找指定地点名称的 adcode。

    Args:
        location_name (str): 地点名称（如南京）。
        excel_file (str): Excel 文件相对路径。

    Returns:
        str: 对应的 adcode，如果未找到则返回 None。
    """
    try:
        # 获取脚本文件的所在目录
        base_dir = os.path.dirname(os.path.abspath(__file__))
        # 拼接相对路径
        excel_path = os.path.join(base_dir, excel_file)

        # 加载 Excel 文件
        df = pd.read_excel(excel_path)

        # 检查列是否存在
        if df.shape[1] < 2:
            raise ValueError("Excel 文件必须至少包含两列，分别为中文名和 adcode。")

        # 假设第一列为中文名，第二列为 adcode
        # 使用 str.contains 进行模糊匹配
        matched_rows = df[df.iloc[:, 0].str.contains(location_name, na=False)]

        if not matched_rows.empty:
            location_adcode = matched_rows.iloc[0, 1]  # 获取第一条匹配记录的 adcode
            logging.info(f"查找地点 {location_name} 的 adcode 成功: {location_adcode}")
            return location_adcode
        else:
            logging.info(f"未找到地点: {location_name}")
            return None

    except Exception as e:
        logging.error(f"发生错误: {e}")
        return None


# 获取天气信息
def get_weather(destination):
    """
    获取指定目的地的天气预报信息（仅包含 forecast 内容）。

    Args:
        destination (str): 城市名称或编码。
        key (str): 高德地图 API 密钥。

    Returns:
        list: 天气预报内容，仅包含 forecasts 的信息。
    """
    logging.info("获取天气信息...")
    adcode=get_adcode(destination, "adcode.xlsx")
    # 高德地图天气API URL
    api_url = f"https://restapi.amap.com/v3/weather/weatherInfo?city={adcode}&key={CONFIG['WEATHER_API_KEY']}"
    
    # 请求参数
    params = {
        "key": CONFIG["WEATHER_API_KEY"],
        "city": destination,
        "extensions": "all"
    }

    try:
        # 发起GET请求
        response = requests.get(api_url, params=params)
        response.raise_for_status()  # 检查HTTP请求是否成功
        weather_data = response.json()

        # 检查返回值状态码
        if weather_data.get("status") == "1":
            logging.info("获取天气信息成功。")
            return weather_data.get("forecasts", [])
        else:
            logging.error(f"获取天气信息失败，错误信息: {weather_data.get('info')}")
            return None
    except requests.RequestException as e:
        logging.error(f"请求天气信息时发生错误: {e}")
        return None

