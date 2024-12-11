import json
import logging

# 配置日志
logging.basicConfig(
    filename='data.log',  # 日志文件名
    level=logging.INFO,  # 日志级别
    format='%(asctime)s - %(levelname)s - %(message)s',  # 日志格式
)

# 保存日志
def save_log(data, filename="logs/log.json"):
    logging.info(f"准备保存日志到文件: {filename}")
    try:
        with open(filename, "a") as log_file:
            json.dump(data, log_file, ensure_ascii=False, indent=4)
        logging.info(f"日志成功保存到文件: {filename}")
    except Exception as e:
        logging.error(f"保存日志到文件失败，错误信息: {e}")
