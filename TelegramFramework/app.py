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

# --- CORE ASYNC FIX ---
# This ensures we always use the SAME event loop across reruns
if "loop" not in st.session_state:
    st.session_state.loop = asyncio.new_event_loop()
    asyncio.set_event_loop(st.session_state.loop)

loop = st.session_state.loop

# Initialize or get the persistent client
if "client" not in st.session_state:
    # Use a session file name that persists
    st.session_state.client = TelegramClient('web_session', api_id, api_hash)
    loop.run_until_complete(st.session_state.client.connect())

client = st.session_state.client

# --- AUTHENTICATION SIDEBAR ---
st.sidebar.header("🔐 Authentication")

async def get_auth_status():
    return await client.is_user_authorized()

# Check if we are already logged in
authorized = loop.run_until_complete(get_auth_status())

if not authorized:
    phone = st.sidebar.text_input("Phone Number (+...)", placeholder="+91...")
    
    # We use a button to trigger the code request inside the loop
    if st.sidebar.button("1. Send OTP"):
        if phone:
            loop.run_until_complete(client.send_code_request(phone))
            st.sidebar.info("OTP Sent! Check your Telegram app.")
        else:
            st.sidebar.error("Please enter a phone number.")

    otp_code = st.sidebar.text_input("Enter OTP Code")
    if st.sidebar.button("2. Verify & Login"):
        try:
            loop.run_until_complete(client.sign_in(phone, otp_code))
            st.sidebar.success("Successfully Authorized!")
            st.rerun() # Refresh to show the scraper
        except Exception as e:
            st.sidebar.error(f"Login failed: {e}")
else:
    st.sidebar.success("✅ Connected to Telegram")
    if st.sidebar.button("Logout"):
        loop.run_until_complete(client.log_out())
        st.rerun()

# --- SCRAPER SETTINGS ---
st.sidebar.header("⚙️ Scraper Settings")
channel_link = st.sidebar.text_input("Channel Link", "https://t.me/+7PGkmLqDYigyNzZl")
msg_limit = st.sidebar.number_input("Message Limit", 1, 10000, 500)
keyword = st.sidebar.text_input("Search Keyword (Optional)")

# --- SCRAPING FUNCTION ---
async def fetch_messages(link, limit, search_term):
    entity = await client.get_entity(link)
    results = []
    
    async for msg in client.iter_messages(entity, limit=limit, search=search_term or None):
        # Filename logic
        fname = "N/A"
        if msg.document:
            for attr in msg.document.attributes:
                if isinstance(attr, DocumentAttributeFilename):
                    fname = attr.file_name
        
        # Timezone conversion
        local_time = msg.date.astimezone(pytz.timezone(target_timezone)).strftime('%Y-%m-%d %H:%M:%S')
        
        results.append({
            'Date': local_time,
            'Views': msg.views or 0,
            'File': fname,
            'Text': msg.text or "",
            'Link': f"https://t.me/c/{abs(entity.id)}/{msg.id}"
        })
    return pd.DataFrame(results)

# --- EXECUTION ---
if st.button("🚀 Start Scraping"):
    if not authorized:
        st.error("Please authorize via the sidebar first.")
    else:
        with st.spinner("Fetching data..."):
            try:
                df = loop.run_until_complete(fetch_messages(channel_link, msg_limit, keyword))
                if not df.empty:
                    st.success(f"Scraped {len(df)} messages!")
                    st.dataframe(df, use_container_width=True)
                    # Download link
                    csv_data = df.to_csv(index=False).encode('utf-8')
                    st.download_button("📥 Download Results", csv_data, "telegram_data.csv", "text/csv")
                else:
                    st.warning("No messages found.")
            except Exception as e:
                st.error(f"Scrape Error: {e}")
