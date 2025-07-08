import streamlit as st
import pandas as pd
import requests
import folium
from streamlit_folium import st_folium

# 1. Kakao API Key 하드코딩
api_key = "3954ac5e45b2aacab5d7158785e8c349"

# 2. Kakao API 지오코딩 함수
def get_coordinates(address, api_key):
    url = "https://dapi.kakao.com/v2/local/search/address.json"
    headers = {"Authorization": f"KakaoAK {api_key}"}
    params = {"query": address}
    try:
        resp = requests.get(url, headers=headers, params=params, timeout=3)
        if resp.status_code == 200:
            result = resp.json()
            if result['documents']:
                x = float(result['documents'][0]['x'])
                y = float(result['documents'][0]['y'])
                return x, y
        return None, None
    except Exception:
        return None, None

st.set_page_config(layout="wide")
st.title("대세연 맛집")

# 3. place_map_template.csv 파일 자동 불러오기
csv_file_path = "place_map_template.csv"
try:
    df = pd.read_csv(csv_file_path, encoding="utf-8")
except UnicodeDecodeError:
    df = pd.read_csv(csv_file_path, encoding="cp949")

if "address" not in df.columns or "name" not in df.columns:
    st.error("'place_map_template.csv' 파일에 'name', 'address' 컬럼이 필요합니다.")
    st.stop()

# 4. 좌표 얻기 (캐싱)
@st.cache_data(show_spinner=True)
def geocode_df(df, api_key):
    coords = df['address'].apply(lambda x: get_coordinates(x, api_key))
    x, y = zip(*coords)
    df = df.copy()
    df['x'] = x
    df['y'] = y
    return df

df = geocode_df(df, api_key)

# 5. folium 지도 생성
map_center = [36.397924, 127.402470]  # 대전시청 중심
m = folium.Map(location=map_center, zoom_start=16)

for idx, row in df.iterrows():
    if pd.notnull(row['x']) and pd.notnull(row['y']):
        # 기본 마커 (클릭시 팝업)
        folium.Marker(
            location=[row['y'], row['x']],
            popup=row['name'],
            tooltip=row['name'],
            icon=folium.Icon(color="blue", icon="info-sign"),
        ).add_to(m)

        # 항상 보이는 라벨
        folium.map.Marker(
            [row['y'], row['x']],
            icon=folium.DivIcon(
                html=f"""<div style="
                    display: inline-block;
                    font-size: 12px;
                    color: white;
                    font-weight: bold;
                    background: #1877f2;
                    border-radius: 6px;
                    padding: 3px 10px;
                    border: 1px solid #999;
                    opacity: 0.85;
                    text-align: center;
                    white-space: nowrap;
                ">{row['name']}</div>"""
            )
        ).add_to(m)

st.write("")
st_folium(m, width=1000, height=650)
