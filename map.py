import time
import folium
import webbrowser
import requests
import logging
import json
import time
from openai import OpenAI
from config import CONFIG

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("route_planner.log"), logging.StreamHandler()]
)

# 配置 API 密钥
MOONSHOT_API_KEY = CONFIG["MOONSHOT_API_KEY"]
TIANDITU_API_KEY = CONFIG["MAP_API_KEY"]

# 初始化 Kimi API 客户端
client = OpenAI(
    api_key=MOONSHOT_API_KEY,
    base_url="https://api.moonshot.cn/v1",
)

def get_daily_routes(info):
    """
    使用 Kimi API 生成每日路线。
    """
    try:
        time.sleep(1)
        prompt = json.dumps({
            "行程": info,
            "需求": "严格按照以下格式制定每日路线,只提供day和地点，地点直接写详细地址。待定地点，如酒店、车站等不写进路线。",
            "格式": {
                "day_1": ["地点1", "地点2", "..."],
                "day_2": ["地点1", "地点2", "..."]
            }
        }, ensure_ascii=False)

        logging.info("调用 Kimi API 生成每日路线...")
        response = client.chat.completions.create(
            model="moonshot-v1-8k",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )
        content = response.choices[0].message.content
        logging.info(f"每日路线生成成功！原始返回内容：{content}")

        # 尝试将 API 返回的字符串转为 JSON 格式
        try:
            parsed_content = json.loads(content)
            return parsed_content
        except json.JSONDecodeError:
            logging.warning("API 返回的内容不是标准 JSON 格式，尝试修正格式...")

        # 修正可能存在的问题
            repaired_content = content.split("{", 1)[-1]  # 截取第一个 `{` 后的内容
            repaired_content = "{" + repaired_content  # 补回丢失的 `{`
            repaired_content = repaired_content.rsplit("}", 1)[0] + "}"  # 截取最后一个 `}` 前的内容

        # 替换常见问题符号
            repaired_content = repaired_content.replace("'", "\"").strip()  # 单引号 -> 双引号
            repaired_content = repaired_content.replace("“", "\"").replace("”", "\"")  # 修正中文引号
            repaired_content = repaired_content.replace("\n", "")  # 删除多余换行符

        # 再次尝试解析为 JSON
            try:
                parsed_content = json.loads(repaired_content)
                logging.info(f"修正后的内容解析成功！内容：{parsed_content}")
                return parsed_content
            except json.JSONDecodeError as e:
                logging.error(f"修正后的内容仍无法解析为 JSON: {repaired_content}")
                logging.error(f"错误信息: {e}")
                return {}
    except Exception as e:
        logging.error(f"Kimi API 调用失败: {e}")
        return {}



def get_coordinates(routes):
    """
    获取所有地点的经纬度。
    """
    coordinates = {}
    for day, locations in routes.items():
        daily_coords = []
        for loc in locations:
            try:
                logging.info(f"获取 {loc} 的经纬度...")
                url = f"http://api.tianditu.gov.cn/geocoder?ds={{\"keyWord\":\"{loc}\"}}&tk={TIANDITU_API_KEY}"
                response = requests.get(url)
                if response.status_code == 200:
                    data = response.json()
                    if data.get("status") == "0":
                        lon, lat = data["location"]["lon"], data["location"]["lat"]
                        daily_coords.append((loc, (lon, lat)))
                        logging.info(f"{loc} 经纬度为: 经度={lon}, 纬度={lat}")
                    else:
                        logging.warning(f"无法获取 {loc} 的经纬度: {data}")
                else:
                    logging.error(f"天地图 API 请求失败: {response.status_code}")
            except Exception as e:
                logging.error(f"获取 {loc} 经纬度时出错: {e}")
        coordinates[day] = daily_coords
    return coordinates


def get_user_location():
    """
    获取用户实时位置。
    """
    try:
        logging.info("尝试获取用户的实时位置...")
        # 调用IP地理定位接口（示例：ipinfo.io 或其他服务）
        response = requests.get("https://ipinfo.io/json")
        if response.status_code == 200:
            data = response.json()
            loc = data.get("loc", "0,0").split(",")
            latitude, longitude = float(loc[0]), float(loc[1])
            logging.info(f"用户实时位置: 纬度={latitude}, 经度={longitude}")
            return latitude, longitude
        else:
            logging.error("获取用户位置失败")
    except Exception as e:
        logging.error(f"获取用户位置出错: {e}")
    return 0, 0


