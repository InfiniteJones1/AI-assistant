import openai
import requests
import logging
from config import CONFIG

logging.basicConfig(
    filename='API.log',  # 日志文件名
    level=logging.INFO,  # 日志级别
    format='%(asctime)s - %(levelname)s - %(message)s',  # 日志格式
)

# ChatGPT API 调用
def generate_itinerary(parsed_info):
    if not parsed_info:
        logging.error("解析后的信息为空，无法生成行程计划。")
        return "行程解析失败，请检查输入或稍后重试。"

    try:
        prompt = f"""
        根据以下信息生成一个初步的行程计划：
        出发地：{parsed_info['departure']}
        目的地：{parsed_info['destination']}
        出发日期：{parsed_info['start_date']}
        返回日期：{parsed_info['end_date']}
        活动偏好：{parsed_info['preferences']}
        预算：{parsed_info['budget']}
        """
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            api_key=CONFIG["OPENAI_API_KEY"]
        )
        return response.choices[0].message['content']
    
    except KeyError as e:
        logging.error(f"解析内容缺少关键字段：{e}")
        return "行程信息不完整，请重新输入。"


# 完善行程计划的外部服务
def enrich_itinerary(itinerary, parsed_info):
    # 添加天气信息
    weather = get_weather(parsed_info["destination"], parsed_info["start_date"])
    itinerary += f"\n\n天气预报：{weather}"

    # 添加路线信息
    route = get_route(parsed_info["departure"], parsed_info["destination"])
    itinerary += f"\n\n推荐路线：{route}"

    return itinerary

# 获取天气信息
def get_weather(destination, date):
    api_url = f"http://api.weatherapi.com/v1/forecast.json"
    params = {"key": CONFIG["WEATHER_API_KEY"], "q": destination, "dt": date}
    response = requests.get(api_url, params=params)
    return response.json()["forecast"]["forecastday"][0]["day"]["condition"]["text"]

# 获取路线信息
def get_route(departure, destination):
    api_url = f"https://maps.googleapis.com/maps/api/directions/json"
    params = {"origin": departure, "destination": destination, "mode": "driving", "key": CONFIG["MAPS_API_KEY"]}
    response = requests.get(api_url, params=params)
    route = response.json()["routes"][0]["overview_polyline"]["points"]
    return f"从 {departure} 到 {destination} 的最佳路线（驾车）：{route}"
