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
    
    async def get_auth():
        return await client.is_user_authorized()
    
    is_authorized = loop.run_until_complete(get_auth())

    if not is_authorized:
        st.header("🔐 Login")
        phone = st.text_input("Phone Number (+...)", placeholder="+91...")
        
        # FIXED: Added missing colons and proper indentation
        if st.button("1. Send OTP"):
            if phone:
                loop.run_until_complete(client.send_code_request(phone))
                st.info("OTP Sent! Check your Telegram.")
            else:
                st.error("Enter phone number first.")
        
        otp = st.text_input("Enter OTP Code")
        if st.button("2. Verify & Login"):
            try:
                loop.run_until_complete(client.sign_in(phone, otp))
                st.success("Logged In!")
                st.rerun()
            except Exception as e:
                st.error(f"Login Error: {e}")
    else:
        st.success("✅ Telegram Connected")
        if st.button("Logout"):
            loop.run_until_complete(client.log_out())
            st.rerun()

# --- SCRAPER UI ---
st.sidebar.header("⚙️ Scraper Settings")
channel_link = st.sidebar.text_input("Channel Link", "
