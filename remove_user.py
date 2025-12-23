import os
import time

SESSION_DIR = "sessions"
HISTORY_DIR = "history"

def remove_user():
    print("🔥 USER REMOVAL TOOL 🔥")
    
    # List active users
    if not os.path.exists(SESSION_DIR):
        print("No users found.")
        return

    files = [f for f in os.listdir(SESSION_DIR) if f.endswith(".sqlite")]
    if not files:
        print("No users found.")
        return

    print("Active Users:")
    for i, f in enumerate(files):
        print(f"{i+1}. {f.replace('.sqlite', '')}")
    
    try:
        choice_input = input("\nSelect number to remove: ")
        if not choice_input.isdigit(): return

        choice = int(choice_input) - 1
        if choice < 0 or choice >= len(files):
            print("Invalid selection.")
            return
            
        target_name = files[choice].replace(".sqlite", "")
        confirm = input(f"⚠️ Are you sure you want to DELETE {target_name}? (yes/no): ")
        
        if confirm.lower() == "yes":
            # 1. Delete Session (Stops the bot from connecting)
            db_path = f"{SESSION_DIR}/{target_name}.sqlite"
            if os.path.exists(db_path):
                os.remove(db_path)
                print(f"   ✅ Deleted Session: {db_path}")
            
            # 2. Delete History (Cleans up disk)
            hist_path = f"{HISTORY_DIR}/{target_name}.json"
            if os.path.exists(hist_path):
                os.remove(hist_path)
                print(f"   ✅ Deleted History: {hist_path}")
                
            print(f"\n💀 User {target_name} has been removed.")
            print("👉 The Manager will detect this and stop their thread automatically.")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    remove_user()