def public_trans(coordinates):
    """
    通过坐标获取公共交通路线并输出，输出格式为linePoint。
    """
    routes = {}
    for day, locations in coordinates.items():
        day_routes = []  # 存储每天的公交路线信息
        for i in range(len(locations) - 1):
            start_loc, start_coords = locations[i]   # 起始地点和坐标
            end_loc, end_coords = locations[i + 1]  # 终点和坐标
            
            # 经纬度拼接（天地图API要求经度在前，纬度在后）
            start_position = f"{str(start_coords[0])},{str(start_coords[1])}"  
            end_position = f"{str(end_coords[0])},{str(end_coords[1])}"
            logging.info(f"startPosition: {start_position}, endPosition: {end_position}")

            try:
                # 构建请求的 JSON 字符串
                postStr = json.dumps({
                    "startposition": start_position,
                    "endposition": end_position,
                    "linetype": "1"
                })

                # 调用天地图公交路线 API
                logging.info(f"获取从 '{start_loc}' 到 '{end_loc}' 的公交路线...")
                url = (
                    f"http://api.tianditu.gov.cn/transit?"
                    f"type=busline&postStr={postStr}&tk={TIANDITU_API_KEY}"
                )
                response = requests.get(url)

                # 检查请求是否成功
                if response.status_code == 200:
                    try:
                        data = response.json()
                        if data.get("resultCode") == 0:  # 检查返回的状态码
                            # 提取公交路线步骤
                            for line in data.get("results", [])[0].get("lines", []):
                                line_name = line.get("lineName", "未知线路")
                                segments = line.get("segments", [])
                                
                                for segment in segments:
                                    start_station = segment.get("stationStart", {}).get("name", "未知起点")
                                    end_station = segment.get("stationEnd", {}).get("name", "未知终点")
                                    
                                    # segmentLine 包含了时间、距离和坐标点
                                    for segment_line in segment.get("segmentLine", []):
                                        segment_time = segment_line.get("segmentTime", "未知时长")
                                        segment_distance = segment_line.get("segmentDistance", "未知距离")
                                        line_points = segment_line.get("linePoint", "").split(';')  # 提取线路的坐标点
                                        
                                        # 保存每天的路线信息
                                        day_routes.append({
                                            "lineName": line_name,
                                            "startStation": start_station,
                                            "endStation": end_station,
                                            "segmentTime": segment_time,
                                            "segmentDistance": segment_distance,
                                            "linePoints": line_points  # 保存linePoints（坐标点）
                                        })

                                        # 打印信息
                                        print(f"公交路线: {line_name}")
                                        print(f"起点: {start_station}, 终点: {end_station}")
                                        print(f"时长: {segment_time}, 距离: {segment_distance}米")
                                        print(f"坐标点: {line_points}")
                        else:
                            logging.warning(f"天地图 API 返回错误: {data.get('msg', '未知错误')}")
                    except json.JSONDecodeError:
                        logging.error(f"解析 JSON 出错: 返回内容: {response.text}")
                else:
                    logging.error(f"API 请求失败，状态码: {response.status_code}")

            except Exception as e:
                logging.error(f"获取公交路线时发生错误: {e}")

        # 将每天的公交路线保存到字典中
        routes[day] = day_routes

    return routes



def plot_route_map(transit_routes, coordinates):
    """
    绘制路线图，并在地图上标记用户位置、地点和路线。
    transit_routes: 从 public_trans 输出的公交路线数据，包括linePoints。
    coordinates: 各地点的经纬度坐标。
    """
    print(transit_routes)
    print(coordinates)
    user_lat, user_lon = get_user_location()

    for day, routes in transit_routes.items():
        logging.info(f"绘制第 {day} 天的路线图...")
        map_center = coordinates[day][0][1]
        route_map = folium.Map(location=[map_center[1], map_center[0]], zoom_start=12)

        # 标记用户位置
        if user_lat and user_lon:
            folium.Marker(
                location=[user_lat, user_lon],
                popup="用户当前位置",
                icon=folium.Icon(color="red", icon="user")
            ).add_to(route_map)

        # 添加地点标记
        for loc, coord in coordinates[day]:
            folium.Marker(
                location=[coord[1], coord[0]],
                popup=loc,
                icon=folium.Icon(color="blue")
            ).add_to(route_map)

        # 绘制路线
        for route in routes:
            line_name = route["lineName"]
            line_points = route["linePoints"]
            points = []

            # 解析linePoints中的坐标点
            for point in line_points:
                coords = point.split(',')
                if len(coords) == 2:
                    lon, lat = float(coords[0]), float(coords[1])
                    points.append([lat, lon])

            # 如果linePoints有效，则绘制路线
            if len(points) > 1:
                folium.PolyLine(
                    points,
                    color="blue",
                    weight=2.5
                ).add_to(route_map)
            else:
                logging.warning(f"警告: 无有效的linePoints数据，跳过 {line_name} 的绘制。")

        # 保存地图
        filename = f"{day}_route_map.html"
        route_map.save(filename)
        webbrowser.open(filename)
        logging.info(f"地图已保存为 {filename}")
