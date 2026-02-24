import json
import os
import threading
import customtkinter as ctk
import agent

APP_NAME = "my-first-agent"
CONFIG_DIR = os.path.join(os.getenv("APPDATA", os.path.expanduser("~")), APP_NAME)
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")


# ---------------------------------------------------------------------------
# API key persistence
# ---------------------------------------------------------------------------

def load_api_key() -> str | None:
    try:
        with open(CONFIG_FILE, "r") as f:
            return json.load(f).get("api_key")
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def save_api_key(api_key: str):
    os.makedirs(CONFIG_DIR, exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        json.dump({"api_key": api_key}, f)


# ---------------------------------------------------------------------------
# API key dialog
# ---------------------------------------------------------------------------

class ApiKeyDialog(ctk.CTkToplevel):
    def __init__(self, parent, existing_key: str = ""):
        super().__init__(parent)
        self.title("API Key")
        self.geometry("460x170")
        self.resizable(False, False)
        self.grab_set()

        self.result = None

        ctk.CTkLabel(self, text="Enter your OpenAI API key:").pack(pady=(18, 6))
        self.entry = ctk.CTkEntry(self, width=400, show="*")
        self.entry.pack(pady=4)
        if existing_key:
            self.entry.insert(0, existing_key)

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(pady=12)
        ctk.CTkButton(btn_frame, text="Save", width=100, command=self._save).pack(side="left", padx=8)
        ctk.CTkButton(btn_frame, text="Cancel", width=100, fg_color="gray", command=self.destroy).pack(side="left", padx=8)

        self.entry.focus_set()
        self.bind("<Return>", lambda e: self._save())

    def _save(self):
        key = self.entry.get().strip()
        if key:
            self.result = key
            self.destroy()


# ---------------------------------------------------------------------------
# Main chat window
# ---------------------------------------------------------------------------

class ChatApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title(APP_NAME)
        self.geometry("700x520")
        self.minsize(480, 360)

        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")

        self._build_ui()
        self._init_agent()

    # -- UI ------------------------------------------------------------------

    def _build_ui(self):
        top_bar = ctk.CTkFrame(self, fg_color="transparent")
        top_bar.pack(fill="x", padx=12, pady=(10, 0))

        ctk.CTkLabel(top_bar, text=APP_NAME, font=ctk.CTkFont(size=16, weight="bold")).pack(side="left")
        ctk.CTkButton(top_bar, text="Settings", width=80, command=self._open_settings).pack(side="right")

        self.chat_box = ctk.CTkTextbox(self, state="disabled", wrap="word", font=ctk.CTkFont(size=13))
        self.chat_box.pack(fill="both", expand=True, padx=12, pady=8)

        bottom = ctk.CTkFrame(self, fg_color="transparent")
        bottom.pack(fill="x", padx=12, pady=(0, 10))

        self.input_entry = ctk.CTkEntry(bottom, placeholder_text="Type a message...", font=ctk.CTkFont(size=13))
        self.input_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.input_entry.bind("<Return>", lambda e: self._send())

        self.send_btn = ctk.CTkButton(bottom, text="Send", width=70, command=self._send)
        self.send_btn.pack(side="right")

        self.status_label = ctk.CTkLabel(self, text="", font=ctk.CTkFont(size=11))
        self.status_label.pack(pady=(0, 4))

    # -- Agent init ----------------------------------------------------------

    def _init_agent(self):
        api_key = load_api_key()
        if not api_key:
            self.after(200, self._prompt_for_key)
        else:
            agent.init(api_key)

    def _prompt_for_key(self):
        dialog = ApiKeyDialog(self)
        self.wait_window(dialog)
        if dialog.result:
            save_api_key(dialog.result)
            agent.init(dialog.result)
        else:
            self._append_message("System", "No API key provided. Use Settings to add one.")

    # -- Settings ------------------------------------------------------------

    def _open_settings(self):
        existing = load_api_key() or ""
        dialog = ApiKeyDialog(self, existing_key=existing)
        self.wait_window(dialog)
        if dialog.result:
            save_api_key(dialog.result)
            agent.init(dialog.result)
            self._append_message("System", "API key updated.")

    # -- Chat ----------------------------------------------------------------

    def _append_message(self, role: str, text: str):
        self.chat_box.configure(state="normal")
        self.chat_box.insert("end", f"{role}: {text}\n\n")
        self.chat_box.configure(state="disabled")
        self.chat_box.see("end")

    def _send(self):
        text = self.input_entry.get().strip()
        if not text or agent.client is None:
            return
        self.input_entry.delete(0, "end")
        self._append_message("You", text)
        self._set_busy(True)
        threading.Thread(target=self._run_agent, args=(text,), daemon=True).start()

    def _run_agent(self, text: str):
        try:
            result = agent.process(text)
        except Exception as exc:
            result = f"[Error] {exc}"
        self.after(0, self._on_response, result)

    def _on_response(self, result: str):
        self._append_message("Agent", result)
        self._set_busy(False)

    def _set_busy(self, busy: bool):
        if busy:
            self.status_label.configure(text="Thinking...")
            self.send_btn.configure(state="disabled")
        else:
            self.status_label.configure(text="")
            self.send_btn.configure(state="normal")


if __name__ == "__main__":
    ChatApp().mainloop()
