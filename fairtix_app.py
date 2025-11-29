import streamlit as st
import pandas as pd
import datetime
import uuid

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="FairTix | Decentralized Ticketing",
    page_icon="🎟️",
    layout="wide"
)

# --- SESSION STATE (The "Blockchain" Simulation) ---
# We use session_state to persist data as if it were on a blockchain ledger.

if 'events' not in st.session_state:
    st.session_state['events'] = []

if 'tickets' not in st.session_state:
    st.session_state['tickets'] = []

if 'ledger' not in st.session_state:
    st.session_state['ledger'] = []

# Simulated Wallets (Users)
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


# --- HELPER FUNCTIONS (Smart Contract Logic) ---

def log_transaction(tx_type, from_user, to_user, details, status):
    """Records an action to the immutable ledger."""
    st.session_state['ledger'].append({
        "Timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Type": tx_type,
        "From": from_user,
        "To": to_user,
        "Details": details,
        "Status": status
    })


def create_event(name, total_supply, face_value):
    """Mints a batch of NFT tickets."""
    event_id = str(uuid.uuid4())[:8]
    new_event = {
        "id": event_id,
        "name": name,
        "supply": total_supply,
        "price": face_value,
        "organizer": "Organizer (You)"
    }
    st.session_state['events'].append(new_event)

    # Mint Tickets
    for i in range(total_supply):
        st.session_state['tickets'].append({
            "ticket_id": f"{event_id}-{i + 1}",
            "event_id": event_id,
            "event_name": name,
            "owner": "Organizer (You)",
            "face_value": face_value,
            "for_sale": True,
            "resale_price": face_value  # Initial price is face value
        })

    log_transaction("MINT", "System", "Organizer", f"Minted {total_supply} tickets for {name}", "SUCCESS")


def buy_ticket(ticket_id, buyer_name):
    """Handles primary market purchase."""
    ticket = next((t for t in st.session_state['tickets'] if t['ticket_id'] == ticket_id), None)
    buyer_wallet = st.session_state['wallets'][buyer_name]

    if ticket and ticket['for_sale']:
        price = ticket['resale_price']

        if buyer_wallet['balance'] >= price:
            # Transfer Funds
            buyer_wallet['balance'] -= price
            st.session_state['wallets'][ticket['owner']]['balance'] += price

            # Transfer Ownership (NFT)
            prev_owner = ticket['owner']
            ticket['owner'] = buyer_name
            ticket['for_sale'] = False  # Remove from market

            log_transaction("BUY", buyer_name, prev_owner, f"Bought Ticket {ticket_id} for ${price}", "SUCCESS")
            return True, "Ticket purchased successfully!"
        else:
            return False, "Insufficient funds!"
    return False, "Ticket not available."


def list_resale(ticket_id, seller_name, resale_price):
    """
    SMART CONTRACT LOGIC: ENFORCE PRICE CAP
    This is the core grading criteria feature.
    """
    ticket = next((t for t in st.session_state['tickets'] if t['ticket_id'] == ticket_id), None)

    if ticket:
        max_price = ticket['face_value'] * 1.10  # 110% CAP

        if resale_price > max_price:
            # REVERT TRANSACTION
            log_transaction("RESALE_ATTEMPT", seller_name, "Market",
                            f"Attempted sell {ticket_id} for ${resale_price} (Cap: ${max_price:.2f})", "REVERTED")
            return False, f"⚠️ SMART CONTRACT ERROR: Price ${resale_price} exceeds the 110% cap (${max_price:.2f}). Transaction Reverted."
        else:
            # ALLOW LISTING
            ticket['for_sale'] = True
            ticket['resale_price'] = resale_price
            log_transaction("LISTING", seller_name, "Market", f"Listed {ticket_id} for ${resale_price}", "SUCCESS")
            return True, f"✅ Success! Ticket listed for ${resale_price}."


# --- SIDEBAR NAVIGATION ---
st.sidebar.title("FairTix 🎟️")
st.sidebar.markdown("Decentralized Ticketing System")

user_role = st.sidebar.selectbox("Select User Role (Simulated)", list(st.session_state['wallets'].keys()))

# --- ADMIN LOGIN PROTECTION ---
if user_role == "Organizer (You)":
    if not st.session_state['admin_logged_in']:
        st.sidebar.markdown("---")
        st.sidebar.warning("🔒 Admin Login Required")
        
        with st.sidebar.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submit = st.form_submit_button("Login")
            
            if submit:
                if username == "admin" and password == "admin":
                    st.session_state['admin_logged_in'] = True
                    st.rerun()
                else:
                    st.error("Invalid credentials")
        
        st.info("Please log in using the sidebar to access the Organizer Dashboard.")
        st.stop()  # Stop execution here to prevent access
    else:
        if st.sidebar.button("Logout"):
            st.session_state['admin_logged_in'] = False
            st.rerun()

