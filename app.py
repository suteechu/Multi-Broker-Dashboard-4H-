import streamlit as st
from tvDatafeed import TvDatafeed, Interval
import plotly.graph_objects as go
import pandas as pd

st.set_page_config(page_title="Dashboard: 6 Brokers Comparison", layout="wide")

st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Prompt:wght@300;400;500;700&family=Space+Mono:wght@400;700&display=swap');
        
        .block-container {
            padding-top: 1rem !important;
            padding-bottom: 0rem !important;
            padding-left: 1rem !important;
            padding-right: 1rem !important;
        }
        header {visibility: hidden;} /* ซ่อนแถบเมนูบนขวาของ Streamlit */
    </style>
""", unsafe_allow_html=True)

import streamlit.components.v1 as components
from streamlit_autorefresh import st_autorefresh

# 1. ระบบ Auto-Refresh (ทุกๆ 15 นาที)
st_autorefresh(interval=900000, limit=None, key="data_refresh")

col1, col2, col3 = st.columns([3, 2, 2])

with col1:
    st.markdown("<h4 style='font-family: \"Space Mono\", sans-serif; font-size: 22px; font-weight: bold; margin-bottom:0px; margin-top:0px; letter-spacing: -0.5px;'>📊 Multi-Broker Dashboard</h4>", unsafe_allow_html=True)

with col2:
    # 2. ปรับ Timeframe (4H | 1D | 1W)
    st.markdown("<style>div.row-widget.stRadio > div{flex-direction:row;} </style>", unsafe_allow_html=True)
    selected_tf_str = st.radio("Timeframe", ["4H", "1D", "1W"], horizontal=True, label_visibility="collapsed")

with col3:
    # 3. อัปเดต Timer ให้คำนวณตาม Timeframe
    timer_html = f"""
    <div style="font-family: 'Space Mono', sans-serif; font-size: 18px; font-weight: bold; display: flex; align-items: center; justify-content: flex-end; margin-top: 5px;">
        <span style="color: #718096; margin-right: 8px;">Next {selected_tf_str} Candle in:</span>
        <span id="candle-timer" style="color: #000000; letter-spacing: 1px; background: rgba(0,255,163,0.3); padding: 4px 10px; border-radius: 6px;">--:--:--</span>
    </div>
    <script>
        var tf = "{selected_tf_str}";
        function updateTimer() {{
            var now = new Date();
            var nextCandle = new Date(now);
            
            if (tf === "4H") {{
                var currentHour = now.getUTCHours();
                var nextHour = currentHour + (4 - (currentHour % 4));
                nextCandle.setUTCHours(nextHour, 0, 0, 0);
            }} else if (tf === "1D") {{
                nextCandle.setUTCDate(now.getUTCDate() + 1);
                nextCandle.setUTCHours(0, 0, 0, 0);
            }} else if (tf === "1W") {{
                var daysUntilMonday = (1 - now.getUTCDay() + 7) % 7;
                if (daysUntilMonday === 0) daysUntilMonday = 7;
                nextCandle.setUTCDate(now.getUTCDate() + daysUntilMonday);
                nextCandle.setUTCHours(0, 0, 0, 0);
            }}
            
            var diff = nextCandle - now;
            var d = Math.floor(diff / (1000 * 60 * 60 * 24));
            var h = Math.floor((diff % (1000 * 60 * 60 * 24)) / 3600000);
            var m = Math.floor((diff % 3600000) / 60000);
            var s = Math.floor((diff % 60000) / 1000);
            
            var timerStr = "";
            if (tf === "1W" && d > 0) timerStr += d + "d ";
            timerStr += (h < 10 ? "0"+h : h) + ":" + (m < 10 ? "0"+m : m) + ":" + (s < 10 ? "0"+s : s);
            
            document.getElementById('candle-timer').innerText = timerStr;
        }}
        setInterval(updateTimer, 1000);
        updateTimer();
    </script>
    """
    components.html(timer_html, height=45)

# st.markdown("<div style='font-family: \"Prompt\", sans-serif; font-size: 13px; color: #718096; margin-bottom: 5px; margin-top: 0px;'>เปรียบเทียบ 3 แท่งล่าสุดจาก 6 โบรกเกอร์ | รีเฟรชอัตโนมัติทุกๆ 15 นาที</div>", unsafe_allow_html=True)

# Initialize tvdatafeed
@st.cache_resource
def get_tv():
    return TvDatafeed()

tv = get_tv()

# นิยามโบรกเกอร์ (Exchanges) สำหรับแต่ละประเภท (เอาแค่ 3 โบรกเกอร์)
crypto_brokers = ["CRYPTO", "BINANCE", "VANTAGE"]
forex_brokers = ["OANDA", "FOREXCOM", "VANTAGE"]
dxy_brokers = ["TVC", "CAPITALCOM", "CURRENCYCOM"]

# รายชื่อสินทรัพย์ (รวม 12 สินทรัพย์ เพื่อให้ได้ 6 แถว แถวละ 2 สินทรัพย์)
assets = [
    {"name": "₿ BTCUSD", "symbol": "BTCUSD", "type": "crypto", "decimals": 2},
    {"name": "🥇 Gold (XAUUSD)", "symbol": "XAUUSD", "type": "forex", "decimals": 2},
    
    {"name": "💵 U.S. Dollar Index (DXY)", "symbol": "DXY", "type": "dxy", "decimals": 3},
    {"name": "💱 EURUSD", "symbol": "EURUSD", "type": "forex", "decimals": 5},
    
    {"name": "💱 GBPUSD", "symbol": "GBPUSD", "type": "forex", "decimals": 5},
    {"name": "💱 USDJPY", "symbol": "USDJPY", "type": "forex", "decimals": 3},
    
    {"name": "💱 AUDUSD", "symbol": "AUDUSD", "type": "forex", "decimals": 5},
    {"name": "💱 USDCAD", "symbol": "USDCAD", "type": "forex", "decimals": 5},
    
    {"name": "💱 USDCHF", "symbol": "USDCHF", "type": "forex", "decimals": 5},
    {"name": "💱 NZDUSD", "symbol": "NZDUSD", "type": "forex", "decimals": 5},
    
    {"name": "💱 EURJPY", "symbol": "EURJPY", "type": "forex", "decimals": 3},
    {"name": "💱 GBPJPY", "symbol": "GBPJPY", "type": "forex", "decimals": 3}
]

# แปลง String เป็น Interval สำหรับแท่งเทียนหลัก
tf_map = {
    "4H": Interval.in_4_hour,
    "1D": Interval.in_daily,
    "1W": Interval.in_weekly
}
selected_interval = tf_map[selected_tf_str]

# กำหนด Interval อ้างอิงและ Label ของ High/Low ตาม Timeframe ที่เลือก
ref_map = {
    "4H": {"interval": Interval.in_daily, "label": "PD"},
    "1D": {"interval": Interval.in_weekly, "label": "PW"},
    "1W": {"interval": Interval.in_monthly, "label": "PM"}
}
ref_info = ref_map[selected_tf_str]
ref_interval = ref_info["interval"]
ref_label = ref_info["label"]

def fetch_data(symbol, exchange):
    try:
        df = tv.get_hist(symbol=symbol, exchange=exchange, interval=selected_interval, n_bars=3)
        return df
    except:
        return None

def fetch_ref_hl(symbol, exchange):
    try:
        df = tv.get_hist(symbol=symbol, exchange=exchange, interval=ref_interval, n_bars=2)
        if df is not None and len(df) >= 2:
            prev_bar = df.iloc[-2]
            return prev_bar['high'], prev_bar['low']
        return None, None
    except:
        return None, None

def plot_candlestick(df, ref_h=None, ref_l=None, y_range=None):
    # ถ้าเป็น 1D หรือ 1W ให้โชว์วันที่แทนเวลา
    x_labels = df.index.strftime('%Y-%m-%d' if selected_tf_str in ["1D", "1W"] else '%H:%M')
    
    fig = go.Figure(data=[go.Candlestick(x=x_labels,
                open=df['open'],
                high=df['high'],
                low=df['low'],
                close=df['close'],
                name='Candles',
                increasing_line_color='#4A5568', decreasing_line_color='#4A5568',
                increasing_fillcolor='#FFFFFF', decreasing_fillcolor='#718096'
                )])
    
    if ref_h is not None and ref_l is not None:
        fig.add_hline(y=ref_h, line_dash="dot", line_width=1, line_color="#10B981", 
                      annotation_text=f"{ref_label}H", annotation_position="top right", 
                      annotation_font=dict(size=9, color="#10B981"))
        fig.add_hline(y=ref_l, line_dash="dot", line_width=1, line_color="#EF4444", 
                      annotation_text=f"{ref_label}L", annotation_position="bottom right", 
                      annotation_font=dict(size=9, color="#EF4444"))

    fig.update_layout(
        template="plotly_dark",
        height=600,
        margin=dict(l=0, r=0, t=10, b=0),
        xaxis_type='category',
        font=dict(size=10, family="Space Mono, Helvetica, sans-serif", color="#A0AEC0"),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        showlegend=False,
        xaxis=dict(showgrid=False, zeroline=False, title="", tickfont=dict(family="Space Mono, sans-serif", size=10)),
        yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.05)', zeroline=False, title="", side='right', range=y_range, tickfont=dict(family="Space Mono, sans-serif", size=10))
    )
    fig.update_layout(xaxis_rangeslider_visible=False)
    return fig

def get_asset_data_and_range(asset, brokers):
    data_list = []
    g_min, g_max = float('inf'), float('-inf')
    for broker in brokers[:3]:
        df = fetch_data(asset['symbol'], broker)
        ref_h, ref_l = fetch_ref_hl(asset['symbol'], broker)
        data_list.append({'broker': broker, 'df': df, 'ref_h': ref_h, 'ref_l': ref_l})
        if df is not None and not df.empty:
            l_min, l_max = df['low'].min(), df['high'].max()
            if ref_l is not None: l_min = min(l_min, ref_l)
            if ref_h is not None: l_max = max(l_max, ref_h)
            g_min, g_max = min(g_min, l_min), max(g_max, l_max)
            
    y_range = None
    if g_min != float('inf') and g_max != float('-inf'):
        padding = (g_max - g_min) * 0.1
        if padding == 0: padding = g_max * 0.001
        y_range = [g_min - padding, g_max + padding]
        
    return data_list, y_range

# ฟังก์ชันสร้าง Badge เตือน Sweep
def get_sweep_badge(df, ref_h, ref_l):
    if df is None or df.empty or ref_h is None or ref_l is None:
        return ""
    last_candle = df.iloc[-1]
    if last_candle['high'] > ref_h:
        return f"<span style='color:#10B981; font-size:10px; margin-left:5px; background:rgba(16,185,129,0.1); padding:2px 4px; border-radius:3px;'>🚨 {ref_label}H Sweep</span>"
    if last_candle['low'] < ref_l:
        return f"<span style='color:#EF4444; font-size:10px; margin-left:5px; background:rgba(239,68,68,0.1); padding:2px 4px; border-radius:3px;'>🚨 {ref_label}L Sweep</span>"
    return ""

# เรนเดอร์ UI แบบจับคู่ (2 สินทรัพย์ต่อ 1 แถว)
for i in range(0, len(assets), 2):
    asset1 = assets[i]
    asset2 = assets[i+1] if i+1 < len(assets) else None
    
    # วาดชื่อหัวข้อในแถวแยกต่างหาก เพื่อไม่ให้ดันกราฟลงมา
    header_cols = st.columns(2)
    with header_cols[0]:
        st.markdown(f"<div style='font-family: \"Space Mono\", sans-serif; font-size: 16px; font-weight: bold; margin-bottom: -10px; color: #E2E8F0; letter-spacing: -0.5px;'>{asset1['name']}</div>", unsafe_allow_html=True)
    if asset2:
        with header_cols[1]:
            st.markdown(f"<div style='font-family: \"Space Mono\", sans-serif; font-size: 16px; font-weight: bold; margin-bottom: -10px; color: #E2E8F0; letter-spacing: -0.5px;'>{asset2['name']}</div>", unsafe_allow_html=True)
            
    # 6 คอลัมน์ต่อแถว (3 คอลัมน์แรกให้ asset1, 3 คอลัมน์หลังให้ asset2)
    cols = st.columns(6)
            
    # เลือกลิสต์โบรกเกอร์ และดึงข้อมูลพร้อมคำนวณ y_range
    brokers1 = crypto_brokers if asset1['type'] == "crypto" else (dxy_brokers if asset1['type'] == "dxy" else forex_brokers)
    data1, y_range1 = get_asset_data_and_range(asset1, brokers1)
    
    brokers2 = []
    data2, y_range2 = [], None
    if asset2:
        brokers2 = crypto_brokers if asset2['type'] == "crypto" else (dxy_brokers if asset2['type'] == "dxy" else forex_brokers)
        data2, y_range2 = get_asset_data_and_range(asset2, brokers2)
        
    # วาดกราฟ Asset 1 (3 ช่องแรก)
    for j in range(3):
        if j < len(data1):
            item = data1[j]
            broker = item['broker']
            badge = get_sweep_badge(item['df'], item['ref_h'], item['ref_l'])
            with cols[j]:
                st.markdown(f"<div style='text-align:center; font-family: \"Space Mono\", sans-serif; font-size:11px; font-weight:bold; color:#A0AEC0; letter-spacing: -0.5px; margin-top: 15px;'>{asset1['symbol']}/{broker} {badge}</div>", unsafe_allow_html=True)
                if item['df'] is not None and not item['df'].empty:
                    st.plotly_chart(plot_candlestick(item['df'], item['ref_h'], item['ref_l'], y_range1), use_container_width=True)
                else:
                    st.warning("No Data")
                    
    # วาดกราฟ Asset 2 (3 ช่องหลัง)
    if asset2:
        for j in range(3):
            if j < len(data2):
                item = data2[j]
                broker = item['broker']
                badge = get_sweep_badge(item['df'], item['ref_h'], item['ref_l'])
                with cols[j+3]:
                    st.markdown(f"<div style='text-align:center; font-family: \"Space Mono\", sans-serif; font-size:11px; font-weight:bold; color:#A0AEC0; letter-spacing: -0.5px; margin-top: 15px;'>{asset2['symbol']}/{broker} {badge}</div>", unsafe_allow_html=True)
                    if item['df'] is not None and not item['df'].empty:
                        st.plotly_chart(plot_candlestick(item['df'], item['ref_h'], item['ref_l'], y_range2), use_container_width=True)
                    else:
                        st.warning("No Data")

    st.markdown("---")
