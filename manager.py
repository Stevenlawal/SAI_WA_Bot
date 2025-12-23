import os
import threading
import time
from src.bot import WhatsAppBot

# Configuration
SESSION_DIR = "sessions"
HISTORY_DIR = "history"
SCAN_INTERVAL = 5  # Check faster for smoother removals

os.makedirs(SESSION_DIR, exist_ok=True)
os.makedirs(HISTORY_DIR, exist_ok=True)

# Track active sessions: { "david": ThreadObject }
active_sessions = {}

def run_bot(name):
    """Starts a single bot in its own thread."""
    print(f"   🚀 Launching Worker for: {name}")
    try:
        bot = WhatsAppBot(name)
        bot.start()
    except Exception as e:
        print(f"   ❌ Critical Crash for {name}: {e}")

def main():
    print("🚀 BOT MANAGER ACTIVE - WAITING FOR USERS...")
    
    try:
        while True:
            # --- 1. DETECT NEW USERS ---
            files = [f for f in os.listdir(SESSION_DIR) if f.endswith(".sqlite")]
            current_users = [f.replace(".sqlite", "") for f in files]
            
            for user in current_users:
                if user not in active_sessions:
                    print(f"\n✨ NEW USER DETECTED: {user}")
                    t = threading.Thread(target=run_bot, args=(user,))
                    t.daemon = True
                    t.start()
                    active_sessions[user] = t
            
            # --- 2. DETECT REMOVED USERS ---
            # Create a copy of keys to avoid runtime error during iteration
            active_names = list(active_sessions.keys())
            
            for user in active_names:
                if user not in current_users:
                    print(f"\n💀 DETECTED REMOVAL: {user}")
                    print(f"   Stopping thread tracking for {user}...")
                    # We can't easily kill the thread in Python, 
                    # but since the DB file is gone, the bot will crash/stop 
                    # on its next action, which is fine.
                    del active_sessions[user]

            time.sleep(SCAN_INTERVAL)
            
    except KeyboardInterrupt:
        print("\n🛑 Shutting down all bots...")

if __name__ == "__main__":
    from keep_alive import keep_alive
    keep_alive()
    main()