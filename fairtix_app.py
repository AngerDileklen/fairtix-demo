import streamlit as st
import pandas as pd
import datetime
import uuid

# --- PAGE CONFIGURATION ---
# 'centered' layout often looks better on mobile than 'wide', but we can keep wide 
# and handle the columns manually for maximum control.
st.set_page_config(
    page_title="FairTix | Decentralized Ticketing",
    page_icon="🎟️",
    layout="wide" 
)

# --- MOBILE DETECTION ---
# We wrap this in a try-except block so the app doesn't crash if the library isn't installed.
try:
    from streamlit_js_eval import streamlit_js_eval
    # Get screen width (returns None on first run, so we default to 1920)
    screen_width = streamlit_js_eval(js_expressions='window.innerWidth', key='SCR')
    if screen_width is None:
        screen_width = 1920
    
    is_mobile = screen_width < 768
except ImportError:
    # Fallback if library not installed
    is_mobile = False

# --- SESSION STATE (The "Blockchain" Simulation) ---
if 'events' not in st.session_state:
    st.session_state['events'] = []
if 'tickets' not in st.session_state:
    st.session_state['tickets'] = []
if 'ledger' not in st.session_state:
    st.session_state['ledger'] = []

# Simulated Wallets
if 'wallets' not in st.session_state:
    st.session_state['wallets'] = {
        "Organizer (You)": {"balance": 1000, "role": "admin"},
        "Alice (Fan)": {"balance": 200, "role": "user"},
        "Bob (Scalper)": {"balance": 500, "role": "user"},
        "Charlie (Fan)": {"balance": 150, "role": "user"}
    }

# Login State
if 'admin_logged_in' not in st.session_state:
    st.session_state['admin_logged_in'] = False

# --- HELPER FUNCTIONS ---
def log_transaction(tx_type, from_user, to_user, details, status):
    st.session_state['ledger'].append({
        "Timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Type": tx_type,
        "From": from_user,
        "To": to_user,
        "Details": details,
        "Status": status
    })

def create_event(name, total_supply, face_value):
    event_id = str(uuid.uuid4())[:8]
    new_event = {
        "id": event_id,
        "name": name,
        "supply": total_supply,
        "price": face_value,
        "organizer": "Organizer (You)"
    }
    st.session_state['events'].append(new_event)
    for i in range(total_supply):
        st.session_state['tickets'].append({
            "ticket_id": f"{event_id}-{i + 1}",
            "event_id": event_id,
            "event_name": name,
            "owner": "Organizer (You)",
            "face_value": face_value,
            "for_sale": True,
            "resale_price": face_value
        })
    log_transaction("MINT", "System", "Organizer", f"Minted {total_supply} tickets for {name}", "SUCCESS")

def buy_ticket(ticket_id, buyer_name):
    ticket = next((t for t in st.session_state['tickets'] if t['ticket_id'] == ticket_id), None)
    buyer_wallet = st.session_state['wallets'][buyer_name]
    if ticket and ticket['for_sale']:
        price = ticket['resale_price']
        if buyer_wallet['balance'] >= price:
            buyer_wallet['balance'] -= price
            st.session_state['wallets'][ticket['owner']]['balance'] += price
            prev_owner = ticket['owner']
            ticket['owner'] = buyer_name
            ticket['for_sale'] = False
            log_transaction("BUY", buyer_name, prev_owner, f"Bought Ticket {ticket_id} for ${price}", "SUCCESS")
            return True, "Ticket purchased successfully!"
        else:
            return False, "Insufficient funds!"
    return False, "Ticket not available."

def list_resale(ticket_id, seller_name, resale_price):
    ticket = next((t for t in st.session_state['tickets'] if t['ticket_id'] == ticket_id), None)
    if ticket:
        max_price = ticket['face_value'] * 1.10
        if resale_price > max_price:
            log_transaction("RESALE_ATTEMPT", seller_name, "Market", f"Attempted sell {ticket_id} for ${resale_price}", "REVERTED")
            return False, f"⚠️ SMART CONTRACT ERROR: Price ${resale_price} exceeds cap (${max_price:.2f})."
        else:
            ticket['for_sale'] = True
            ticket['resale_price'] = resale_price
            log_transaction("LISTING", seller_name, "Market", f"Listed {ticket_id} for ${resale_price}", "SUCCESS")
            return True, f"✅ Success! Listed for ${resale_price}."

# --- SIDEBAR NAVIGATION ---
st.sidebar.title("FairTix 🎟️")
st.sidebar.markdown("Decentralized Ticketing System")

user_role = st.sidebar.selectbox("Select Role", list(st.session_state['wallets'].keys()))

# --- ADMIN LOGIN PROTECTION ---
if user_role == "Organizer (You)":
    if not st.session_state['admin_logged_in']:
        st.sidebar.warning("🔒 Admin Login Required")
        with st.sidebar.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            if st.form_submit_button("Login"):
                if username == "admin" and password == "admin":
                    st.session_state['admin_logged_in'] = True
                    st.rerun()
                else:
                    st.error("Invalid credentials")
        st.stop()
    else:
        if st.sidebar.button("Logout"):
            st.session_state['admin_logged_in'] = False
            st.rerun()

