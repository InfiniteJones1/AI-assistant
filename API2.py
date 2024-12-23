import requests
import pandas as pd
import json
from datetime import datetime
import chardet
import logging

#train-info
# 检测并加载 city 数据
def load_city_data(file_path):
    """加载城市站点数据"""
    with open(file_path, 'rb') as f:
        raw_data = f.read()
        result = chardet.detect(raw_data)
        encoding = result['encoding']

    with open(file_path, 'r', encoding=encoding, errors='ignore') as f:
        return json.load(f)

# 格式化日期
def convert_date_format(depart_date):
    """将MM-DD格式的日期转换为YYYY-MM-DD格式"""
    if len(depart_date) == 5 and depart_date[2] == '-':  # 判断格式是 MM-DD
        current_year = datetime.now().year
        try:
            return datetime.strptime(f"{current_year}-{depart_date}", "%Y-%m-%d").strftime("%Y-%m-%d")
        except ValueError:
            print(f"日期格式转换失败: {depart_date}")
            return None
    return depart_date  # 如果日期已经是 YYYY-MM-DD 格式，直接返回

# 获取站点代码
def get_station_code(city_name, city_data):
    """根据城市名称获取车站代码"""
    return city_data.get(city_name)

# 验证用户输入
def validate_input(dict_info, city_data):
    """校验出发地、目的地和日期信息"""
    start = dict_info.get('出发地')
    end = dict_info.get('目的地')
    depart_date = dict_info.get('出发日期')
    return_date = dict_info.get('返回日期')

    if not start or not end:
        print("出发地或目的地不能为空！")
        return None, None, None, None

    if start not in city_data or end not in city_data:
        print("出发地或目的地无效，请检查输入！")
        return None, None, None, None

    depart_date = convert_date_format(depart_date) if depart_date else None
    return_date = convert_date_format(return_date) if return_date else None

    return start, end, depart_date, return_date

# 获取火车票信息
def fetch_train_info(session, depart_date, start_code, end_code, retries=3):
    """获取火车票信息"""
    url = "https://kyfw.12306.cn/otn/leftTicket/queryO"
    params = {
        "leftTicketDTO.train_date": depart_date,
        "leftTicketDTO.from_station": start_code,
        "leftTicketDTO.to_station": end_code,
        "purpose_codes": "ADULT"
    }
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
        "Accept": "*/*",
        "Referer": "https://kyfw.12306.cn/otn/leftTicket/init?linktypeid=dc",
        "Cookie": "_uab_collina=173479079602795978157776; JSESSIONID=0C751774EA0CF1B02ACD4B7C6A15D12E; guidesStatus=off; highContrastMode=defaltMode; cursorStatus=off; _jc_save_fromStation=%u5357%u4EAC%2CNJH; _jc_save_toStation=%u4E0A%u6D77%2CSHH; _jc_save_fromDate=2024-12-23; _jc_save_toDate=2024-12-23; _jc_save_wfdc_flag=dc; BIGipServerotn=1960378634.50210.0000; BIGipServerpassport=904397066.50215.0000; route=c5c62a339e7744272a54643b3be5bf64"
    }

    for attempt in range(retries):
        response = session.get(url, params=params, headers=headers)
        print(response.text)  # 输出返回的内容，查看是否有有效的火车票数据
        if response.status_code == 200:
            try:
                data = response.json()
                if 'data' in data and 'result' in data['data']:
                    return data['data']['result']
                else:
                    print("没有返回火车票数据。")
                    logging.info("没有返回火车票数据。")
                    return []
            except ValueError as e:
                print(f"解析JSON失败: {e}")
                logging.info(f"解析JSON失败: {e}")
                return []
        else:
            print(f"请求失败，状态码：{response.status_code}。重试中...")
            logging(f"请求失败，状态码：{response.status_code}。重试中...")

    print("重试次数已用尽，未能成功获取火车票信息。")
    logging.info("重试次数已用尽，未能成功获取火车票信息。")
    return []


# 打印火车票信息
def print_train_info(train_info):
    """打印火车票信息"""
    if not train_info:
        print("没有查询到符合条件的火车票。")
        return

    columns = ["车次", "出发时间", "到达时间", "中途时长", "商务座", "一等座", "二等座", "软卧", "硬卧", "软座", "硬座", "无座"]
    data = []
    for info in train_info:
        info_list = info.split("|")
        try:
            data.append([
                info_list[3], info_list[8], info_list[9], info_list[10],
                info_list[32], info_list[31], info_list[30], info_list[23],
                info_list[28], info_list[27], info_list[29], info_list[26]
            ])
        except IndexError:
            print("数据解析时遇到问题，跳过一条记录。")
            logging.info("数据解析时遇到问题，跳过一条记录。")
            continue
    df = pd.DataFrame(data, columns=columns)
    print(df)
    logging.info(df)
    return df

# 查询火车票主逻辑
def train_ticket_query(dict_info, city_data):
    start, end, depart_date, return_date = validate_input(dict_info, city_data)
    if not start or not end:
        return

    start_code = get_station_code(start, city_data)
    end_code = get_station_code(end, city_data)

    # 创建一个 requests.Session 对象
    session = requests.Session()

    if depart_date:
        print(f"查询 {start} 到 {end} 从 {depart_date} 的火车票信息：")
        logging.info(f"查询 {start} 到 {end} 从 {depart_date} 的火车票信息：")
        train_info = fetch_train_info(session, depart_date, start_code, end_code)
        return(print_train_info(train_info))

    if return_date:
        print(f"查询 {end} 到 {start} 从 {return_date} 的火车票信息：")
        logging.info(f"查询 {end} 到 {start} 从 {return_date} 的火车票信息：")
        train_info = fetch_train_info(session, return_date, end_code, start_code)
        return(print_train_info(train_info))
