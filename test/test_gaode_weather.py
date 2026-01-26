import os
import sys
import json
import http.client
from urllib.parse import quote

from config import LLM_CONFIG,GAODE_WEATHER_KEY
conn = http.client.HTTPSConnection("restapi.amap.com")
payload = ''
headers = {}
city = '北京'
safe_city = quote(city)
# --- 第一步：获取地理编码 ---
conn.request("GET", f"/v3/geocode/geo?&key={GAODE_WEATHER_KEY}&address={safe_city}", payload, headers)
res1 = conn.getresponse() # 必须先获取响应
data1 = res1.read().decode("utf-8")
data1 = json.loads(data1)
city_code = data1["geocodes"][0]["adcode"]
print("地理编码结果:", data1)
# 此时你需要解析 data1 里的 JSON 拿到 adcode，而不是直接往下跑

# --- 第二步：获取天气 (使用刚才获取的 adcode 或者硬编码的 110101) ---
# 注意：http.client 有时需要重新建立连接，或者确保上一个流已读完
conn.request("GET", f"/v3/weather/weatherInfo?city={city_code}&key={GAODE_WEATHER_KEY}")
res2 = conn.getresponse()
data2 = res2.read().decode("utf-8")
print("天气结果:", data2)