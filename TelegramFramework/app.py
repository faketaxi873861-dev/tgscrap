import streamlit as st
import asyncio
import pandas as pd
from telethon import TelegramClient
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

st.set_page_config(
    page_title=f"Advanced Telegram Scraper - {NAME}", 
    layout="wide",
    page_icon="📡"
)

# --- CUSTOM STYLING (CSS) ---
st.markdown("""
    <style>
        .block-container { padding-top: 2rem; }
        .stButton>button { width: 100%; border-radius: 8px; font-weight: bold; }
        div[data-testid="stMetricValue"] { font-size: 24px; color: #0088cc; }
        .footer-text { text-align: center; font-weight: bold; color: #555; margin-top: 30px; }
    </style>
""", unsafe_allow_html=True)

# --- UI HEADER ---
st.title("📡 Advanced Telegram Message Scraper")
st.markdown(f"📊 *Enhanced Hybrid Engine (Colab + Web Framework Integration)* | **Made by {NAME}**")
st.divider()

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
    st.header("👤 System Developer")
    st.markdown(f"🔬 **{NAME}**")
    st.divider()
    
    async def check_auth():
        return await client.is_user_authorized()
    
    is_authorized = loop.run_until_complete(check_auth())

    if not is_authorized:
        login_method = st.radio("Choose Verification Method", ["Phone + OTP", "Secure QR Code"])

        if login_method == "Phone + OTP":
            phone = st.text_input("Phone Number", placeholder="+91...")
            if st.button("1. Request Authorization OTP"):
                if phone:
                    try:
                        loop.run_until_complete(client.send_code_request(phone))
                        st.info("OTP Sent! Check your active Telegram apps.")
                    except Exception as e:
                        st.error(f"Error sending code: {e}")
            
            otp = st.text_input("Enter Received OTP")
            if st.button("2. Finalize Validation"):
                try:
                    loop.run_until_complete(client.sign_in(phone, otp))
                    st.success("Authorization Complete!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Login Exception: {e}")

        else:  # QR Code Method
            if st.button("Generate Secure QR Entry"):
                qr_container = st.empty()
                
                async def qr_login_process():
                    qr_op = await client.qr_login()
                    while True:
                        img = qrcode.make(qr_op.url)
                        buf = BytesIO()
                        img.save(buf)
                        qr_container.image(buf.getvalue(), caption="Scan: Settings > Devices > Link Desktop Device")
                        
                        try:
                            user = await qr_op.wait(timeout=10)
                            if user:
                                return True
                        except asyncio.TimeoutError:
                            continue
                        except Exception as e:
                            st.error(f"QR Interruption: {e}")
                            return False

                try:
                    if loop.run_until_complete(qr_login_process()):
                        st.success("Authorized via QR successfully!")
                        st.rerun()
                except Exception as e:
                    st.error(f"Authentication Failure: {e}")
    else:
        st.success("✅ Engine Status: Connected")
        if st.button("Terminate Session (Logout)"):
            loop.run_until_complete(client.log_out())
            st.rerun()

# --- SCRAPER UI ---
st.sidebar.header("⚙️ Target Profile Configuration")
# Unified target input box supporting link types from both setups
channel_target = st.sidebar.text_input(
    "Channel Identifier", 
    value="https://t.me/+7PGkmLqDYigyNzZl",
    help="Accepts Public links, Invite links, Channel Username, or Raw Numeric IDs"
)

limit = st.sidebar.number_input("Maximum Record Limit", min_value=1, max_value=20000, value=500, step=50)
keyword = st.sidebar.text_input("Context Filter Keyword (Optional)")

async def scrape_logic():
    target = channel_target.strip()
    
    # Process numeric inputs derived from the Colab approach
    if target.startswith('-') or target.isdigit():
        entity = await client.get_entity(int(target))
    else:
        entity = await client.get_entity(target)
        
    channel_name = entity.title
    sub_count = getattr(entity, 'participants_count', 'Hidden/N/A')
    
    # Accurate URL routing for public vs private contexts
    if getattr(entity, 'username', None):
        channel_url = f"https://t.me/{entity.username}"
    else:
        channel_url = f"https://t.me/c/{abs(entity.id)}"
        
    data = []
    
    # Visual Progress feedback element for web application flow
    progress_bar = st.progress(0.0)
    status_text = st.empty()
    
    # Fetch data structure dynamically matching core metrics
    current_count = 0
    async for msg in client.iter_messages(entity, limit=limit, search=keyword or None):
        fname = "N/A"
        if msg.document:
            for attr in msg.document.attributes:
                if isinstance(attr, DocumentAttributeFilename):
                    fname = attr.file_name
                    break
        
        dt = "N/A"
        if msg.date:
            dt = msg.date.astimezone(pytz.timezone(target_timezone)).strftime('%Y-%m-%d %H:%M:%S')
        
        data.append({
            'Channel Name': channel_name,
            'Channel ID': entity.id,
            'Subscribers': sub_count,
            'Date': dt, 
            'Views': msg.views or 0, 
            'File Name': fname, 
            'Message Content': msg.text or "",
            'Message URL': f"{channel_url}/{msg.id}"
        })
        
        current_count += 1
        if current_count % 50 == 0 or current_count == limit:
            pct = min(current_count / limit, 1.0)
            progress_bar.progress(pct)
            status_text.text(f"📥 Pulled {current_count} of {limit} records...")

    progress_bar.empty()
    status_text.empty()
    return pd.DataFrame(data), channel_name, sub_count

# --- MAIN ACTION ROW ---
if st.button("🚀 Execute Cloud Extraction"):
    if not is_authorized:
        st.error("Access Denied: Please authorize your session via the control sidebar panel first.")
    elif not channel_target:
        st.warning("Input Error: Please pass a valid Channel target configuration.")
    else:
        with st.spinner("Extracting parameters and querying Telegram ledger..."):
            try:
                df, title, total_subs = loop.run_until_complete(scrape_logic())
                
                if not df.empty:
                    st.success(f"Transaction Complete: Extracted {len(df)} records from database context.")
                    
                    # Highlight Dashboard Metrics
                    m1, m2, m3 = st.columns(3)
                    m1.metric("Channel Target Title", title)
                    m2.metric("Subscriber Capacity", total_subs)
                    m3.metric("Records Scraped", len(df))
                    
                    st.divider()
                    
                    # Modern functional DataFrame View
                    st.dataframe(df, use_container_width=True)
                    
                    # Generate dynamic Download Artifact
                    csv = df.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')
                    st.download_button(
                        label="📥 Download Extracted Datatable (CSV)",
                        data=csv,
                        file_name=f"scraped_report_{title.replace(' ', '_')}.csv",
                        mime="text/csv"
                    )
                else:
                    st.warning("Null Dataset returned. Refine parameters or filtering query.")
            except Exception as e:
                st.error(f"Execution Error: {e}")

# --- FOOTER ---
st.markdown('<div class="footer-text">Framework Infrastructure Engineered By ' + NAME + '</div>', unsafe_allow_html=True)
