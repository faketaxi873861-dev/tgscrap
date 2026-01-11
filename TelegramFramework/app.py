import streamlit as st
import asyncio
import pandas as pd
from telethon import TelegramClient
from telethon.tl.types import DocumentAttributeFilename
import pytz

# --- CONFIGURATION ---
api_id = 27485643
api_hash = '42ebf6916aa332d152e3bd4476e29061'
target_timezone = 'Asia/Kolkata'

st.set_page_config(page_title="Telegram Scraper", layout="wide")
st.title("📡 Telegram Message Scraper")

# Initialize session state for the Telegram client
if 'client' not in st.session_state:
    st.session_state.client = TelegramClient('web_session', api_id, api_hash)

# --- STEP 1: LOGIN SECTION ---
st.sidebar.header("🔐 Authentication")
phone = st.sidebar.text_input("Phone Number (with country code, e.g., +91...)", key="phone")
otp_code = st.sidebar.text_input("Enter OTP Code", key="otp")

async def setup_client():
    if not st.session_state.client.is_connected():
        await st.session_state.client.connect()
    
    if phone and not await st.session_state.client.is_user_authorized():
        if st.sidebar.button("Send OTP"):
            await st.session_state.client.send_code_request(phone)
            st.sidebar.success("Code sent! Check your Telegram app.")
        
        if otp_code and st.sidebar.button("Verify OTP"):
            try:
                await st.session_state.client.sign_in(phone, otp_code)
                st.sidebar.success("Login Successful!")
                st.rerun()
            except Exception as e:
                st.sidebar.error(f"Login Failed: {e}")

# --- STEP 2: SCRAPER SECTION ---
st.sidebar.header("⚙️ Scraper Settings")
target_channel = st.sidebar.text_input("Channel Link", "https://t.me/+7PGkmLqDYigyNzZl")
message_limit = st.sidebar.number_input("Message Limit", 1, 10000, 500)
search_keyword = st.sidebar.text_input("Search Keyword (Optional)")

async def run_scraper():
    await st.session_state.client.connect()
    if not await st.session_state.client.is_user_authorized():
        st.error("Please login via the sidebar first.")
        return

    scraped_data = []
    try:
        entity = await st.session_state.client.get_entity(target_channel)
        channel_url = f"https://t.me/{entity.username}" if entity.username else "Private Channel"
        
        async for message in st.session_state.client.iter_messages(entity, limit=message_limit, search=search_keyword or None):
            file_name = "N/A"
            if message.document:
                for attr in message.document.attributes:
                    if isinstance(attr, DocumentAttributeFilename):
                        file_name = attr.file_name
                        break
            
            post_date = message.date.astimezone(pytz.timezone(target_timezone)).strftime('%Y-%m-%d %H:%M:%S')
            scraped_data.append({
                'Date': post_date,
                'Views': message.views or 0,
                'File': file_name,
                'Text': message.text or "",
                'Link': f"https://t.me/c/{abs(entity.id)}/{message.id}" if not entity.username else f"{channel_url}/{message.id}"
            })
        return pd.DataFrame(scraped_data)
    except Exception as e:
        st.error(f"Scraping Error: {e}")
        return None

# Execution logic
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
loop.run_until_complete(setup_client())

if st.button("🚀 Start Scraping"):
    with st.spinner("Scraping..."):
        df = loop.run_until_complete(run_scraper())
        if df is not None and not df.empty:
            st.success(f"Scraped {len(df)} messages!")
            st.dataframe(df)
            st.download_button("📥 Download CSV", df.to_csv(index=False).encode('utf-8'), "data.csv", "text/csv")
