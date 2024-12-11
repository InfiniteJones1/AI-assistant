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

#初步获取信息
def parse_trip_description(user_input):
    logging.info("开始解析行程描述...")
    API_key = CONFIG["MOONSHOT_API_KEY"]

    client = OpenAI(
        api_key=API_key,
        base_url="https://api.moonshot.cn/v1",
    )

    try:
        description = f"""拆解信息：{user_input}。
        格式如下：
        出发地：xxx,
        目的地：xxx,
        出发日期：xxx,
        返回日期：xxx,
        活动偏好：xxx,
        预算：xxx。
        """
                
        logging.info(f"发送请求到API，行程描述: {description}")
        
        # 调用 OpenAI API 的 chat.completions 端点
        response = client.chat.completions.create(
            model="moonshot-v1-8k",
            messages=[
                {"role": "user", "content": description}
            ],
            temperature = 0.3,
        )

        # 解析返回内容
        parsed_info = response.choices[0].message.content

        if not parsed_info:
            parsed_info = '无信息'
        
        logging.info(f"成功解析行程描述。解析内容：{parsed_info}")
        return parsed_info

    except Exception as e:
        logging.error(f"API 请求失败，错误信息: {str(e)}")
        return None

# 输出格式化
def format_plan(plan):
    logging.info(f"开始格式化行程计划...")
    formatted_plan = f"行程计划：\n{plan}"
    logging.info("行程计划格式化成功")
    return formatted_plan
