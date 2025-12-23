import os
import signal
from neonize.client import NewClient
from neonize.events import ConnectedEv, PairStatusEv
from neonize.utils import log

SESSION_DIR = "sessions"
os.makedirs(SESSION_DIR, exist_ok=True)

# Global flag to exit cleanly
is_linked = False

def add_new_friend():
    name = input("Enter a name for this user (e.g., 'david'): ").strip()
    if not name: return
    
    db_path = f"{SESSION_DIR}/{name}.sqlite"
    
    if os.path.exists(db_path):
        print("⚠️ This user already exists!")
        return

    phone = input("Enter their phone number (e.g., 2348012345678): ").strip()
    
    print(f"\n⚡ Initializing Client for {name}...")
    client = NewClient(db_path)

    @client.event(ConnectedEv)
    def on_connect(c, e):
        print("✅ Connection Established. requesting code...")

    @client.event(PairStatusEv)
    def on_pair_status(c, message: PairStatusEv):
        global is_linked
        print(f"🔗 Logged in as: {message.ID.User}")
        is_linked = True
        client.disconnect()

    # We need to connect first, then request the code
    # Neonize usually handles the pair_phone call internally if we set it up right
    # But since this is a specific flow, we define a custom runner:
    
    try:
        # 1. Start the connection in non-blocking mode if possible, 
        #    or just use the provided pair_phone method if available.
        #    NOTE: In most versions of this library, you call pair_phone() 
        #    instead of just connect() to trigger this mode.
        
        print(f"👉 Link Code for {phone}:")
        
        # This will print the code to your terminal
        code = client.pair_phone(phone, show_notification=True, client_display_name="SaaS Bot", client_type=1)
        print(f"\n   {code}\n")
        print("Enter this code on the user's phone (Linked Devices > Link with phone number).")
        
        # Now we wait for them to enter it
        client.connect()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        # If pairing fails, clean up the bad file
        if os.path.exists(db_path) and not is_linked:
            os.remove(db_path)

if __name__ == "__main__":
    add_new_friend()