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

st.set_page_config(page_title="Telegram Scraper Framework", layout="wide")
st.title("📡 Telegram Message Scraper")

# --- ASYNC LOOP HANDLING ---
# This is the "Magic Fix" for the RuntimeError you saw
if "loop" not in st.session_state:
    st.session_state.loop = asyncio.new_event_loop()
    asyncio.set_event_loop(st.session_state.loop)

loop = st.session_state.loop

# Initialize the Telegram Client once
if "client" not in st.session_state:
    st.session_state.client = TelegramClient('web_session', api_id, api_hash)
    loop.run_until_complete(st.session_state.client.connect())

client = st.session_state.client

# --- AUTHENTICATION SIDEBAR ---
st.sidebar.header("🔐 Authentication")

async def check_auth():
    return await client.is_user_authorized()

is_authorized = loop.run_until_complete(check_auth())

if not is_authorized:
    phone = st.sidebar.text_input("Phone Number (+...)", placeholder="+911234567890")
    if st.sidebar.button("1. Send OTP"):
        if phone:
            loop.run_until_complete(client.send_code_request(phone))
            st.sidebar.info("OTP Sent! Check your Telegram.")
        else:
            st.sidebar.error("Enter phone number first.")

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
    if st.sidebar.button("Logout / Clear Session"):
        loop.run_until_complete(client.log_out())
        st.rerun()

# --- SCRAPER SETTINGS ---
st.sidebar.header("⚙️ Scraper Settings")
channel_link = st.sidebar.text_input("Channel Link", "https://t.me/+7PGkmLqDYigyNzZl")
limit = st.sidebar.number_input("Message Limit", 1, 10000, 500)
keyword = st.sidebar.text_input("Search Keyword (Optional)")

# --- SCRAPING LOGIC ---
async def start_scraping(link, msg_limit, search_query):
    entity = await client.get_entity(link)
    messages = []
    
    async for msg in client.iter_messages(entity, limit=msg_limit, search=search_query or None):
        # Extract filename
        file_name = "N/A"
        if msg.document:
            for attr in msg.document.attributes:
                if isinstance(attr, DocumentAttributeFilename):
                    file_name = attr.file_name
        
        # Timezone Conversion
        dt = msg.date.astimezone(pytz.timezone(target_timezone)).strftime('%Y-%m-%d %H:%M:%S')
        
        messages.append({
            'Date': dt,
            'Views': msg.views or 0,
            'File Name': file_name,
            'Message': msg.text or "",
            'URL': f"https://t.me/c/{abs(entity.id)}/{msg.id}"
        })
    return pd.DataFrame(messages)

if st.button("🚀 Start Scraping"):
    if not is_authorized:
        st.error("Please log in using the sidebar first!")
    else:
        with st.spinner("Fetching messages..."):
            try:
                df = loop.run_until_complete(start_scraping(channel_link, limit, keyword))
                if not df.empty:
                    st.success(f"Scraped {len(df)} messages!")
                    st.dataframe(df, use_container_width=True)
                    csv = df.to_csv(index=False).encode('utf-8')
                    st.download_button("📥 Download CSV", csv, "telegram_data.csv", "text/csv")
                else:
                    st.warning("No messages found.")
            except Exception as e:
                st.error(f"Error: {e}")
