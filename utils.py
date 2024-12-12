import requests
import re
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


# 将解析后的行程信息转换为字典
def parse_to_dict(parsed_info):
    logging.info("开始将解析后的行程信息转换为字典...")
    try:
        # 使用正则表达式提取信息
        fields = {
            "出发地": r"出发地：(.+)",
            "目的地": r"目的地：(.+)",
            "出发日期": r"出发日期：(.+)",
            "返回日期": r"返回日期：(.+)",
            "活动偏好": r"活动偏好：(.+)",
            "预算": r"预算：(.+)"
        }

        # 初始化字典
        parsed_dict = {}
        for key, pattern in fields.items():
            match = re.search(pattern, parsed_info)
            if match:
                parsed_dict[key] = match.group(1).strip()
            else:
                parsed_dict[key] = None  # 如果没有匹配到则设置为 None

        logging.info(f"转换成功，结果为：{parsed_dict}")
        return parsed_dict

    except Exception as e:
        logging.error(f"转换行程信息为字典失败，错误信息: {str(e)}")
        return None


