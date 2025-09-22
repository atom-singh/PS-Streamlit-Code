import streamlit as st
from openai import OpenAI

# -----------------------------
# Mock Order Database
# -----------------------------
mock_order_db = {
    "john@example.com": [
        {
            "order_id": "ORD12345",
            "status": "Out for Delivery",
            "expected_delivery": "2025-07-06",
            "carrier": "BlueDart",
            "tracking_link": "https://track.bluedart.com/ORD12345",
            "amount": 1299
        },
        {
            "order_id": "ORD11111",
            "status": "Shipped",
            "expected_delivery": "2025-07-08",
            "carrier": "Delhivery",
            "tracking_link": "https://track.delhivery.com/ORD11111",
            "amount": 899
        }
    ],
    "alice@example.com": [
        {
            "order_id": "ORD67890",
            "status": "Shipped",
            "expected_delivery": "2025-07-08",
            "carrier": "Delhivery",
            "tracking_link": "https://track.delhivery.com/ORD67890",
            "amount": 899
        }
    ],
    "bob@example.com": [
        {
            "order_id": "ORD54321",
            "status": "Delivered",
            "expected_delivery": "2025-07-02",
            "carrier": "Xpressbees",
            "tracking_link": "https://xpressbees.com/track/ORD54321",
            "amount": 1549
        }
    ],
    "sara@example.com": [
        {
            "order_id": "ORD98765",
            "status": "Processing",
            "expected_delivery": "2025-07-10",
            "carrier": "Ecom Express",
            "tracking_link": "https://ecomexpress.in/track/ORD98765",
            "amount": 2199
        }
    ]
}

# -----------------------------
# OpenAI Client
# -----------------------------
client = OpenAI(api_key= st.secrets["OPENAI_API_KEY"])  
# replace with st.secrets["OPENAI_API_KEY"]

# -----------------------------
# Agent Functions
# -----------------------------
def order_tracking_agent(order, user_prompt):
    prompt = f"""
    You are a friendly and helpful customer support assistant.

    A customer asked: "{user_prompt.strip()}"

    Their order details:
    - Order ID: {order['order_id']}
    - Status: {order['status']}
    - Carrier: {order['carrier']}
    - Expected Delivery: {order['expected_delivery']}
    - Amount: ₹{order['amount']}
    - Tracking Link: {order['tracking_link']}

    Write a warm, natural response:
    - Acknowledge the question
    - Answer using order info
    - Provide tracking link & delivery timeline
    - Be conversational and supportive
    """
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content.strip()


def return_agent(order, user_email, user_prompt):
    prompt = f"""
    You are a helpful, empathetic customer support assistant in a live chat.

    Customer message: "{user_prompt.strip()}"

    Order details:
    - Order ID: {order['order_id']}
    - Status: {order['status']}
    - Expected Delivery: {order['expected_delivery']}
    - Refund Amount: ₹{order['amount']}
    - Carrier: {order['carrier']}
    - Tracking: {order['tracking_link']}
    - Email: {user_email}

    If delivered → confirm return scheduled for pickup tomorrow, refund after pickup.
    If not delivered → explain returns can only start after delivery, share current status + expected delivery, reassure them.

    Keep it short, chat-style, and human.
    """
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content.strip()


def refund_agent(order, user_email, user_prompt):
    prompt = f"""
    You are a supportive customer support assistant.

    Customer request: "{user_prompt.strip()}"

    Order details:
    - Order ID: {order['order_id']}
    - Status: {order['status']}
    - Expected Delivery: {order['expected_delivery']}
    - Refund Amount: ₹{order['amount']}
    - Carrier: {order['carrier']}
    - Tracking: {order['tracking_link']}
    - Email: {user_email}

    If delivered → confirm refund initiated, when money arrives, mention confirmation email sent.
    If not delivered → explain refund policy, current delivery status & tracking, reassure support.

    Write warm, friendly, chat-style response.
    """
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content.strip()


def general_support_agent(user_prompt):
    prompt = f"""
    You are a friendly and professional customer support assistant.

    Customer query: "{user_prompt.strip()}"

    Write a short, conversational response:
    - Acknowledge query
    - Confirm it has been received
    - Offer contact options if urgent
    - Keep it warm and human
    """
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content.strip()


# -----------------------------
# Streamlit UI
# -----------------------------
st.set_page_config(page_title="Customer Support Assistant", page_icon="📦", layout="centered")
st.title("🛍️ Customer Support Assistant")

# Step 1: Email input
user_email = st.text_input("Enter your email:", placeholder="you@example.com")

orders = None
if user_email:
    orders = mock_order_db.get(user_email)
    if orders:
        st.success(f"✅ {len(orders)} order(s) found for {user_email}")
    else:
        st.error("❌ No orders found for this email.")

# Step 2: Choose action
if orders:
    st.subheader("👉 Choose an Action")
    action = st.radio(
        "Select what you'd like help with:",
        ["Track Order", "Return Order", "Refund", "General Support"]
    )

    # Step 3: Select order (skip if general support)
    order = None
    if action != "General Support":
        st.subheader("📋 Select Your Order")
        order_options = [f"{o['order_id']} - ₹{o['amount']} ({o['status']})" for o in orders]
        selected_order = st.selectbox("Your Orders", order_options)
        order = orders[order_options.index(selected_order)]

    # Step 4: Query input
    st.subheader("💬 Enter Your Query")
    user_prompt = st.text_area("Your message:", placeholder="e.g., Where is my order?")

    # Step 5: Get Support
    if st.button("Get Support"):
        if not user_prompt.strip():
            st.warning("Please enter a query.")
        else:
            with st.spinner("Fetching support response..."):
                if action == "Track Order":
                    response = order_tracking_agent(order, user_prompt)
                elif action == "Return Order":
                    response = return_agent(order, user_email, user_prompt)
                elif action == "Refund":
                    response = refund_agent(order, user_email, user_prompt)
                elif action == "General Support":
                    response = general_support_agent(user_prompt)
                else:
                    response = "Sorry, I couldn't process your request."

            st.success(f"🧑‍💻 {action} Response:")
            st.info(response)
