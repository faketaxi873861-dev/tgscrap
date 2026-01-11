import streamlit as st
import asyncio
import pandas as pd
from telethon import TelegramClient
from telethon.tl.types import DocumentAttributeFilename
import pytz
import os

# --- CONFIGURATION ---
api_id = 27485643
api_hash = '42ebf6916aa332d152e3bd4476e29061'
target_timezone = 'Asia/Kolkata'

st.set_page_config(page_title="Telegram Scraper", layout="wide")
st.title("📡 Telegram Message Scraper")

# --- ASYNC HELPER ---
# This ensures we use the same loop and don't trigger the RuntimeError
def get_or_create_event_loop():
    try:
        return asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop

loop = get_or_create_event_loop()

# Initialize Telethon Client in Streamlit Session State
if 'client' not in st.session_state:
    # Use a persistent file for the session
    st.session_state.client = TelegramClient('web_session', api_id, api_hash)
    loop.run_until_complete(st.session_state.client.connect())

client = st.session_state.client

# --- AUTHENTICATION UI ---
st.sidebar.header("🔐 Authentication")
if not loop.run_until_complete(client.is_user_authorized()):
    phone = st.sidebar.text_input("Phone Number (+91...)", key="phone_input")
    sent_code = st.sidebar.button("1. Send OTP")
    
    if sent_code and phone:
        loop.run_until_complete(client.send_code_request(phone))
        st.sidebar.info("Code sent to your Telegram!")

    otp_code = st.sidebar.text_input("Enter OTP", key="otp_input")
    login_btn = st.sidebar.button("2. Verify & Login")

    if login_btn and otp_code:
        try:
            loop.run_until_complete(client.sign_in(phone, otp_code))
            st.sidebar.success("Logged in!")
            st.rerun()
        except Exception as e:
            st.sidebar.error(f"Error: {e}")
else:
    st.sidebar.success("✅ Connected to Telegram")
    if st.sidebar.button("Logout"):
        loop.run_until_complete(client.log_out())
        st.rerun()

# --- SCRAPER SETTINGS ---
st.sidebar.header("⚙️ Scraper Settings")
target_channel = st.sidebar.text_input("Channel Link", "https://t.me/+7PGkmLqDYigyNzZl")
message_limit = st.sidebar.number_input("Message Limit", 1, 10000, 500)
search_keyword = st.sidebar.text_input("Search (Optional)")

async def scrape_logic():
    entity = await client.get_entity(target_channel)
    data = []
    async for msg in client.iter_messages(entity, limit=message_limit, search=search_keyword or None):
        # Extract filename if exists
        fname = "N/A"
        if msg.document:
            for attr in msg.document.attributes:
                if isinstance(attr, DocumentAttributeFilename):
                    fname = attr.file_name
        
        # Time conversion
        dt = msg.date.astimezone(pytz.timezone(target_timezone)).strftime('%Y-%m-%d %H:%M:%S')
        
        data.append({
            'Date': dt,
            'Message': msg.text or "",
            'File': fname,
            'Views': msg.views or 0,
            'Link': f"https://t.me/c/{abs(entity.id)}/{msg.id}" if not entity.username else f"https://t.me/{entity.username}/{msg.id}"
        })
    return pd.DataFrame(data)

if st.button("🚀 Start Scraping"):
    if not loop.run_until_complete(client.is_user_authorized()):
        st.error("Please login first using the sidebar!")
    else:
        with st.spinner("Scraping data..."):
            try:
                df = loop.run_until_complete(scrape_logic())
                st.success(f"Found {len(df)} messages")
                st.dataframe(df)
                st.download_button("📥 Download CSV", df.to_csv(index=False).encode('utf-8'), "scraped_data.csv")
            except Exception as e:
                st.error(f"Scrape failed: {e}")
