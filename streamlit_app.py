import os
import streamlit as st
import requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

DEFAULT_API_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")

# Page Configuration
st.set_page_config(
    page_title="AI Support Decision Assistant",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }
    
    .main-title {
        font-size: 2.2rem;
        font-weight: 700;
        background: linear-gradient(135deg, #2563eb, #7c3aed);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
    }
    
    .sub-title {
        font-size: 1rem;
        color: #64748b;
        margin-bottom: 1.5rem;
    }
    
    .metric-card {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 1.25rem;
        margin-bottom: 1rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    
    .badge {
        display: inline-block;
        padding: 0.35rem 0.8rem;
        font-size: 0.85rem;
        font-weight: 700;
        border-radius: 9999px;
        letter-spacing: 0.05em;
        text-transform: uppercase;
    }
    
    .badge-approve {
        background-color: #dcfce7;
        color: #15803d;
        border: 1px solid #86efac;
    }
    
    .badge-photo {
        background-color: #fef9c3;
        color: #a16207;
        border: 1px solid #fde047;
    }
    
    .badge-reject {
        background-color: #fee2e2;
        color: #b91c1c;
        border: 1px solid #fca5a5;
    }
    
    .badge-info {
        background-color: #e0f2fe;
        color: #0369a1;
        border: 1px solid #7dd3fc;
    }

    .source-tag {
        display: inline-block;
        background: #f1f5f9;
        color: #475569;
        padding: 0.2rem 0.6rem;
        border-radius: 6px;
        font-size: 0.8rem;
        margin-right: 0.4rem;
        border: 1px solid #cbd5e1;
        font-family: monospace;
    }
</style>
""", unsafe_allow_html=True)

# Session State Initialization
if "auth_token" not in st.session_state:
    st.session_state.auth_token = None
if "user_email" not in st.session_state:
    st.session_state.user_email = None
if "user_id" not in st.session_state:
    st.session_state.user_id = None
if "api_url" not in st.session_state:
    st.session_state.api_url = DEFAULT_API_URL

# Helper for API headers
def get_auth_headers():
    if st.session_state.auth_token:
        return {"Authorization": f"Bearer {st.session_state.auth_token}"}
    return {}

def get_action_badge(action: str) -> str:
    action_upper = action.upper()
    if "APPROVE" in action_upper:
        css_class = "badge-approve"
    elif "PHOTO" in action_upper or "BILLING" in action_upper or "ESCALATE" in action_upper:
        css_class = "badge-photo"
    elif "REJECT" in action_upper:
        css_class = "badge-reject"
    else:
        css_class = "badge-info"
    return f'<span class="badge {css_class}">{action}</span>'

# Sidebar Navigation and Profile
with st.sidebar:
    st.markdown("### ⚙️ System Settings")
    api_url_input = st.text_input("Backend API URL", value=st.session_state.api_url)
    st.session_state.api_url = api_url_input.strip()

    # Health Check
    try:
        r = requests.get(f"{st.session_state.api_url}/", timeout=2)
        if r.status_code == 200:
            st.success("🟢 Backend Connected", icon="✅")
        else:
            st.warning(f"🟡 Backend Status {r.status_code}")
    except Exception:
        st.error("🔴 Backend Offline (Run FastAPI on port 8000)")

    st.markdown("---")

    if st.session_state.auth_token:
        st.markdown(f"**Logged in as:**\n👤 `{st.session_state.user_email}`")
        st.caption(f"User ID: #{st.session_state.user_id}")
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.auth_token = None
            st.session_state.user_email = None
            st.session_state.user_id = None
            st.rerun()
    else:
        st.info("Please log in or register to access ticket processing and history.")

# Main Application Views
if not st.session_state.auth_token:
    # ------------------ AUTHENTICATION VIEW ------------------
    st.markdown('<div class="main-title">🛡️ AI Support Decision Assistant</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">Automated, policy-grounded support ticket decision engine with RAG and JWT authentication</div>', unsafe_allow_html=True)

    tab_login, tab_register = st.tabs(["🔑 Login", "📝 Register New Account"])

    with tab_login:
        st.subheader("Login to your account")
        with st.form("login_form"):
            login_email = st.text_input("Email", placeholder="user@example.com")
            login_password = st.text_input("Password", type="password", placeholder="••••••••")
            login_submitted = st.form_submit_button("Sign In", use_container_width=True)

            if login_submitted:
                if not login_email or not login_password:
                    st.error("Please fill in both email and password.")
                else:
                    try:
                        resp = requests.post(
                            f"{st.session_state.api_url}/login",
                            json={"email": login_email, "password": login_password},
                            timeout=5
                        )
                        if resp.status_code == 200:
                            data = resp.json()
                            st.session_state.auth_token = data["access_token"]
                            st.session_state.user_id = data["user_id"]
                            st.session_state.user_email = data["email"]
                            st.success("Login successful! Redirecting...")
                            st.rerun()
                        else:
                            st.error(resp.json().get("detail", "Authentication failed."))
                    except Exception as e:
                        st.error(f"Error connecting to backend: {e}")

    with tab_register:
        st.subheader("Create a new account")
        with st.form("register_form"):
            reg_email = st.text_input("Email", placeholder="newuser@example.com")
            reg_password = st.text_input("Password (min 6 characters)", type="password", placeholder="••••••••")
            reg_submitted = st.form_submit_button("Create Account", use_container_width=True)

            if reg_submitted:
                if not reg_email or not reg_password:
                    st.error("Please provide both email and password.")
                elif len(reg_password) < 6:
                    st.error("Password must be at least 6 characters.")
                else:
                    try:
                        resp = requests.post(
                            f"{st.session_state.api_url}/register",
                            json={"email": reg_email, "password": reg_password},
                            timeout=5
                        )
                        if resp.status_code == 201:
                            st.success("Account created successfully! You can now log in.")
                        else:
                            st.error(resp.json().get("detail", "Registration failed."))
                    except Exception as e:
                        st.error(f"Error connecting to backend: {e}")

else:
    # ------------------ AUTHENTICATED USER DASHBOARD ------------------
    st.markdown('<div class="main-title">🛡️ AI Support Decision Assistant</div>', unsafe_allow_html=True)
    st.caption(f"Authenticated as **{st.session_state.user_email}** (User #{st.session_state.user_id})")

    tab_new, tab_history = st.tabs(["🚀 New Decision", "📜 Decision History"])

    with tab_new:
        st.subheader("Submit Customer Support Ticket")
        st.write("Enter the customer's request below to retrieve relevant policies and generate an evidence-backed AI decision.")

        # Quick preset examples for testing
        example_choice = st.selectbox(
            "Load a sample scenario (Optional):",
            [
                "-- Select a sample ticket --",
                "Damaged order above ₹2,000: 'I bought a luxury leather jacket for ₹4,500 (Order #9821). It arrived today with a tear down the sleeve. I want a refund.'",
                "Damaged order under ₹2,000: 'Order #4421: My ₹800 coffee mug arrived shattered yesterday in the mail. Can I please get a replacement sent?'",
                "Late return beyond 7 days: 'I received shoes 18 days ago (Order #1029). The size is slightly too tight for me. I would like to return them.'",
                "Valid return within 7 days: 'I purchased a cotton shirt 3 days ago (Order #3312). All original tags are intact and unworn. Can I return it?'",
                "Lost in transit (10+ days): 'My order #8819 was shipped 14 business days ago and the carrier tracking shows no scan update for over a week.'",
                "Vague ticket (missing info): 'Help, my item is broken!'"
            ]
        )

        preset_text = ""
        if example_choice != "-- Select a sample ticket --":
            preset_text = example_choice.split(": '", 1)[-1].rstrip("'")

        ticket_text = st.text_area(
            "Ticket Message",
            value=preset_text,
            height=120,
            placeholder="Describe the issue, order number, delivery date, item condition, or requested action..."
        )

        col_btn, col_blank = st.columns([1, 4])
        with col_btn:
            submit_btn = st.button("⚡ Evaluate Decision", type="primary", use_container_width=True)

        if submit_btn:
            if not ticket_text.strip():
                st.warning("Please enter a ticket message first.")
            else:
                with st.spinner("Retrieving policy documents & generating AI decision..."):
                    try:
                        resp = requests.post(
                            f"{st.session_state.api_url}/tickets",
                            headers=get_auth_headers(),
                            json={"message": ticket_text.strip()},
                            timeout=20
                        )
                        if resp.status_code == 201:
                            ticket_res = resp.json()
                            decision = ticket_res.get("decision", {})

                            st.success(f"Ticket #{ticket_res['ticket_id']} successfully processed and saved!")

                            # Decision Card Display
                            action_name = decision.get("action", "NEEDS_MORE_INFORMATION")
                            conf = decision.get("confidence", 0.0)
                            reason = decision.get("reason", "")
                            sources = decision.get("sources", [])

                            st.markdown("### 📋 AI Decision Result")
                            
                            c1, c2 = st.columns([2, 1])
                            with c1:
                                st.markdown(f"**Recommended Action:** {get_action_badge(action_name)}", unsafe_allow_html=True)
                            with c2:
                                st.metric("Confidence", f"{conf * 100:.1f}%")

                            st.progress(conf)

                            st.markdown("#### 💡 Policy Grounding & Reasoning")
                            st.info(reason)

                            st.markdown("#### 📚 Cited Knowledge Base Sources")
                            if sources:
                                badges_html = "".join([f'<span class="source-tag">📄 {s}</span>' for s in sources])
                                st.markdown(badges_html, unsafe_allow_html=True)
                            else:
                                st.write("No specific sources cited.")

                        elif resp.status_code == 401:
                            st.error("Session expired. Please log in again.")
                            st.session_state.auth_token = None
                            st.rerun()
                        else:
                            st.error(f"Error ({resp.status_code}): {resp.text}")
                    except Exception as e:
                        st.error(f"Failed to communicate with API: {e}")

    with tab_history:
        st.subheader("Your Ticket & Decision History")
        col_ref, col_spacer = st.columns([1, 5])
        with col_ref:
            refresh_btn = st.button("🔄 Refresh History", use_container_width=True)

        try:
            resp = requests.get(
                f"{st.session_state.api_url}/tickets",
                headers=get_auth_headers(),
                timeout=10
            )
            if resp.status_code == 200:
                tickets_data = resp.json()
                if not tickets_data:
                    st.info("No tickets submitted yet. Use the **New Decision** tab to submit your first ticket!")
                else:
                    st.write(f"Showing **{len(tickets_data)}** tickets submitted by your account:")

                    for t in tickets_data:
                        t_id = t["ticket_id"]
                        t_msg = t["message"]
                        t_date = t.get("ticket_created_at", "")
                        dec = t.get("decision")

                        action_badge = get_action_badge(dec["action"]) if dec else '<span class="badge badge-info">PENDING</span>'
                        conf_str = f"{dec['confidence']*100:.0f}%" if dec else "N/A"

                        with st.expander(f"Ticket #{t_id}: {t_msg[:60]}... — Action: {dec['action'] if dec else 'N/A'}"):
                            st.markdown(f"**Created:** `{t_date}` | **Action:** {action_badge} | **Confidence:** `{conf_str}`", unsafe_allow_html=True)
                            st.markdown(f"**Customer Message:**\n> {t_msg}")

                            if dec:
                                st.markdown(f"**Reasoning:**\n{dec['reason']}")
                                if dec.get("sources"):
                                    src_html = "".join([f'<span class="source-tag">📄 {s}</span>' for s in dec["sources"]])
                                    st.markdown(f"**Sources:** {src_html}", unsafe_allow_html=True)

                            # Test endpoint GET /tickets/{id} verification button
                            if st.button(f"🔍 Inspect via GET /tickets/{t_id}", key=f"inspect_{t_id}"):
                                inspect_resp = requests.get(
                                    f"{st.session_state.api_url}/tickets/{t_id}",
                                    headers=get_auth_headers()
                                )
                                if inspect_resp.status_code == 200:
                                    st.json(inspect_resp.json())
                                else:
                                    st.error(f"Error fetching ticket: {inspect_resp.status_code}")
            elif resp.status_code == 401:
                st.error("Session expired. Please log in again.")
                st.session_state.auth_token = None
                st.rerun()
            else:
                st.error(f"Failed to load history: {resp.text}")
        except Exception as e:
            st.error(f"Unable to fetch history from API: {e}")
