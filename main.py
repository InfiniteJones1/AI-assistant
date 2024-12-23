import config
import logging
import utils
from utils import parse_trip_description
from API import generate_itinerary, enrich_itinerary
from data import save_log
from map import get_daily_routes, get_coordinates, plot_route_map, public_trans
from API2 import get_station_code, validate_input, fetch_train_info, print_train_info, train_ticket_query
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
    parsed_info = utils.parse_trip_description(user_input)
    logging.info(f"解析后的行程信息: {parsed_info}")
    dict_info = utils.parse_to_dict(parsed_info)
    print(dict_info)

    # Step 2: 调用其他API生成补充信息
    logging.info("开始生成行程计划...")
    other_info = enrich_itinerary(dict_info)
    logging.info(f"生成的补充信息: {other_info}")
    print(f"\n生成的补充信息：{other_info}")

    # Step 3: 调用kimi完善行程
    logging.info("开始完善行程计划...")
    detailed_itinerary = generate_itinerary(dict_info, other_info)
    logging.info(f"生成完善信息: {detailed_itinerary}")
    print(f"\n完善后的行程计划：{detailed_itinerary}")

    #绘制路线图/地图
    #route = get_daily_routes(detailed_itinerary)
    #print(f"路线：{route}")
    #logging.info("开始生成路线并绘制地图...")
    #coor_route=get_coordinates(route)
    #print(f"坐标：{coor_route}")
    #route_data = public_trans(coor_route)
    #plot_route_map(route_data, coor_route)

    


if __name__ == "__main__":
    main()
    input("按回车键Enter退出...")
