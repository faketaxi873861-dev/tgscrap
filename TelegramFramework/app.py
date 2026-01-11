import streamlit as st
import asyncio
import pandas as pd
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.tl.types import DocumentAttributeFilename
import pytz

# --- PROJECT BRANDING ---
NAME = "RITIK KOLI"

# --- CONFIGURATION ---
api_id = 27485643
api_hash = '42ebf6916aa332d152e3bd4476e29061'
target_timezone = 'Asia/Kolkata'

st.set_page_config(page_title=f"Telegram Scraper - {NAME}", layout="wide")

# --- CUSTOM BRANDING IN UI ---
st.title("📡 Telegram Message Scraper")
st.markdown(f"**Created and Maintained by: {NAME}**")

# --- ASYNC LOOP HANDLING ---
if "loop" not in st.session_state:
    st.session_state.loop = asyncio.new_event_loop()
    asyncio.set_event_loop(st.session_state.loop)

loop = st.session_state.loop

# --- TELETHON CLIENT SETUP ---
# Using StringSession() prevents the "sqlite3.OperationalError: database is locked"
if "client" not in st.session_state:
    st.session_state.client = TelegramClient(StringSession(), api_id, api_hash)
    loop.run_until_complete(st.session_state.client.connect())

client = st.session_state.client

# --- SIDEBAR AUTHENTICATION ---
with st.sidebar:
    st.header("👤 Author Information")
    st.success(f"Framework made by: **{NAME}**")
    st.divider()
    
    st.header("🔐 Authentication")
    
    async def get_auth():
        return await client.is_user_authorized()
    
    is_authorized = loop.run_until_complete(get_auth())

    if not is_authorized:
        phone = st.text_input("Phone Number (+...)", placeholder="+91...")
        if st.button("1. Send OTP"):
            if phone:
                loop.run_until_complete(client.send_code_request(phone))
                st.info("OTP Sent! Check your Telegram.")
        
        otp = st.text_input("Enter OTP Code")
        if st.button("2. Verify & Login"):
            try:
                loop.run_until_complete(client.sign_in(phone, otp))
                st.success("Logged In!")
                st.rerun()
            except Exception as e:
                st.error(f"Login Error: {e}")
    else:
        st.success("✅ Connected to Telegram")
        if st.button("Logout"):
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
            'Date': dt, 
            'Views': msg.views or 0, 
            'File': fname, 
            'Text': msg.text or "",
            'Link': f"https://t.me/c/{abs(entity.id)}/{msg.id}" if not entity.username else f"https://t.me/{entity.username}/{msg.id}"
        })
    return pd.DataFrame(data)

# --- MAIN ACTION ---
if st.button("🚀 Start Scraping"):
    if not is_authorized:
        st.error("Please log in via the sidebar first.")
    else:
        with st.spinner("Scraping messages..."):
            try:
                df = loop.run_until_complete(scrape_logic())
                st.success(f"Scraped {len(df)} messages!")
                st.dataframe(df, use_container_width=True)
                csv = df.to_csv(index=False).encode('utf-8')
                st.download_button("📥 Download CSV", csv, "scraped_data.csv", "text/csv")
            except Exception as e:
                st.error(f"Error during scrape: {e}")

# --- FOOTER ---
st.divider()
st.caption(f"© 2024 Telegram Scraper Framework | Made with ❤️ by {NAME}")
