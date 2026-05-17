import streamlit as st
import asyncio
import pandas as pd
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.tl.types import DocumentAttributeFilename, MessageMediaDocument
import pytz
import qrcode
from io import BytesIO
import re

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
st.markdown(f"📊 *Enhanced Hybrid Engine (Smart Asset Matcher & Content Classifier)* | **Made by {NAME}**")
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

# --- MASTER ASSET LIST ---
ASSET_LIST = [
    "Akbar Birbal", "Ramayan Sabke Jeevan Ka Aadhar", "Al Akhawat (Maayka) (Zee Alwan)", 
    "Al Malik W Al Malika (Ek Tha Raja Ek Thi Rani)", "Anta Mahboobi (Rabb Se Hai Dua)", 
    "Jodha Akbar (Arabic)", "Jodha Akbar(Indonesia)", "Jodha And Akbar", "Les Voeux De Vidya", 
    "Pavithra Rishta", "Qubool", "Radha Mohan (Pyar Ka Kehla Naam Radha Mohan)", "Siddhivinayak", 
    "Zindagi Ki Mehek (Zee Alwan)", "Bhagya Lakshmi (Arabic)", "Kumkum Bhagya (Arabic)", 
    "Kumkum Bhagya (USA)", "Kundali Bhagya (Arabic)", "My Journey To You (Kaise Mujhe Tum Mil Gaye)", 
    "Aap Ke Aa Jane Se", "Aga Aga Sunbai, Kay Mhanta Sasubai?", "Agar Tum Na Hote", 
    "Aisi Deewangi Dekhi Nahi Kahi", "Apna Time Bhi Aayega", "Bandbudh Aur Budbak", 
    "Bhootu Hindi", "Brahmarakshas", "Choti Bahu", "Daayan", "Dadagiri", "Dance Bangla Dance (All seasons)", 
    "Do Dil Bandhe Ek Dori Se", "Ek Mahanayak - Dr B R Ambedkar", "Ek Mutthi Aasmaan", 
    "Ek Vivah Aisa Bhi", "Fear Files", "Guddan Tumse Na Ho Paayega", "Ikk Kudi Punjab Di", 
    "Iniya Iru Malargal", "Jamai Raja", "Jodha Akbar", "Laal Ishq (Hindi)", "Lag Ja Gale", 
    "Lakshmi Raave Maa Intiki", "Main Hoon Sath Tere", "Mr. Nonsense", "Qubool Hai", 
    "Sa Re Ga Ma Pa Lil Champs (Tamil)", "Saat Paake Bandha", "Sanjog", "Thirumangalyam", 
    "Vishkanya (Hindi)", "Woh Apna Sa", "Yeh Teri Galiyan", "Zee Rishtey Awards (All Years)", 
    "Zindagi Ki Mehek", "Suryakantham", "Kaise Mujhe Tum Mil Gaye", "Rannaghar", 
    "Savalyachi Janu Savali", "Ammayi Garu", "Amruthadhaare", "Anna", "Atal", "Bhabi Ji Ghar Par Hai!", 
    "Bhagya Lakshmi", "CHIRANJEEVI LAKSHMI SOWBHAGYAVATI", "Didi No.1 (Bengali)", "Gundamma Katha", 
    "Happu Ki Ultan Paltan", "Idhayam", "Jabilli Kosam Aakashamalle", "Jagadhatri (Telugu)", 
    "Janaki Ramayya Gari Manavaralu", "Kalavaari Kodalu Kanakamahalakshmi", "Karthigai Deepam", 
    "Kon Gopone Mon Bheseche", "Kumkum Bhagya", "Kundali Bhagya", "Lakshmi Kalyanam", "Maa Annayya", 
    "Maari", "Mala Bodol", "Meghasandesam", "Mukkupudaka", "Neem Phooler Mudhu", "Ninaithale Inikkum", 
    "Olimayamana Ethirkaalam", "Omkaram", "Padamati Sandhyaragam", "Prema Entha Maduram", 
    "Puber Moyna", "Rabb Se Hai Dua", "Sa Re Ga Ma Pa (Bangla)", "Sandhya Raagam", "Seetha Rama", 
    "Seethe Ramudi Katnam", "Tamizha Tamizha S3", "Trinayani (Telugu)", "Vasudha", "Veera", 
    "Nindu Noorella Saavasam", "Bahu Beti Aur ZEE5", "Anondi", "Jagriti", "SaReGaMaPa 2024", 
    "Jaane Anjaane Hum Mile", "Mounam Pesiyadhe", "Parineeta", "Jamai No. 1", "Lakshmi Niwas", 
    "Chamanthi", "Manasellam", "Gattimelam", "Naa Ninna Bidalaare", "Dance Bangla Dance S13", 
    "Duggamoni O Bagh Mama", "Chirodini Tumi Je Amar", "Tui Amar Hero (Tv Show)", "A Aa", 
    "Antim The Final Truth", "Attack: Part 1", "Babumoshai Bandookbaaz (Hindi)", "Bal Naren", 
    "Bangarraju Hindi Dubbed", "Bareilly Ki Barfi", "Baster – The Naxal Story", "Bengal Tiger (Hindi)", 
    "Bhaiyya Ji", "Bhaje Vaayu Vegam", "Chal Mohan Ranga", "Commando 3 (Hindi)", "DD Returns", 
    "Deool Band", "Dhaakad (Hindi)", "Dharmaveer 2: Mukkam Post Thane", "Dharmaveer: Mukkam Post Thane", 
    "Farrey", "Gadar 2 – The Katha Continues", "Gadar: Ek Prem Katha (Hindi)", "Game Changer", 
    "Gangubai Kathiawadi", "Geeta Govinda", "Ghoomer", "Hacked (Hindi)", "Hotel Mumbai (Hindi)", 
    "Identity", "Interrogation", "iSmart Shankar", "Janhit mein Jaari", "Jersey (Hindi)", 
    "Kaho Naa... Pyaar Hai (Hindi)", "Kala Shah Kala", "Kalavani 2", "Kanaa (Tamil Movie)", 
    "Kanam", "Kanchana 3", "Kathar Basha Endra Muthuramalingam", "Kavan", "Kayal", "Kedarnath", 
    "Kennedy Club", "Khuda Haafiz Chapter 2: Agni Pariksha", "Kisi Ka Bhai Kisi Ki Jaan", 
    "Kolamavu Kokila(KOKO)", "Krack", "Max", "Mulshi Pattern (Marathi)", "Padman", 
    "Qarib Qarib Singlle (Hindi)", "Raksha Bandhan (Hindi)", "Rashtra Kavach Om - The Battle Within", 
    "Real Tevar", "Sam Bahadur", "Sankranthiki Vasthunam", "Sarla Ek Koti", "Simmba", "Srimanthudu", 
    "Surya The Soldier", "Tejas", "The Kashmir Files (Hindi)", "The Kerala Story", "The Sabarmati Report", 
    "Uri The Surgical Strike (Hindi)", "Valimai (Hindi)", "Valimai (Telugu)", "Vedaa", 
    "Viduthalai - Part 1", "Woh Bhi Din The", "Kudumbasthan", "Abar Proloy", "Abhay", 
    "Ayali (Web Series)", "Churails", "Dhoop Ki Deewar", "Duranga", "Gyaarah Gyaarah", 
    "Jaanbaaz Hindustan ke", "Kaafir", "Manorathangal", "Rangbaaz: Darr Ki Rajneeti", "Sunflower", 
    "Taj", "The Broken News", "The Kashmir Files: Unreported", "Berlin", "Cabaret", "Chhatriwali", 
    "Kadak Singh", "Kakuda", "Kanjoos Makhichoos", "Mrs Undercover", "Rautu Ka Raaz", 
    "Silence 2: The Night Owl Bar Shootout", "Sirf Ek Bandaa Kaafi Hai", "State of Siege: Temple Attack", 
    "Tarla", "The Signature", "U-Turn", "Murshid", "Aindham Vedham", "Mithya", 
    "Divorce Ke Liye Kuch Bhi Karega", "Despatch", "Khoj - Parchaiyo Ke Uss Paar", "Hisaab Barabar", 
    "Mrs", "Pyaar Testing", "Crime Beat", "Vanvaas", "Viduthalai Part 2", "Prem Pratigya", "Parul", 
    "Kaafir (Movie)", "Tum Se Tum Tak", "Detective Sherdil", "Logout", "Parvati – Umeed Zindagi Ki", 
    "Ayyana Mane", "Costao", "Robin Hood 2025", "Ata Thambaycha Naay!", "Saru", "Andhar Maya", 
    "SaReGaMaPa Seniors Season 05", "Sang Hoon Main Tere", "Ayali (TV Shows)", "Uma Kaali", 
    "Chhal Kapat - The Deception", "Kusum", "Bibhishon", "Vikram (2022)", "Varisu", "Kamali (Marathi)", 
    "Kaalidhar Laapata", "Jarann", "Amader Dadamoni", "The Bhootnii", "Bhairavam", "Meghasandhesham", 
    "Samayal Express S2", "Sattamum Needhiyum", "Saunkan Saunkanay 2", "Chinnan Siru Kiliye", 
    "Main Teri Parchayi", "Bahu No. 1", "Bakaiti", "Tehran", "Aamar Boss", "Chhoriyan Chali Gaon", 
    "JSK-Janaki V Vs State of Kerala", "Single Pasanga", "Aankhon ki Gustakhiyaan", 
    "Veen Doghatli Hi Tutena", "Taarini", "Jayammu NischayammuRaa with Jagapathi", "Salangai Oli", 
    "Bedeni Jyotsnar Amar Prem", "Dosh Dine Dosh Lakh", "Kone Dekhaa Alo", "Dakuaan Da Munda 3", 
    "Kahani Har Ghar Ki", "Sri Raghavendra Mahatme", "Saregamapa 2025", "Paarijatham", "Jowar Bhanta", 
    "Housemates", "Janaawar - The Beast Within", "Mrigaya: The Hunt", "Raja Chinna Roja", 
    "Ganga Mai Ki Betiyan", "SUMATHI VALAVU", "Bhagwat Chapter One - Raakshas", "Kishkindhapuri", 
    "Madam Sengupta", "Ideabaaz", "Dashavatar", "Thode Door Thode Paas", "Rangbaaz: The Bihar Chapter", 
    "Ganoshotru", "Thirumangalyam New", "The Bengal files", "Jagadhatri (Hindi)", "Raktabeej 2", 
    "Honeymoon Se Hatya", "The pet detective", "Regai", "Aval Varuvala", "Annamalai Kudumbam", 
    "Sach - Subhash Chandra Show", "Saali Mohabbat", "Shabad - Reet aur Riwaaz", "Gharwali Pedwali", 
    "Ronkini Bhavan", "Heartiley Battery", "Besh Korechi Prem Korechi", "SaReGaMaPa Lil Champs Season 5", 
    "Devi Chowdhurani: Bandit Queen of Bengal", "Godday Godday Chaa 2", "Taare Dhori Dhori Mone Kori", 
    "Ek Diwaane Ki Deewaniyat", "Date with Saie (Movie)", "Bhabiji Ghar Par Hai 2.0", "Vritta", 
    "Joto Kando Kolkatatei", "45", "Lakshmi Nivas", "Mastiii 4", "Sirai", "Safia Safdar", 
    "Shubh Shravanii", "Kaalipotka", "Vaagai Sooda Vaa", "PARASAKTHI", "Devkhel", 
    "Bhanupriya Bhooter Hotel", "Mana Shankara Vara Prasad Garu", "Uttar", "Kennedy", 
    "Krantijyoti Vidyalay Marathi Madhyam", "Shabdam", "Jab Khuli Kitaab", "Thadayam", 
    "Bhartha Mahasayulaku Wignyapthi", "Landlord", "Abar Proloy 2", "Gandhi Talks", 
    "ZEE CINE AWARDS 2026", "Pookie", "Andha Pyaar 2.0", "PRAKAMBANAM", 
    "Aga Aga Saunbai Kay Mhantay Sasubai (Movie)", "Street 9 (Sharea Tessa)", "Saat Pake Bandha", 
    "Kasaragod Embassy", "Abdullahpur Ka Devdas", "Bhabiji Ghar Par Hain: Fun on the Run", 
    "Projapati 2", "Mom Talks: Maa Ki Baat Maa Ke Jazbaat", "Hey Balwanth", "Rubaab", 
    "Everyone loves Saurabh Handa", "Kaakee Circus", "Kamala Nibas", "Kaathal the core", "Assi", 
    "Ashakal Aayiram", "BANDMELAM", "JERAX", "Kerala Story 2", "Dhumketu", 
    "Gaddi Jaandi Ae Chalaangaan Maardi", "Carry On Jatta 3", "Jatt & Juliet 3", "Kali Jotta", 
    "Oye Bhole Oye", "Annhi Dea Mazaak Ae", "Aaja Mexico Challiye", "Blackia 2", "Je Jatt Vigarh Gya", 
    "Ni Main Sass Kuttni 2", "Kudi Haryane Val Di", "Shinda Shinda No Papa", "Shikaari", 
    "Jatt Nuu Chudail Takri", "Sarpanchi 2024", "Ucha Dar Babe Nanak Da", "Shayar", "Buhe Bariyan", 
    "Laxmi Raj", "Rickshaw Romeo", "Teen Yaar Twisted Pyaar", "The Truth Serum Wife", "Two Sisters", 
    "Muka Ghya Muka", "Pandu Hawaldar", "Songadya", "Tumcha Aamcha Jamla (Movie)", "Trademark of ZEE TV", 
    "Annapoorna", "Brahmagantu", "Jagruti", "Kalyanamasthu", "Paaru (Marathi)", "Sandhyaraaga", 
    "Shravani Subramanya", "Srikaram Shubhakaram", "Sa Re Ga Ma Pa - The Next Singing Youth Icon", 
    "SA RE GA MA PA Lil Champs Season 4", "Ummadi Kutumbam", "Naag Bhairavi", "Ennallo Vechina Hrudayam", 
    "Sathi Sata Janmara", "Tula Japnar Aahe", "Dance Jodi Dance Reloaded 3", "Super Serial Championship Season 4", 
    "Bhaiaji Superhittt", "Fatteshikast (Marathi)", "Koi... Mil Gaya", "Parmanu The Story Of Pokhran", 
    "Spyder (Hindi)", "Taxiwaala", "Riwaj", "Mazaka", "Kingston", "Daveed", 
    "Tere Chehre Se Nazar Nahi Hatati", "Gharana Mogudu", "Agnyathavasi", "DD Next level", 
    "Prince and Family", "Mafia - Game for Life", "Tamilarasan", "Sonar Jalsaghar", "Sriman Bhogoban Das", 
    "S.I.T. Bengal", "Lights, Camera, Achhan", "AABHYANTHARA KUTTAVAALI", "What a Kismat", "Sthal", 
    "Baai Tujhyapayi", "Comedy Khiladigalu 5", "Akshardham: Operation Vajra Shakti (2025)", 
    "Vikkatakavi - The Movie", "Dance Karnataka Dance 2025", "Durga", "Murugesan +2", 
    "Ondu Sarala Prema Kathe", "Be dune teen", "Paavanaganga", "Dance Odisha Dance - Celebrity with Little Masters", 
    "Kesariya@100", "Court Martial", "Adi Lakshmi Purana", "Aranyar Prachin Probad", "Natsamrat", 
    "Chembarathy", "Hamlet", "Lakshmi Raave Maa Intiki (New)", "Fab5", "Chote Tara ka Bada Gadar", 
    "Aaranyak", "Beauty", "Mask", "Char Chaughi", "Kapus Kondyachi Goshta", "Bha Bha Ba", 
    "Gurram Paapi Reddy", "Comedy Khiladi Juniors", "Parashakthi Pongal Kondattam", "Short & Sweet", 
    "Khiladi Jodies", "Chi Sou Mahalakshmi", "Kongu Bangaram", "Jai 2026", "Aata", 
    "NELLIKKAMPOYIL NIGHT RIDERS", "Drama Juniors Season 2", "Baal Krishna", "D/o Prasad Rao: Kanabadutaledhu", 
    "Krishna Rukku", "Sose Tanda Soubhagya", "Kichi Sata Kichi Michha", "Alam Tani", 
    "Noqta Al Ameya (Blind Spot)", "Zee Natya Gaurav Puraskar 2026", "Raja Jotaka", "Sanai Chaughade", 
    "Ugadi Ki Vasthunam Sandadi Testhunam", "Bookie", "Hey Kay Navin?", "Karna (Telugu)", 
    "The B Gang- Punjab Chapter", "Unlimit Awards 2026", "Deergha Sumangali Bhava", "Know Your Leader", 
    "Raja Queen 2026", "Deep Jyoti", "DETECTIVE DHANANJAY: RAHASYAJAAL", "LIK Audio Launch", 
    "Sa Re Ga Ma Pa Li'l Champs", "The Family Assembly", "Valyettan", "Boishakhi Hullor", 
    "AADU 3", "Love Mocktail 3", "Bowling-ah? Fielding-ah?", "Cricket Darbar", "Tighee", "Neelira"
]

