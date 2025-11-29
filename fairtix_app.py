import streamlit as st
import pandas as pd
import datetime
import uuid

# --- PAGE CONFIGURATION (Mobile Optimization) ---
st.set_page_config(
    page_title="FairTix",
    page_icon="🎟️",
    layout="centered", # Centered is better for mobile
    initial_sidebar_state="collapsed"
)

# --- CUSTOM CSS (The "Figma" Look) ---
# This hides the default Streamlit header and styles buttons to look like apps
st.markdown("""
    <style>
    /* Force Dark Theme Background */
    .stApp {
        background-color: #0f172a;
        color: white;
    }
    
    /* Hide Streamlit Elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Card Styling */
    .css-1r6slb0, .css-12oz5g7 {
        background-color: #1e293b;
        border-radius: 15px;
        padding: 20px;
        border: 1px solid #334155;
        margin-bottom: 10px;
    }
    
    /* Success Message Styling */
    .stSuccess {
        background-color: #064e3b !important;
        color: #6ee7b7 !important;
        border-radius: 10px;
    }
    
    /* Error Message Styling */
    .stError {
        background-color: #7f1d1d !important;
        color: #fca5a5 !important;
        border-radius: 10px;
    }
    
    /* Make Buttons full width and rounded */
    .stButton>button {
        width: 100%;
        border-radius: 25px;
        font-weight: bold;
        height: 50px;
        background-color: #3b82f6;
        color: white;
        border: none;
    }
    </style>
""", unsafe_allow_html=True)

# --- SESSION STATE SETUP ---
if 'tickets' not in st.session_state:
    st.session_state['tickets'] = []
    # Pre-seed one ticket for the demo
    st.session_state['tickets'].append({
        "ticket_id": "NFT-8821",
        "event_name": "Graduation Gala 2025",
        "owner": "Alice (You)",
        "face_value": 20.0,
        "resale_price": 20.0,
        "for_sale": False,
        "image": "https://images.unsplash.com/photo-1492684223066-81342ee5ff30"
    })

# --- APP HEADER ---
col1, col2 = st.columns([4, 1])
with col1:
    st.markdown("## FairTix 🎟️")
with col2:
    # Role Switcher (Hidden in a tiny expander for demo purposes)
    with st.expander("👤"):
        user_role = st.radio("User:", ["Alice (You)", "Organizer"])

# --- NAVIGATION TABS (Like a Mobile App) ---
tab1, tab2, tab3 = st.tabs(["🔥 Discover", "👛 Wallet", "⚙️ Dashboard"])

# --- TAB 1: DISCOVER ---
with tab1:
    st.image("https://images.unsplash.com/photo-1492684223066-81342ee5ff30", use_container_width=True)
    st.markdown("### Graduation Gala 2025")
    st.caption("Fri, Jun 20 • Grand Hall, Reims")
    
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("#### $20.00")
    with c2:
        st.button("Sold Out", disabled=True)
    
    st.info("ℹ️ Official tickets sold out. Check secondary market.")

# --- TAB 2: WALLET (THE MAIN DEMO) ---
with tab2:
    st.markdown("### My Tickets")
    
    my_tickets = [t for t in st.session_state['tickets'] if t['owner'] == "Alice (You)"]
    
    if not my_tickets:
        st.write("No tickets yet.")
    else:
        for t in my_tickets:
            # TICKET CARD
            with st.container():
                st.image(t['image'], use_container_width=True)
                st.markdown(f"**{t['event_name']}**")
                st.caption(f"ID: {t['ticket_id']} • Face Value: ${t['face_value']}")
                
                # QR Code simulation
                st.markdown("---")
                c_qr1, c_qr2, c_qr3 = st.columns([1,2,1])
                with c_qr2:
                    # Simple QR code image
                    st.image("https://api.qrserver.com/v1/create-qr-code/?size=150x150&data=FairTixProof", use_container_width=True)
                st.caption("Scan at entry")
                
                st.markdown("---")
                st.write("#### Resell Ticket")
                
                # THE SMART CONTRACT LOGIC
                new_price = st.number_input("Set Price ($)", value=float(t['face_value']), step=1.0)
                cap = t['face_value'] * 1.10
                
                if st.button("List for Resale"):
                    if new_price > cap:
                        st.error(f"⛔ BLOCKED: Price ${new_price} exceeds the 110% Smart Contract Cap (${cap:.2f})")
                    else:
                        st.success(f"✅ SUCCESS: Listed for ${new_price}")
                        # logic to move ticket would go here

# --- TAB 3: ORGANIZER ---
with tab3:
    st.write("Organizer Stats")
    st.metric("Total Sales", "$1,000")
    st.metric("Royalty Earnings", "$45.00")
    st.caption("Smart Contract deployed on Polygon")