# --- MAIN APP LOGIC ---

current_balance = st.session_state['wallets'][user_role]['balance']
st.sidebar.metric("Current Wallet Balance", f"${current_balance}")

menu = st.sidebar.radio("Navigation",
                        ["Marketplace", "My Wallet & Tickets", "Organizer Dashboard", "Blockchain Explorer"])

# --- PAGE: ORGANIZER DASHBOARD ---
if menu == "Organizer Dashboard":
    st.header("⚡ Organizer Dashboard")
    st.markdown("Create events and mint NFT tickets.")

    if user_role != "Organizer (You)":
        st.warning("Access Denied: You are not an Organizer.")
    else:
        with st.form("create_event_form"):
            col1, col2, col3 = st.columns(3)
            with col1:
                ev_name = st.text_input("Event Name", value="Graduation Party 2025")
            with col2:
                ev_supply = st.number_input("Total Tickets", min_value=1, value=50)
            with col3:
                ev_price = st.number_input("Face Value ($)", min_value=1, value=20)

            submitted = st.form_submit_button("Mint Tickets on Blockchain")

            if submitted:
                create_event(ev_name, ev_supply, ev_price)
                st.success(f"Successfully minted {ev_supply} NFT tickets for {ev_name}!")

# --- PAGE: MARKETPLACE ---
elif menu == "Marketplace":
    st.header("🛒 Ticket Marketplace")
    st.markdown("Buy verified NFT tickets directly from organizers or other fans.")

    # Filter tickets that are FOR SALE and NOT owned by current user
    available_tickets = [t for t in st.session_state['tickets'] if t['for_sale'] and t['owner'] != user_role]

    if not available_tickets:
        st.info("No tickets currently available for sale.")
    else:
        # Display as cards
        for t in available_tickets:
            with st.container():
                col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
                with col1:
                    st.subheader(t['event_name'])
                    st.caption(f"NFT ID: {t['ticket_id']}")
                with col2:
                    st.write(f"**Seller:** {t['owner']}")
                with col3:
                    st.metric("Price", f"${t['resale_price']}")
                    if t['resale_price'] > t['face_value']:
                        st.caption("⚠️ Resale Market")
                with col4:
                    if st.button(f"Buy Now", key=f"buy_{t['ticket_id']}"):
                        success, msg = buy_ticket(t['ticket_id'], user_role)
                        if success:
                            st.success(msg)
                            st.rerun()
                        else:
                            st.error(msg)
                st.divider()

# --- PAGE: MY WALLET ---
elif menu == "My Wallet & Tickets":
    st.header(f"🎟️ {user_role}'s Wallet")

    # Filter tickets owned by current user
    my_tickets = [t for t in st.session_state['tickets'] if t['owner'] == user_role]

    if not my_tickets:
        st.info("You don't own any tickets yet.")
    else:
        st.subheader("Your Inventory")
        for t in my_tickets:
            with st.expander(f"{t['event_name']} (ID: {t['ticket_id']})"):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Face Value:** ${t['face_value']}")
                    st.write(f"**Status:** {'Listed for Sale' if t['for_sale'] else 'In Wallet'}")

                with col2:
                    st.write("### Sell Ticket")
                    st.write("Smart Contract Rule: Max Price = 110% of Face Value")

                    new_price = st.number_input(
                        "Set Resale Price ($)",
                        min_value=0.0,
                        value=float(t['face_value']),
                        key=f"price_{t['ticket_id']}"
                    )

                    if st.button("List for Resale", key=f"sell_{t['ticket_id']}"):
                        success, msg = list_resale(t['ticket_id'], user_role, new_price)
                        if success:
                            st.success(msg)
                            st.rerun()
                        else:
                            st.error(msg)

# --- PAGE: BLOCKCHAIN EXPLORER ---
elif menu == "Blockchain Explorer":
    st.header("⛓️ Blockchain Ledger")
    st.markdown("Immutable record of all transactions. This proves transparency.")

    if st.session_state['ledger']:
        df = pd.DataFrame(st.session_state['ledger'])


        # Color code status
        def color_status(val):
            color = 'green' if val == 'SUCCESS' else 'red'
            return f'color: {color}'


        st.dataframe(df.style.map(color_status, subset=['Status']), use_container_width=True)
    else:
        st.info("No transactions recorded yet.")

# --- FOOTER ---
st.markdown("---")
st.caption("FairTix Project Prototype | Built with Python & Streamlit")