current_balance = st.session_state['wallets'][user_role]['balance']
st.sidebar.metric("Wallet Balance", f"${current_balance}")
menu = st.sidebar.radio("Navigation", ["Marketplace", "My Wallet & Tickets", "Organizer Dashboard", "Blockchain Explorer"])

# --- PAGE: ORGANIZER DASHBOARD ---
if menu == "Organizer Dashboard":
    st.header("⚡ Organizer Dashboard")
    
    if user_role != "Organizer (You)":
        st.warning("Access Denied.")
    else:
        with st.form("create_event_form"):
            # MOBILE ADAPTATION: Use 1 column for mobile, 3 for desktop
            if is_mobile:
                st.write("### Create New Event")
                ev_name = st.text_input("Event Name", value="Graduation Party 2025")
                ev_supply = st.number_input("Total Tickets", min_value=1, value=50)
                ev_price = st.number_input("Face Value ($)", min_value=1, value=20)
            else:
                col1, col2, col3 = st.columns(3)
                with col1: ev_name = st.text_input("Event Name", value="Graduation Party 2025")
                with col2: ev_supply = st.number_input("Total Tickets", min_value=1, value=50)
                with col3: ev_price = st.number_input("Face Value ($)", min_value=1, value=20)

            if st.form_submit_button("Mint Tickets"):
                create_event(ev_name, ev_supply, ev_price)
                st.success(f"Minted {ev_supply} tickets!")

# --- PAGE: MARKETPLACE ---
elif menu == "Marketplace":
    st.header("🛒 Ticket Marketplace")
    available_tickets = [t for t in st.session_state['tickets'] if t['for_sale'] and t['owner'] != user_role]

    if not available_tickets:
        st.info("No tickets available.")
    else:
        for t in available_tickets:
            with st.container():
                # MOBILE ADAPTATION: Vertical Stack vs Horizontal Columns
                if is_mobile:
                    # Mobile Card View
                    st.markdown(f"**{t['event_name']}** (ID: {t['ticket_id']})")
                    c1, c2 = st.columns(2)
                    with c1: st.caption(f"Seller: {t['owner']}")
                    with c2: st.metric("Price", f"${t['resale_price']}")
                    if st.button(f"Buy Now (${t['resale_price']})", key=f"buy_{t['ticket_id']}"):
                         success, msg = buy_ticket(t['ticket_id'], user_role)
                         if success: st.success(msg); st.rerun()
                         else: st.error(msg)
                    st.divider()
                else:
                    # Desktop Table Row View
                    col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
                    with col1:
                        st.subheader(t['event_name'])
                        st.caption(f"NFT ID: {t['ticket_id']}")
                    with col2:
                        st.write(f"**Seller:** {t['owner']}")
                    with col3:
                        st.metric("Price", f"${t['resale_price']}")
                    with col4:
                        if st.button(f"Buy Now", key=f"buy_{t['ticket_id']}"):
                            success, msg = buy_ticket(t['ticket_id'], user_role)
                            if success: st.success(msg); st.rerun()
                            else: st.error(msg)
                    st.divider()

# --- PAGE: MY WALLET ---
elif menu == "My Wallet & Tickets":
    st.header(f"🎟️ {user_role}'s Wallet")
    my_tickets = [t for t in st.session_state['tickets'] if t['owner'] == user_role]

    if not my_tickets:
        st.info("No tickets owned.")
    else:
        st.subheader("Your Inventory")
        for t in my_tickets:
            with st.expander(f"{t['event_name']} (ID: {t['ticket_id']})"):
                # Use standard columns here; they stack automatically well enough in expanders
                c1, c2 = st.columns(2)
                with c1:
                    st.write(f"**Face Value:** ${t['face_value']}")
                    st.write(f"**Status:** {'Listed' if t['for_sale'] else 'In Wallet'}")
                with c2:
                    new_price = st.number_input("Resale Price ($)", min_value=0.0, value=float(t['face_value']), key=f"p_{t['ticket_id']}")
                    if st.button("List for Resale", key=f"s_{t['ticket_id']}"):
                        success, msg = list_resale(t['ticket_id'], user_role, new_price)
                        if success: st.success(msg); st.rerun()
                        else: st.error(msg)

# --- PAGE: BLOCKCHAIN EXPLORER ---
elif menu == "Blockchain Explorer":
    st.header("⛓️ Blockchain Ledger")
    if st.session_state['ledger']:
        df = pd.DataFrame(st.session_state['ledger'])
        def color_status(val):
            return f'color: {"green" if val == "SUCCESS" else "red"}'
        
        # DataFrame is scrollable by default, which is good for mobile
        st.dataframe(df.style.map(color_status, subset=['Status']), use_container_width=True)
    else:
        st.info("No transactions yet.")

st.markdown("---")
st.caption(f"FairTix v2 | Mobile Mode: {'✅ ON' if is_mobile else '❌ OFF'}")