# Sort asset list by length descending to match longer names first (e.g., "Kumkum Bhagya (Arabic)" before "Kumkum Bhagya")
ASSET_LIST_SORTED = sorted(ASSET_LIST, key=len, reverse=True)

# --- SCRAPER UI ---
st.sidebar.header("⚙️ Target Profile Configuration")

channel_target = st.sidebar.text_input(
    "Channel Identifier / ID", 
    value="",
    help="Accepts Public Links, Usernames, or Raw Numeric IDs (e.g., -10012345678)"
)

joinchat_target = st.sidebar.text_input(
    "Private Invite Link (joinchat)", 
    value="",
    placeholder="https://t.me/+...",
    help="Paste private invite links here (starts with + or joinchat)"
)

limit = st.sidebar.number_input("Maximum Record Limit", min_value=1, max_value=20000, value=500, step=50)
keyword = st.sidebar.text_input("Context Filter Keyword (Optional)")

# Helper logic to fetch all joined channels if inputs are empty
async def fetch_joined_channels():
    channels_list = []
    async for dialog in client.iter_dialogs():
        if dialog.is_channel:
            channels_list.append({
                'Channel Name': dialog.name,
                'Channel ID': dialog.id
            })
    return pd.DataFrame(channels_list)

async def scrape_logic():
    if joinchat_target.strip():
        target = joinchat_target.strip()
    else:
        target = channel_target.strip()
        if target.startswith('-') or target.isdigit():
            target = int(target)
            
    entity = await client.get_entity(target)
    channel_name = entity.title
    sub_count = getattr(entity, 'participants_count', 'Hidden/N/A')
    
    if getattr(entity, 'username', None):
        channel_url = f"https://t.me/{entity.username}"
    else:
        channel_url = f"https://t.me/c/{abs(entity.id)}"
        
    data = []
    progress_bar = st.progress(0.0)
    status_text = st.empty()
    
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
        
        msg_text = msg.text or ""
        
        # 1. Classify Content Type (Video vs Message)
        content_type = "Message"
        if msg.video or (msg.media and isinstance(msg.media, MessageMediaDocument) and any(
            getattr(attr, 'mime_type', '').startswith('video/') for attr in [msg.media.document] if hasattr(msg.media, 'document')
        )):
            content_type = "Video"
            
        # 2. ADVANCED PARTIAL MATCH LOGIC
        # Clean up target text (remove special characters/extra spaces to increase matching rates)
        search_blob = f" {msg_text} {fname} ".lower()
        search_blob_clean = re.sub(r'[^a-z0-9\s]', ' ', search_blob)
        search_blob_clean = " ".join(search_blob_clean.split())

        matched_asset = "na"
        for asset in ASSET_LIST_SORTED:
            # Clean asset string for a loose structural comparison
            asset_clean = asset.lower()
            asset_clean_noparen = re.sub(r'[^a-z0-9\s]', ' ', asset_clean)
            asset_clean_final = " ".join(asset_clean_noparen.split())
            
            # Checks if cleaned asset name exists as a substring or part of full string
            if asset_clean_final in search_blob_clean or asset_clean in search_blob:
                matched_asset = asset
                break
        
        data.append({
            'Channel Name': channel_name,
            'Channel ID': entity.id,
            'Subscribers': sub_count,
            'Date': dt, 
            'Views': msg.views or 0, 
            'File Name': fname, 
            'Asset Name': matched_asset,
            'Content Type': content_type,
            'Message Content': msg_text,
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
        
    elif not channel_target.strip() and not joinchat_target.strip():
        st.info("🔍 Targets are empty! Fetching your joined channels list...")
        with st.spinner("Loading channels ledger from Telegram..."):
            try:
                channels_df = loop.run_until_complete(fetch_joined_channels())
                if not channels_df.empty:
                    st.success("📋 Found Channels! Copy the 'Channel ID' and paste it into the Sidebar input.")
                    st.dataframe(channels_df, use_container_width=True)
                else:
                    st.warning("No channels found on this account.")
            except Exception as e:
                st.error(f"Failed to fetch list: {e}")
                
    else:
        with st.spinner("Extracting parameters and querying Telegram ledger..."):
            try:
                df, title, total_subs = loop.run_until_complete(scrape_logic())
                
                if not df.empty:
                    st.success(f"Transaction Complete: Extracted {len(df)} records from database context.")
                    
                    m1, m2, m3 = st.columns(3)
                    m1.metric("Channel Target Title", title)
                    m2.metric("Subscriber Capacity", total_subs)
                    m3.metric("Records Scraped", len(df))
                    
                    st.divider()
                    st.dataframe(df, use_container_width=True)
                    
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
