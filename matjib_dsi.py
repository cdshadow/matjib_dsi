import streamlit as st
import pandas as pd
import requests
import folium
from streamlit_folium import st_folium
import io

# Kakao API Key 하드코딩
api_key = "3954ac5e45b2aacab5d7158785e8c349"

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
st.title("(참여형) 대세연 맛집 지도")

csv_files = [
    ("lunch.csv",  "일반식당",   "orange"),
    ("event.csv",  "행사 후 식당", "green"),
    ("dinner.csv", "저녁회식",   "blue"),
    ("cafe.csv", "카페", "purple"),
    ("night_work.csv", "초과식당", "red"),
]

@st.cache_data(show_spinner=True)
def geocode_df(csv_file, api_key):
    try:
        df = pd.read_csv(csv_file, encoding="utf-8")
    except UnicodeDecodeError:
        df = pd.read_csv(csv_file, encoding="cp949")
    if "address" not in df.columns or "name" not in df.columns:
        raise ValueError(f"{csv_file} 파일에 'name', 'address' 컬럼이 필요합니다.")
    coords = df['address'].apply(lambda x: get_coordinates(x, api_key))
    x, y = zip(*coords)
    df = df.copy()
    df['x'] = x
    df['y'] = y
    return df

# 1. 모든 데이터 로딩 및 지오코딩
layer_data = []
for file, label, color in csv_files:
    try:
        df = geocode_df(file, api_key)
        layer_data.append((df, label, color))
    except Exception as e:
        st.error(f"{file} 로딩 실패: {e}")

# 2. 지도 생성
map_center = [36.397924, 127.402470]  # 대전시청 중심
m = folium.Map(location=map_center, zoom_start=16)

# 3. 각 레이어에 데이터 추가
for df, label, color in layer_data:
    # 여기서 show 값을 조정!
    show = label in ["일반식당", "행사 후 식당"]  # 기본 활성화 레이어만 True
    feature_group = folium.FeatureGroup(name=label, show=show)
    for idx, row in df.iterrows():
        if pd.notnull(row['x']) and pd.notnull(row['y']):
            # 기본 마커
            folium.Marker(
                location=[row['y'], row['x']],
                popup=row['name'],
                tooltip=row['name'],
                icon=folium.Icon(color=color, icon="info-sign"),
            ).add_to(feature_group)
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
            ).add_to(feature_group)
    feature_group.add_to(m)

# LayerControl 위치
folium.LayerControl(position="topleft").add_to(m)

# Streamlit에 지도 표시
st_folium(m, width=1200, height=800)

# HTML로 다운로드 옵션
html_str = m.get_root().render()
html_data = io.BytesIO(html_str.encode('utf-8'))
st.download_button(
    label="지도 HTML 다운로드",
    data=html_data.getvalue(),
    file_name="facility_map.html",
    mime="text/html"
)
