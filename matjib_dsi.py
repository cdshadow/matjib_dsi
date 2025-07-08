import streamlit as st
import pandas as pd
import requests
import folium
from streamlit_folium import st_folium

# Kakao API Key 하드코딩
api_key = "3954ac5e45b2aacab5d7158785e8c349"

# GitHub raw csv 주소로 파일명과 함께 지정
GITHUB_RAW_BASE = "https://raw.githubusercontent.com/cdshadow/daejeon/main/"

csv_files = [
    (GITHUB_RAW_BASE + "lunch.csv",  "일반식당",   "orange"),
    (GITHUB_RAW_BASE + "event.csv",  "행사 후 식당", "green"),
    (GITHUB_RAW_BASE + "dinner.csv", "저녁회식",   "blue"),
]

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
st.title("대세연 맛집 지도")

@st.cache_data(show_spinner=True)
def geocode_df(csv_url, api_key):
    df = pd.read_csv(csv_url)
    # 컬럼에 공백 있을 때 자동 정리
    df.columns = [c.strip() for c in df.columns]
    if "address" not in df.columns or "name" not in df.columns:
        raise ValueError(f"{csv_url} 파일에 'name', 'address' 컬럼이 필요합니다.")
    # address 값도 strip 처리 (혹시 있을 공백 제거)
    df['address'] = df['address'].astype(str).str.strip()
    coords = df['address'].apply(lambda x: get_coordinates(x, api_key))
    x, y = zip(*coords)
    df = df.copy()
    df['x'] = x
    df['y'] = y
    return df

# 1. 모든 데이터 로딩 및 지오코딩
layer_data = []
for url, label, color in csv_files:
    try:
        df = geocode_df(url, api_key)
        layer_data.append((df, label, color))
    except Exception as e:
        st.error(f"{url} 로딩 실패: {e}")

# 2. 지도 생성
map_center = [36.397924, 127.402470]  # 대전시청 중심
m = folium.Map(location=map_center, zoom_start=16)

# 3. 각 레이어에 데이터 추가
for df, label, color in layer_data:
    feature_group = folium.FeatureGroup(name=label, show=True)
    label_bg = "#1877f2" if color=="blue" else ("orange" if color=="orange" else "green")
    for idx, row in df.iterrows():
        if pd.notnull(row['x']) and pd.notnull(row['y']):
            folium.Marker(
                location=[row['y'], row['x']],
                popup=row['name'],
                tooltip=row['name'],
                icon=folium.Icon(color=color, icon="info-sign"),
            ).add_to(feature_group)
            folium.map.Marker(
                [row['y'], row['x']],
                icon=folium.DivIcon(
                    html=f"""<div style="
                        display: inline-block;
                        font-size: 12px;
                        color: white;
                        font-weight: bold;
                        background: {label_bg};
                        border-radius: 6px;
                        padding: 3px 10px;
                        border: 1px solid #999;
                        opacity: 0.85;
                        text-align: center;
                        white-space: nowrap;
                    ">{row['name']}</div>"""
                )
            ).add_to(feature_group)
    feature_group.add_to(m)

folium.LayerControl().add_to(m)

st_folium(m, width=1200, height=800)
