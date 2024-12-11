import requests
import logging
from config import CONFIG
from openai import OpenAI

# 配置日志
logging.basicConfig(
    filename='utils.log',  # 日志文件名
    level=logging.INFO,  # 日志级别
    format='%(asctime)s - %(levelname)s - %(message)s',  # 日志格式
)

# 输入解析
def parse_trip_description(description):
    logging.info("开始解析行程描述...")
    api_key = CONFIG["OPENAI_API_KEY"]
    
    # 设置 OpenAI API 密钥
    OpenAI.api_key = api_key

    try:
        logging.info(f"发送请求到API，行程描述: {description}")
        
        # 发送请求到 chat/completions 端点
        response = OpenAI.chat.completions.create(
            model="gpt-4o-mini",  # 使用 GPT-4 模型，也可以使用 gpt-3.5-turbo
            messages=[
                {"role": "user", "content": description}
            ]
        )

        # 获取响应中的结果        
        parsed_info = response['choices'][0]['message']['content']
        
        if not parsed_info:
            parsed_info = '无信息'
        
        logging.info("成功解析行程描述")
        return parsed_info

    except:
        logging.error(f"API 请求失败，错误信息。")
        return None

# 输出格式化
def format_plan(plan):
    logging.info(f"开始格式化行程计划...")
    formatted_plan = f"行程计划：\n{plan}"
    logging.info("行程计划格式化成功")
    return formatted_plan
