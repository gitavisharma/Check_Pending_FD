import requests
from datetime import datetime, timedelta
import pytz

# Freshdesk API details
FRESHDESK_DOMAIN = "orosoft.freshdesk.com"  # Replace with your Freshdesk domain
API_KEY = "qtThGRKUwIVd54wT65NB"  # Replace with your actual API Key
HEADERS = {"Content-Type": "application/json"}

# Set timezone to IST and calculate time threshold
ist = pytz.timezone('Asia/Kolkata')
current_time_ist = datetime.now(ist)
time_threshold_ist = current_time_ist - timedelta(hours=36)
time_threshold_utc = time_threshold_ist.astimezone(pytz.utc)
formatted_time = time_threshold_utc.strftime('%Y-%m-%dT%H:%M:%SZ')

print(f"✅ Checking tickets updated since: {formatted_time}")

# Fetch all tickets updated in the last 3 hours (handle pagination)
all_tickets = []
page = 1
while True:
    url = f"https://{FRESHDESK_DOMAIN}/api/v2/tickets?updated_since={formatted_time}&per_page=100&page={page}"
    response = requests.get(url, auth=(API_KEY, "X"), headers=HEADERS)
    
    if response.status_code != 200:
        print("❌ Failed to fetch tickets:", response.status_code, response.text)
        break
    
    tickets = response.json()
    if not tickets:
        break

    all_tickets.extend(tickets)
    page += 1

print(f"ℹ️ Total tickets fetched: {len(all_tickets)}")

# Filter tickets where the last response was from the customer and ticket is not closed
filtered_tickets = []

for ticket in all_tickets:
    # Skip closed tickets
    if ticket.get("status") == 5:
        continue
    
    # Fetch conversations for each ticket
    conversations_url = f"https://{FRESHDESK_DOMAIN}/api/v2/tickets/{ticket['id']}/conversations"
    conv_response = requests.get(conversations_url, auth=(API_KEY, "X"), headers=HEADERS)
    
    if conv_response.status_code == 200:
        conversations = conv_response.json()
        if not conversations:
            continue
        
        last_response = conversations[-1]
        # Check if the last response was from the customer
        if last_response.get("incoming", False):
            last_customer_response = last_response["created_at"]
            if last_customer_response > formatted_time:
                filtered_tickets.append({
                    "id": ticket['id'],
                    "subject": ticket['subject']
                })

# Print results
print("✅ Tickets where Customer responded within the last 3 hours:")
if filtered_tickets:
    for t in filtered_tickets:
        print(f"📌 Ticket ID: {t['id']}, Subject: {t['subject']}")
else:
    print("❌ No tickets found with customer responses in the given time range.")
