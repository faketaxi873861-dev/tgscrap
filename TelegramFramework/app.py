import streamlit as st
import asyncio
import pandas as pd
from telethon import TelegramClient
from telethon.tl.types import DocumentAttributeFilename
import re
from datetime import timezone
import pytz

# --- CONFIGURATION ---
# Your credentials from the Colab script
api_id = 27485643
api_hash = '42ebf6916aa332d152e3bd4476e29061'
target_timezone = 'Asia/Kolkata'

st.set_page_config(page_title="Telegram Scraper Framework", layout="wide")

st.title("📡 Telegram Message Scraper")
st.markdown("Enter the channel details below to scrape messages into a permanent CSV format.")

# --- SIDEBAR / UI INPUTS ---
with st.sidebar:
    st.header("Settings")
    target_channel = st.text_input("Channel Link", "https://t.me/+7PGkmLqDYigyNzZl")
    message_limit = st.number_input("Message Limit", min_value=1, max_value=10000, value=500)
    search_keyword = st.text_input("Search Keyword (Optional)")
    st.info("Note: First-time run will require a Telegram OTP code in the server logs.")

async def scrape_telegram(channel_link, limit, keyword):
    scraped_data = []
    # 'web_session' stores your login so you don't have to login every time
    client = TelegramClient('web_session', api_id, api_hash)
    
    await client.connect()
    
    if not await client.is_user_authorized():
        st.error("Client is not authorized. Please check server logs for login.")
        return pd.DataFrame()

    try:
        entity = await client.get_entity(channel_link)
        
        # Determine channel URL
        if entity.username:
            channel_url = f"https://t.me/{entity.username}"
        else:
            channel_url = f"https://t.me/c/{abs(entity.id)}"
            
        st.write(f"✅ Connected to: **{entity.title}**")

        async for message in client.iter_messages(entity, limit=limit, search=keyword if keyword else None):
            file_name = "N/A"
            if message.document:
                for attr in message.document.attributes:
                    if isinstance(attr, DocumentAttributeFilename):
                        file_name = attr.file_name
                        break

            # Timezone conversion
            post_date = message.date.astimezone(pytz.timezone(target_timezone)).strftime('%Y-%m-%d %H:%M:%S')
            
            scraped_data.append({
                'Channel Name': entity.title,
                'Post Date': post_date,
                'Views': message.views or 0,
                'File Name': file_name,
                'Message Text': message.text or "",
                'Message URL': f"{channel_url}/{message.id}"
            })
        
        return pd.DataFrame(scraped_data)
    
    except Exception as e:
        st.error(f"Error: {e}")
        return pd.DataFrame()
    finally:
        await client.disconnect()

# --- MAIN LOGIC ---
if st.button("🚀 Start Scraping"):
    if not target_channel:
        st.warning("Please provide a channel link.")
    else:
        with st.spinner("Fetching data from Telegram..."):
            # Setup Async Loop for Streamlit
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            df = loop.run_until_complete(scrape_telegram(target_channel, message_limit, search_keyword))
            
            if not df.empty:
                st.success(f"Done! Scraped {len(df)} messages.")
                st.dataframe(df, use_container_width=True)
                
                # Download Button
                csv = df.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')
                st.download_button(
                    label="📥 Download Data as CSV",
                    data=csv,
                    file_name="telegram_scraped_data.csv",
                    mime="text/csv"
                )
            else:
                st.info("No data found or check connection settings.")