import streamlit as st
import requests
import pandas as pd

# ตั้งค่าหน้าเว็บ Streamlit
st.set_page_config(
    page_title="ระบบคำนวณและแสดงอัตราแลกเปลี่ยนเงินตรา",
    page_icon="💱",
    layout="wide"
)

# API Key ที่ได้รับจาก ExchangeRate-API (ดึงจากรูปภาพของคุณ)
DEFAULT_API_KEY = "eff8c79df40254bf1852ac7a"

st.sidebar.header("⚙️ ตั้งค่าระบบ (Settings)")
api_key = st.sidebar.text_input("ระบุ API Key", value=DEFAULT_API_KEY, type="password")

st.title("💱 แอปพลิเคชันแปลงและแสดงอัตราแลกเปลี่ยนเงินตรา")
st.markdown("ดึงข้อมูลอัตราแลกเปลี่ยนล่าสุดแบบ Real-time จาก **ExchangeRate-API**")

# รายชื่อสกุลเงินยอดนิยม
POPULAR_CURRENCIES = [
    "THB", "USD", "EUR", "JPY", "GBP", "AUD", "CAD", "CHF", "CNY", "HKD", "SGD", "KRW", "INR", "MYR", "TWD"
]

# ฟังก์ชันดึงข้อมูลอัตราแลกเปลี่ยน
@st.cache_data(ttl=3600)
def get_exchange_rates(key, base_code):
    url = f"https://v6.exchangerate-api.com/v6/{key}/latest/{base_code}"
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        if response.status_code == 200 and data.get("result") == "success":
            return data
        else:
            return {"error": data.get("error-type", "ไม่สามารถดึงข้อมูลได้")}
    except Exception as e:
        return {"error": str(e)}

# แบ่งส่วนแสดงผลด้วย Tabs
tab1, tab2 = st.tabs(["🔄 แปลงสกุลเงิน (Currency Converter)", "📊 ตารางอัตราแลกเปลี่ยนทั้งหมด (Exchange Rates Table)"])

with tab1:
    st.subheader("คำนวณการแปลงสกุลเงิน")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        amount = st.number_input("จำนวนเงินที่ต้องการแปลง", min_value=0.01, value=100.0, step=10.0)
    
    with col2:
        from_curr = st.selectbox("จากสกุลเงิน (From)", POPULAR_CURRENCIES, index=1) # USD
        
    with col3:
        to_curr = st.selectbox("ไปยังสกุลเงิน (To)", POPULAR_CURRENCIES, index=0) # THB

    if st.button("คำนวณอัตราแลกเปลี่ยน", type="primary"):
        if not api_key:
            st.error("กรุณาระบุ API Key ก่อนทำรายการ")
        else:
            with st.spinner("กำลังดึงข้อมูล..."):
                data = get_exchange_rates(api_key, from_curr)
            
            if "error" in data:
                st.error(f"เกิดข้อผิดพลาด: {data['error']}")
            else:
                rates = data.get("conversion_rates", {})
                if to_curr in rates:
                    rate = rates[to_curr]
                    converted = amount * rate
                    
                    st.success(f"### {amount:,.2f} {from_curr} = {converted:,.2f} {to_curr}")
                    st.info(f"💡 อัตราแลกเปลี่ยนปัจจุบัน: 1 {from_curr} = {rate:,.4f} {to_curr}")
                    st.caption(f"อัปเดตล่าสุดเมื่อ: {data.get('time_last_update_utc', 'N/A')}")
                else:
                    st.warning("ไม่พบข้อมูลสกุลเงินที่เลือก")

with tab2:
    st.subheader("ตารางอัตราแลกเปลี่ยนเทียบกับสกุลเงินหลัก")
    base_currency = st.selectbox("เลือกสกุลเงินหลัก (Base Currency)", POPULAR_CURRENCIES, index=1)
    
    if api_key:
        with st.spinner("กำลังโหลดตารางอัตราแลกเปลี่ยน..."):
            rates_data = get_exchange_rates(api_key, base_currency)
        
        if "error" in rates_data:
            st.error(f"เกิดข้อผิดพลาด: {rates_data['error']}")
        else:
            rates = rates_data.get("conversion_rates", {})
            df = pd.DataFrame(list(rates.items()), columns=["สกุลเงิน (Currency)", "อัตราแลกเปลี่ยน (Rate)"])
            
            search_term = st.text_input("🔍 ค้นหาสกุลเงิน (เช่น THB, EUR, JPY)", "")
            if search_term:
                df = df[df["สกุลเงิน (Currency)"].str.contains(search_term.upper())]
            
            st.dataframe(df, use_container_width=True, height=400)
            st.caption(f"จำนวนสกุลเงินทั้งหมด: {len(df)} สกุลเงิน | อัปเดตล่าสุด: {rates_data.get('time_last_update_utc', 'N/A')}")