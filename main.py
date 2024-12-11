import config
import logging
from utils import parse_trip_description, format_plan
from API import generate_itinerary, enrich_itinerary
from data import save_log

# 配置日志
logging.basicConfig(
    filename='itinerary_assistant.log',  # 日志文件名
    level=logging.INFO,  # 日志级别
    format='%(asctime)s - %(levelname)s - %(message)s',  # 日志格式
)

def main():
    logging.info("程序启动，欢迎使用智能行程助手！")
    print("欢迎使用智能行程助手！")
    user_input = input("请描述您的行程需求：\n")

    # Step 1: 使用 Chatgpt 解析输入
    logging.info(f"用户输入的行程需求: {user_input}")
    parsed_info = parse_trip_description(user_input)
    logging.info(f"解析后的行程信息: {parsed_info}")

    # Step 2: 调用 ChatGPT 生成大致行程计划
    logging.info("开始生成行程计划...")
    itinerary = generate_itinerary(parsed_info)
    logging.info(f"生成的大致行程计划: {itinerary}")

    # Step 3: 调用其他服务完善行程
    logging.info("开始完善行程计划...")
    detailed_itinerary = enrich_itinerary(itinerary, parsed_info)
    logging.info(f"完善后的行程计划: {detailed_itinerary}")

    # Step 4: 输出结果
    formatted_itinerary = format_plan(detailed_itinerary)
    print("\n生成的行程计划：")
    print(formatted_itinerary)

    # 保存日志
    save_log({"input": user_input, "parsed": parsed_info, "plan": detailed_itinerary})
    logging.info("行程计划已保存日志。")

if __name__ == "__main__":
    main()
