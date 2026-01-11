import streamlit as st
import asyncio
import pandas as pd
from telethon import TelegramClient
from telethon.sessions import StringSession # Fix for SQLite error
from telethon.tl.types import DocumentAttributeFilename
import pytz

# --- CONFIGURATION ---
api_id = 27485643
api_hash = '42ebf6916aa332d152e3bd4476e29061'
target_timezone = 'Asia/Kolkata'

st.set_page_config(page_title="Telegram Scraper", layout="wide")
st.title("📡 Telegram Message Scraper")

# --- ASYNC LOOP HANDLING ---
if "loop" not in st.session_state:
    st.session_state.loop = asyncio.new_event_loop()
    asyncio.set_event_loop(st.session_state.loop)

loop = st.session_state.loop

# --- TELETHON CLIENT SETUP ---
# We use an empty StringSession() to avoid sqlite3 file locking errors
if "client" not in st.session_state:
    st.session_state.client = TelegramClient(StringSession(), api_id, api_hash)
    loop.run_until_complete(st.session_state.client.connect())

client = st.session_state.client

# --- AUTHENTICATION ---
st.sidebar.header("🔐 Authentication")

async def check_auth():
    return await client.is_user_authorized()

is_authorized = loop.run_until_complete(check_auth())

if not is_authorized:
    phone = st.sidebar.text_input("Phone Number (+...)", placeholder="+91...")
    if st.sidebar.button("1. Send OTP"):
        if phone:
            loop.run_until_complete(client.send_code_request(phone))
            st.sidebar.info("OTP Sent! Check your Telegram.")
    
    otp = st.sidebar.text_input("Enter OTP Code")
    if st.sidebar.button("2. Verify & Login"):
        try:
            loop.run_until_complete(client.sign_in(phone, otp))
            st.sidebar.success("Logged In!")
            st.rerun()
        except Exception as e:
            st.sidebar.error(f"Login Error: {e}")
else:
    st.sidebar.success("✅ Connected to Telegram")
    if st.sidebar.button("Logout"):
        loop.run_until_complete(client.log_out())
        st.rerun()

# --- SCRAPER UI ---
st.sidebar.header("⚙️ Scraper Settings")
channel_link = st.sidebar.text_input("Channel Link", "https://t.me/+7PGkmLqDYigyNzZl")
limit = st.sidebar.number_input("Message Limit", 1, 10000, 500)
keyword = st.sidebar.text_input("Search (Optional)")

async def scrape_logic():
    entity = await client.get_entity(channel_link)
    data = []
    async for msg in client.iter_messages(entity, limit=limit, search=keyword or None):
        fname = "N/A"
        if msg.document:
            for attr in msg.document.attributes:
                if isinstance(attr, DocumentAttributeFilename):
                    fname = attr.file_name
        
        dt = msg.date.astimezone(pytz.timezone(target_timezone)).strftime('%Y-%m-%d %H:%M:%S')
        data.append({
            'Date': dt, 'Views': msg.views or 0, 'File': fname, 'Text': msg.text or ""
        })
    return pd.DataFrame(data)

if st.button("🚀 Start Scraping"):
    if not is_authorized:
        st.error("Login first!")
    else:
        with st.spinner("Scraping..."):
            df = loop.run_until_complete(scrape_logic())
            st.dataframe(df)
            st.download_button("Download CSV", df.to_csv(index=False).encode('utf-8'), "data.csv")
