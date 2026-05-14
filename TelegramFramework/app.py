import qrcode
from io import BytesIO
from PIL import Image

# ... (rest of your imports and setup) ...

# --- SIDEBAR AUTHENTICATION ---
with st.sidebar:
    st.header("👤 Developer")
    st.markdown(f"**{NAME}**")
    st.divider()
    
    async def get_auth():
        return await client.is_user_authorized()
    
    is_authorized = loop.run_until_complete(get_auth())

    if not is_authorized:
        login_method = st.radio("Choose Login Method", ["OTP (Phone)", "QR Code"])

        if login_method == "OTP (Phone)":
            st.header("🔐 OTP Login")
            phone = st.text_input("Phone Number (+...)", placeholder="+91...")
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
            st.header("📲 QR Login")
            if st.button("Generate QR Code"):
                qr_container = st.empty()
                
                async def do_qr_login():
                    qr_login = await client.qr_login()
                    
                    while not qr_login.is_logged_in():
                        # Create QR Image
                        img = qrcode.make(qr_login.url)
                        buf = BytesIO()
                        img.save(buf)
                        
                        with qr_container.container():
                            st.image(buf.getvalue(), caption="Scan this with Telegram > Settings > Devices > Link Desktop Device")
                            st.warning("The code expires in 30 seconds.")
                        
                        try:
                            # Wait for scan with a timeout
                            await qr_login.wait(timeout=30)
                            st.success("Successfully logged in via QR!")
                            st.rerun()
                        except asyncio.TimeoutError:
                            # Re-generate if it expires
                            qr_login = await client.qr_login()
                        except Exception as e:
                            st.error(f"Error: {e}")
                            break

                loop.run_until_complete(do_qr_login())

    else:
        st.success("✅ Telegram Connected")
        if st.button("Logout"):
            loop.run_until_complete(client.log_out())
            st.rerun()
