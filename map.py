import folium
import webbrowser
import requests
import logging
import json
from openai import OpenAI
from config import CONFIG
import os


# 绘制地图-天地图
def create_map(route_data):
    api_key = CONFIG["MAPS_API_KEY"]
    # 使用天地图的矢量底图和注记
    tile_url = f"http://t0.tianditu.gov.cn/vec_c/wmts?tk={api_key}"
    annotation_url = f"http://t0.tianditu.gov.cn/cva_c/wmts?tk={api_key}"
    
    # 为每天生成一个地图
    for i, day in enumerate(route_data):
        # 创建地图，设置默认中心和缩放级别
        center_lat, center_lng = float(day['places'][0]['lat']), float(day['places'][0]['lng'])
        trip_map = folium.Map(location=[center_lat, center_lng], zoom_start=13, control_scale=True)

        # 添加天地图的底图和注记
        folium.TileLayer(
            tiles=tile_url, 
            attr="天地图", 
            name="天地图矢量底图", 
            overlay=True, 
            control=True
        ).add_to(trip_map)
        
        folium.TileLayer(
            tiles=annotation_url, 
            attr="天地图", 
            name="天地图注记", 
            overlay=True, 
            control=True
        ).add_to(trip_map)

        # 为当天的地点添加标记
        for place in day["places"]:
            folium.Marker(
                location=[float(place["lat"]), float(place["lng"])],
                popup=f"{place['name']} ({place['time']})",
                tooltip=place['name']
            ).add_to(trip_map)

        # 绘制当天的路线
        points = [(float(place["lat"]), float(place["lng"])) for place in day["places"]]
        if len(points) > 1:
            folium.PolyLine(points, color="blue", weight=2.5, opacity=1).add_to(trip_map)

        # 添加图层控制
        folium.LayerControl().add_to(trip_map)
        logging.info(f"绘制第{i+1}天地图成功。")

        # 保存地图为 HTML 文件
        map_filename = f"day_{i+1}_route_map.html"
        trip_map.save(map_filename)
        logging.info(f"第{i+1}天地图已保存为 {map_filename}")

        # 确保文件路径是绝对路径，方便浏览器打开
        map_file_path = os.path.abspath(map_filename)
        webbrowser.open(f'file://{map_file_path}')
    
    logging.info("所有地图已生成并展示。")
    print(f"正在浏览器中生成每天路线图...")
    return route_data  # 返回生成的路线数据



    


# 提供路线
def generate_route(detailed_itinerary):
    API_key = CONFIG["MOONSHOT_API_KEY"]
    client = OpenAI(
        api_key=API_key,
        base_url="https://api.moonshot.cn/v1",
    )
    
    try:
        # 使用三引号来表示多行字符串，并确保格式化正确
        prompt = f"""
行程：{detailed_itinerary}。
根据以上行程生成路线，格式如下：
[
    {{
        "day": "xxx",
        "date": "xxxx-xx-xx",
        "places": [
            {{
                "name": "xxx", "lat": "xxx", "lng": "xxx", "time": "xx:xx-xx:xx"
            }},
            {{
                "name": "xxx", "lat": "xxx", "lng": "xxx", "time": "xx:xx-xx:xx"
            }}
        ]
    }},
    ...
]
"""
        # 调用 API 生成路线
        response = client.chat.completions.create(
            model="moonshot-v1-8k",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )
        
        # 获取返回的内容，去掉 Markdown 标记
        content = response.choices[0].message.content
        
        # 提取 JSON 部分
        try:
            # 找到 JSON 数据部分并去除标记
            json_data = content.split("```json")[1].split("```")[0].strip()
            
            # 解析 JSON
            route_data = json.loads(json_data)
            
            # 输出解析后的数据
            logging.info(f"成功解析的路由数据：{route_data}")
        except (IndexError, json.JSONDecodeError) as e:
            logging.error(f"解析 JSON 时出错：{e}")
            return "路线生成失败。"
        
        # 返回生成的路线数据
        logging.info(f"成功生成路线。生成内容：{route_data}")
        return route_data
    
    except KeyError as e:
        logging.error(f"缺少关键字段：{e}")
        return "路线生成失败。"

