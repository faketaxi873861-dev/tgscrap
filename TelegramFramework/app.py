import streamlit as st
import asyncio
import pandas as pd
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from telethon.tl.types import DocumentAttributeFilename
import pytz
import qrcode
from io import BytesIO

# --- PROJECT BRANDING ---
NAME = "RITIK KOLI"
# --- CONFIGURATION ---
api_id = 27485643
api_hash = '42ebf6916aa332d152e3bd4476e29061'
target_timezone = 'Asia/Kolkata'

st.set_page_config(page_title=f"Telegram Scraper - {NAME}", layout="wide")

# --- UI HEADER ---
st.title("📡 Telegram Message Scraper")
st.markdown(f"### **Made by {NAME}**")

# --- ASYNC LOOP HANDLING ---
if "loop" not in st.session_state:
    st.session_state.loop = asyncio.new_event_loop()
    asyncio.set_event_loop(st.session_state.loop)

loop = st.session_state.loop

# --- TELETHON CLIENT SETUP ---
if "client" not in st.session_state:
    st.session_state.client = TelegramClient(StringSession(), api_id, api_hash)
    loop.run_until_complete(st.session_state.client.connect())

client = st.session_state.client

# --- SIDEBAR AUTHENTICATION ---
with st.sidebar:
    st.header("👤 Developer")
    st.markdown(f"**{NAME}**")
    st.divider()
    
    async def check_auth():
        return await client.is_user_authorized()
    
    is_authorized = loop.run_until_complete(check_auth())

    if not is_authorized:
        login_method = st.radio("Choose Login Method", ["Phone + OTP", "QR Code"])

        if login_method == "Phone + OTP":
            phone = st.text_input("Phone Number (+...)", placeholder="+91...")
            if st.button("1. Send OTP"):
                if phone:
                    loop.run_until_complete(client.send_code_request(phone))
                    st.info("OTP Sent!")
            
            otp = st.text_input("Enter OTP Code")
            if st.button("2. Verify & Login"):
                try:
                    loop.run_until_complete(client.sign_in(phone, otp))
                    st.success("Logged In!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Login Error: {e}")

        else:  # QR Code Method
            if st.button("Generate QR Code"):
                qr_container = st.empty()
                async def qr_login():
                    qr_login = await client.qr_login()
                    while not qr_login.is_logged_in():
                        # Generate QR Image
                        img = qrcode.make(qr_login.url)
                        buf = BytesIO()
                        img.save(buf)
                        qr_container.image(buf.getvalue(), caption="Scan with Telegram > Devices > Link Device")
                        
                        try:
                            await qr_login.wait(timeout=10)
                        except asyncio.TimeoutError:
                            continue
                    return True

                if loop.run_until_complete(qr_login()):
                    st.success("Logged in via QR!")
                    st.rerun()
    else:
        st.success("✅ Telegram Connected")
        if st.button("Logout"):
            loop.run_until_complete(client.log_out())
            st.rerun()

# --- SCRAPER UI ---
st.sidebar.header("⚙️ Scraper Settings")
channel_link = st.sidebar.text_input("Channel Link", value="https://t.me/+7PGkmLqDYigyNzZl")
limit = st.sidebar.number_input("Message Limit", min_value=1, max_value=10000, value=500)
keyword = st.sidebar.text_input("Search (Optional)")

async def scrape_logic():
    entity = await client.get_entity(channel_link)
    channel_name = entity.title
    channel_url = f"https://t.me/{entity.username}" if entity.username else f"https://t.me/c/{abs(entity.id)}"
        
    data = []
    async for msg in client.iter_messages(entity, limit=limit, search=keyword or None):
        fname = "N/A"
        if msg.document:
            for attr in msg.document.attributes:
                if isinstance(attr, DocumentAttributeFilename):
                    fname = attr.file_name
        
        dt = msg.date.astimezone(pytz.timezone(target_timezone)).strftime('%Y-%m-%d %H:%M:%S')
        data.append({
            'Channel Name': channel_name,
            'Channel URL': channel_url,
            'Date': dt, 
            'Views': msg.views or 0, 
            'File Name': fname, 
            'Message': msg.text or "",
            'Message URL': f"{channel_url}/{msg.id}"
        })
    return pd.DataFrame(data)

# --- MAIN ACTION ---
if st.button("🚀 Start Scraping"):
    if not is_authorized:
        st.error("Please login via the sidebar first.")
    else:
        with st.spinner("Scraping messages..."):
            try:
                df = loop.run_until_complete(scrape_logic())
                if not df.empty:
                    st.success(f"Scraped {len(df)} messages")
                    st.dataframe(df, use_container_width=True)
                    csv = df.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')
                    st.download_button("📥 Download Full CSV", csv, "telegram_data.csv", "text/csv")
                else:
                    st.warning("No messages found.")
            except Exception as e:
                st.error(f"Error: {e}")

st.divider()
st.markdown(f"<center><b>Framework Made By {NAME}</b></center>", unsafe_allow_html=True)
