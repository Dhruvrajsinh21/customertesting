import requests
import json
import websocket
from faker import Faker
import threading
import time
import random
import streamlit as st

# Initialize Faker
fake = Faker()

# Define the API URLs
signup_url = "http://3.108.52.92//api/auth/customer/register/"
login_url = "http://3.108.52.92//customersignin/"
pickup_request_ws_url = "ws://3.108.52.92//ws/pickup_request/?token="

# Function to generate a 10-digit phone number
def generate_10_digit_phone_number():
    return f"{fake.random_number(digits=10, fix_len=True)}"

# Function to sign up the vendor
def signup_vendor():
    signup_payload = {
        "name": fake.name(),
        "email": fake.email(),
        "mobile_no": generate_10_digit_phone_number()
    }
    signup_response = requests.post(signup_url, json=signup_payload)
    
    if signup_response.status_code == 201:
        print("Signup successful:", signup_payload)
        return signup_payload["mobile_no"]
    else:
        print("Signup failed:", signup_response.text)
        return None

# Function to login the vendor and retrieve token
def login_vendor(mobile_no):
    login_payload = {
        "mobile_no": mobile_no
    }
    login_response = requests.post(login_url, json=login_payload)
    
    if login_response.status_code == 200:
        token = login_response.json().get("access")
        if token:
            print("Login successful. Token received.")
            return token
        else:
            print("Token not found in the login response.")
            return None
    else:
        print("Login failed:", login_response.text)
        return None

# Function to handle WebSocket events
def on_message(ws, message):
    print("Received message:", message)

def on_error(ws, error):
    print("Error occurred:", error)

def on_close(ws):
    print("WebSocket closed")

# Function to handle WebSocket connection and sending requests
def run_websocket(token, stop_event):
    ws_url = pickup_request_ws_url + token
    ws = websocket.WebSocketApp(
        ws_url,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close
    )

    def on_open(ws):
        # Send pickup requests with random latitude and longitude
        while not stop_event.is_set():
            pickup_payload = {
                "status": "Request Sent",
                "latitude": "{}".format(fake.latitude()),
                "longitude": "{}".format(fake.longitude())
            }
            ws.send(json.dumps(pickup_payload))
            print("Pickup request sent:", pickup_payload)
            time.sleep(random.randint(36, 60))  # Wait for a random time between 1 and 2 hours

    ws.on_open = on_open

    while not stop_event.is_set():
        try:
            # Set a ping interval to allow for responsiveness
            ws.run_forever(ping_interval=10)  # Sends ping every 10 seconds
        except Exception as e:
            print("WebSocket connection error:", e)
            break
        time.sleep(1)  # Allow some time before retrying the connection

    ws.close()  # Close the WebSocket when stopping

# Function to process the vendor and send pickup requests
def process_vendor(stop_event):
    mobile_no = signup_vendor()
    if not mobile_no:
        return  # Skip this vendor if signup fails

    token = login_vendor(mobile_no)
    if not token:
        return  # Skip this vendor if login fails

    run_websocket(token, stop_event)

# Streamlit app logic
def main():
    st.title("Vendor Registration Simulator")

    if 'vendor_thread' not in st.session_state:
        st.session_state['vendor_thread'] = None
        st.session_state['stop_event'] = None

    # Start Button
    if st.button("Start"):
        if st.session_state['vendor_thread'] is None:
            stop_event = threading.Event()
            st.session_state['stop_event'] = stop_event
            st.session_state['vendor_thread'] = threading.Thread(target=process_vendor, args=(stop_event,))
            st.session_state['vendor_thread'].start()
            st.write("Vendor registration started in the background.")

    # Stop Button
    if st.button("Stop"):
        if st.session_state['vendor_thread'] is not None:
            st.session_state['stop_event'].set()  # Signal to stop the thread
            st.session_state['vendor_thread'].join()  # Wait for the thread to finish
            st.session_state['vendor_thread'] = None  # Reset the process in session state
            st.write("Vendor registration stopped.")

if __name__ == "__main__":
    main()
