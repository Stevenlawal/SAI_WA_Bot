import os
import time
import json
import traceback
import copy
from threading import Thread
from neonize.client import NewClient
from neonize.events import ConnectedEv, MessageEv
from neonize.proto.waE2E.WAWebProtobufsE2E_pb2 import Message, ReactionMessage
from .config import CMD_PREFIX
from .features import build_black_status_message

TWENTY_FOUR_HOURS = 86400

class WhatsAppBot:
    def __init__(self, session_name):
        self.session_name = session_name

        # 1. Independent Paths
        self.db_path = f"sessions/{session_name}.sqlite"
        self.history_path = f"history/{session_name}.json"

        print(f"   👤 Initializing User: {session_name}")

        # 2. Connect to THIS user's database
        self.client = NewClient(self.db_path)
        self.status_history = self.load_and_clean_history()
        self.register_events()

    def load_and_clean_history(self):
        """Loads history specific to THIS user."""
        if not os.path.exists(self.history_path): return []
        try:
            with open(self.history_path, "r") as f:
                data = json.load(f)

            # Clean expired
            now = time.time()
            clean = [x for x in data if (now - x['timestamp']) < TWENTY_FOUR_HOURS]

            if len(clean) != len(data):
                self.save_history(clean) # Save immediately if cleaned
            return clean
        except: return []

    def save_history(self, data=None):
        """Saves history specific to THIS user."""
        if data is None: data = self.status_history
        try:
            with open(self.history_path, "w") as f:
                json.dump(data, f)
        except Exception as e:
            print(f"⚠️ Save failed for {self.session_name}: {e}")

    def register_events(self):
        @self.client.event(ConnectedEv)
        def on_connect(client, event):
            print(f"   ✅ {self.session_name} is Online!")

        @self.client.event(MessageEv)
        def on_message(client, message: MessageEv):
            try:
                if not message.Info: return

                # Check if message is from the user themselves
                is_from_me = getattr(message.Info, 'IsFromMe', False)
                sender = message.Info.MessageSource.Sender.User

                # We only want the bot to react to the owner of this specific session
                my_jid = client.get_me().JID.User
                if sender != my_jid and not is_from_me:
                    return

                text = self.extract_text(message.Message)
                if not text: return

                # --- COMMANDS ---
                if text.startswith(CMD_PREFIX + "status "):
                    self.post_status(client, text, message)

                elif text == CMD_PREFIX + "list":
                    self.list_statuses(client, message)

                elif text.startswith(CMD_PREFIX + "delete"):
                    self.smart_delete(client, text, message)

                elif text == CMD_PREFIX + "stopbot":
                    self.unlink_user(client, message)

            except Exception:
                traceback.print_exc()

    def post_status(self, client, text, msg_event):
        content = text[len(CMD_PREFIX + "status "):]
        try:
            # Broadcast
            status_jid = client.get_me().JID
            status_jid.User = "status"; status_jid.Server = "broadcast"; status_jid.Device = 0

            msg = build_black_status_message(content)
            resp = client.send_message(status_jid, msg)

            new_id = resp.ID if hasattr(resp, 'ID') else resp.id

            # Add to history
            self.status_history.append({
                "id": new_id,
                "text": content[:20] + "...", # Save snippet for the list
                "timestamp": time.time()
            })
            self.save_history()

            # Send Receipt
            count = len(self.status_history)
            client.send_message(msg_event.Info.Chat, Message(conversation=f"✅ *Posted!* (Status #{count})"))

        except Exception as e:
            print(f"Error {self.session_name}: {e}")

    def list_statuses(self, client, msg_event):
        # Refresh history
        self.status_history = self.load_and_clean_history()

        if not self.status_history:
            client.send_message(msg_event.Info.Chat, Message(conversation="📭 You have no active statuses."))
            return

        # Build the Smart List
        msg = "📋 *Active Statuses:*\n"
        for index, item in enumerate(self.status_history):
            # Users count from 1, Python counts from 0
            msg += f"{index + 1}. {item['text']}\n"

        msg += "\nTo delete, type: *.delete <number>* (e.g., .delete 1)"
        client.send_message(msg_event.Info.Chat, Message(conversation=msg))

    def smart_delete(self, client, text, msg_event):
        try:
            parts = text.split()
            if len(parts) < 2:
                client.send_message(msg_event.Info.Chat, Message(conversation="⚠️ Please specify a number. Example: .delete 1"))
                return

            # User inputs "1", we need index "0"
            target_index = int(parts[1]) - 1

            self.status_history = self.load_and_clean_history()

            if target_index < 0 or target_index >= len(self.status_history):
                client.send_message(msg_event.Info.Chat, Message(conversation="❌ Invalid number. Check .list"))
                return

            # Get ID and Remove from list
            target_item = self.status_history.pop(target_index)
            self.save_history()

            # Perform Delete
            status_jid = client.get_me().JID
            status_jid.User = "status"; status_jid.Server = "broadcast"; status_jid.Device = 0
            me_jid = client.get_me().JID

            client.revoke_message(status_jid, me_jid, target_item['id'])

            client.send_message(msg_event.Info.Chat, Message(conversation=f"🗑️ Deleted Status #{parts[1]}"))

        except ValueError:
            client.send_message(msg_event.Info.Chat, Message(conversation="⚠️ Please enter a valid number."))
        except Exception as e:
            print(e)

    def unlink_user(self, client, msg_event):
        """Allows the user to disconnect nicely."""
        client.send_message(msg_event.Info.Chat, Message(conversation="👋 Disconnecting from bot server..."))
        client.logout()
        print(f"🛑 {self.session_name} has unlinked.")

    def extract_text(self, msg_obj):
        if not msg_obj: return ""
        
        def get_content(m):
            if hasattr(m, 'conversation') and m.conversation: return m.conversation
            if hasattr(m, 'extendedTextMessage') and m.extendedTextMessage: return m.extendedTextMessage.text
            if hasattr(m, 'imageMessage') and m.imageMessage: return m.imageMessage.caption
            return None

        text = get_content(msg_obj)
        if text: return text
        
        # Check inside specific message types (Replies, Ephemeral, etc)
        if hasattr(msg_obj, 'deviceSentMessage') and msg_obj.deviceSentMessage:
            return get_content(msg_obj.deviceSentMessage.message)
        if hasattr(msg_obj, 'ephemeralMessage') and msg_obj.ephemeralMessage:
            return get_content(msg_obj.ephemeralMessage.message)
        if hasattr(msg_obj, 'viewOnceMessage') and msg_obj.viewOnceMessage:
            return get_content(msg_obj.viewOnceMessage.message)
            
        return ""

    def start(self):
        # We run connect() but we catch errors so one user crashing doesn't kill the server
        try:
            self.client.connect()
        except Exception as e:
            print(f"❌ User {self.session_name} crashed: {e}")