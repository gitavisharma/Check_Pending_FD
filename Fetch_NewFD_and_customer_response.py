import requests
from datetime import datetime, timedelta
import pytz
import tkinter as tk
from tkinter import messagebox, scrolledtext

# Function to fetch Freshdesk tickets

def fetch_tickets():
    domain = domain_entry.get()
    api_key = api_key_entry.get()
    hours = int(hours_entry.get())
    
    if not domain or not api_key:
        messagebox.showerror("Error", "Please enter Freshdesk domain and API key")
        return

    try:
        headers = {"Content-Type": "application/json"}
        ist = pytz.timezone('Asia/Kolkata')
        current_time_ist = datetime.now(ist)
        time_threshold_ist = current_time_ist - timedelta(hours=hours)
        time_threshold_utc = time_threshold_ist.astimezone(pytz.utc)
        formatted_time = time_threshold_utc.strftime('%Y-%m-%dT%H:%M:%SZ')

        all_tickets = []
        page = 1
        
        # Fetch all tickets with pagination
        while True:
            url = f"https://{domain}/api/v2/tickets?updated_since={formatted_time}&per_page=100&page={page}"
            response = requests.get(url, auth=(api_key, "X"), headers=headers)
            
            if response.status_code != 200:
                messagebox.showerror("Error", f"Failed to fetch tickets: {response.status_code} {response.text}")
                return
            
            tickets = response.json()
            if not tickets:
                break

            all_tickets.extend(tickets)
            page += 1

        # Separate new tickets and customer responded tickets
        new_tickets = []
        customer_responses = []
        
        # Process each ticket
        for ticket in all_tickets:
            created_time = ticket.get("created_at")
            ticket_id = ticket['id']
            subject = ticket['subject']
            status = ticket.get("status")

            # Skip closed tickets
            if status == 5:
                continue

            # Fetch ticket conversations
            conversations_url = f"https://{domain}/api/v2/tickets/{ticket_id}/conversations"
            conv_response = requests.get(conversations_url, auth=(api_key, "X"), headers=headers)

            if conv_response.status_code == 200:
                conversations = conv_response.json()
                last_response = conversations[-1] if conversations else None
                
                # Identify new tickets (no replies yet)
                if created_time and created_time > formatted_time and not conversations:
                    new_tickets.append(f"Ticket ID: {ticket_id}, Subject: {subject}")
                
                # Identify customer responded tickets (last response is from customer)
                if last_response and last_response.get("incoming", False) and last_response["created_at"] > formatted_time:
                    if ticket_id not in [t.split(':')[1].strip() for t in new_tickets]:
                        customer_responses.append(f"Ticket ID: {ticket_id}, Subject: {subject}")

        # Display results in the GUI
        result_text.config(state=tk.NORMAL)
        result_text.delete(1.0, tk.END)

        if new_tickets:
            result_text.insert(tk.END, "\n\n**New Tickets:**\n" + "\n".join(new_tickets))
        else:
            result_text.insert(tk.END, "\n\n**New Tickets:**\nNo new tickets found.")

        if customer_responses:
            result_text.insert(tk.END, "\n\n**Customer Responses:**\n" + "\n".join(customer_responses))
        else:
            result_text.insert(tk.END, "\n\n**Customer Responses:**\nNo customer responses found.")

        result_text.config(state=tk.DISABLED)

    except Exception as e:
        messagebox.showerror("Error", str(e))

# Create the GUI window
window = tk.Tk()
window.title("Freshdesk Ticket Fetcher")
window.geometry("700x600")
window.configure(bg='#f0f0f0')

# Input fields
tk.Label(window, text="Freshdesk Domain:", bg='#f0f0f0', font=('Arial', 12, 'bold')).pack(pady=5)
domain_entry = tk.Entry(window, width=40, font=('Arial', 12))
domain_entry.pack(pady=5)

tk.Label(window, text="API Key:", bg='#f0f0f0', font=('Arial', 12, 'bold')).pack(pady=5)
api_key_entry = tk.Entry(window, width=40, show="*", font=('Arial', 12))
api_key_entry.pack(pady=5)

# Hours look back
tk.Label(window, text="Hours (Look back):", bg='#f0f0f0', font=('Arial', 12, 'bold')).pack(pady=5)
hours_entry = tk.Entry(window, width=10, font=('Arial', 12))
hours_entry.pack(pady=5)
hours_entry.insert(0, "3")

# Fetch button
tk.Button(window, text="Fetch Tickets", command=fetch_tickets, font=('Arial', 12, 'bold'), bg='#4CAF50', fg='white').pack(pady=10)

# Results area
result_text = scrolledtext.ScrolledText(window, width=80, height=25, state=tk.DISABLED, font=('Courier', 10))
result_text.pack(pady=10)

window.mainloop()
