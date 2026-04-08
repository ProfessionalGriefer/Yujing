import os
import sys
import threading
import json
import urllib.request
import urllib.error

# --- Imports ---
from aqt import mw, gui_hooks
from aqt.utils import showInfo, showCritical, tooltip
from aqt.qt import *


def get_config():
    return mw.addonManager.getConfig(__name__)


# --- API Logic ---


def generate_sentence_task(note_id, target_word, prev_sentence, prev_translation):
    config = get_config()

    # Prepare the prompt
    prompt_template = config.get("prompt_template", "")
    placeholders = {
        "Target": target_word,
        "Generated Sentence": prev_sentence or "",
        "Generated Translation": prev_translation or "",
    }

    try:
        prompt = prompt_template.format(**placeholders)
    except Exception as e:
        prompt = f"Target: {target_word}\nPrevious: {prev_sentence}\n\nGenerate a new sentence."
        print(f"Yujing Prompt Format Error: {str(e)}")

    try:
        api_key = config.get("api_key", "")
        # Ensure we target the exact completion endpoint
        endpoint = config.get("api_endpoint", "https://api.openai.com/v1/chat/completions")
        if not endpoint.endswith("/chat/completions") and "api.openai.com" in endpoint:
            endpoint = endpoint.rstrip("/") + "/chat/completions"

        # Instead of Pydantic, we pass the JSON Schema directly to OpenAI
        # This achieves the exact same strict structured output.
        payload = {
            "model": config.get("model", "gpt-4o-mini"),
            "messages": [{"role": "user", "content": prompt}],
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": "GeneratedResponse",
                    "strict": True,
                    "schema": {
                        "type": "object",
                        "properties": {"sentence": {"type": "string"}, "translation": {"type": "string"}},
                        "required": ["sentence", "translation"],
                        "additionalProperties": False,
                    },
                },
            },
        }

        headers = {"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}

        req = urllib.request.Request(
            url=endpoint, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST"
        )

        # Execute HTTP Request via standard library
        with urllib.request.urlopen(req, timeout=15) as response:
            response_body = response.read().decode("utf-8")
            response_json = json.loads(response_body)

        # Extract the content
        content = response_json["choices"][0]["message"]["content"]

        if content:
            # Parse the strict JSON returned by the model
            parsed = json.loads(content)
            new_s = parsed.get("sentence", "").strip()
            new_t = parsed.get("translation", "").strip()

            # Update the note in the main thread
            mw.taskman.run_on_main(lambda: update_note_fields(note_id, new_s, new_t))
        else:
            raise ValueError("Failed to retrieve generated content from API response.")

    except Exception as e:
        error_msg = str(e)
        # Capture specific API error bodies if HTTP request fails
        if isinstance(e, urllib.error.HTTPError):
            try:
                error_body = e.read().decode("utf-8")
                error_msg += f"\nDetails: {error_body}"
            except Exception:
                pass

        print(f"Yujing Error: {error_msg}")
        if config.get("report_errors"):
            mw.taskman.run_on_main(lambda: showCritical(f"Yujing Background Generation Failed:\n\n{error_msg}"))


def update_note_fields(note_id, new_sentence, new_translation):
    try:
        note = mw.col.get_note(note_id)
        if "Generated Sentence" in note and "Generated Translation" in note:
            note["Generated Sentence"] = new_sentence
            note["Generated Translation"] = new_translation
            mw.col.update_note(note)
            # Visual feedback in the status bar
            tooltip("Yujing: New sentence generated", period=2000)
    except Exception as e:
        print(f"Yujing Update Error: {str(e)}")


# --- Hooks ---


def on_answer(reviewer, card, ease):
    # Check if ease is Good (3) or Easy (4)
    # 1=Again, 2=Hard, 3=Good, 4=Easy
    if ease < 3:
        return

    note = card.note()

    # Requirement: Fields must exist
    if "Generated Sentence" not in note or "Generated Translation" not in note:
        return

    config = get_config()

    # Determine the target word (using the configured Target field or first field)
    target_field = config.get("target_field", "")

    # Check if the configured field actually exists on this note
    if not target_field or target_field not in note:
        # Fallback to the first field on the card
        target_field = note.keys()[0]

    target_word = note[target_field] if target_field in note else "Unknown Word"

    prev_s = note["Generated Sentence"]
    prev_t = note["Generated Translation"]

    # Run generation in background thread to prevent UI freezing
    thread = threading.Thread(target=generate_sentence_task, args=(note.id, target_word, prev_s, prev_t), daemon=True)
    thread.start()


gui_hooks.reviewer_did_answer_card.append(on_answer)

# --- Settings Menu ---


class YujingSettingsDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle("Yujing Settings")
        self.setMinimumWidth(500)
        self.setup_ui()
        self.load_config()

    def setup_ui(self):
        layout = QVBoxLayout()
        form = QFormLayout()

        self.api_endpoint = QLineEdit()
        self.api_key = QLineEdit()
        self.api_key.setEchoMode(QLineEdit.EchoMode.Password)
        self.model = QLineEdit()
        self.target_field = QLineEdit()
        self.report_errors = QCheckBox("Report Errors (popups)")

        self.prompt_template = QTextEdit()
        self.prompt_template.setAcceptRichText(False)
        self.prompt_template.setMinimumHeight(150)

        form.addRow("API Endpoint:", self.api_endpoint)
        form.addRow("API Key:", self.api_key)
        form.addRow("Model:", self.model)
        form.addRow("Target Word Field:", self.target_field)
        form.addRow("", self.report_errors)

        layout.addLayout(form)
        layout.addWidget(
            QLabel("Prompt Template (placeholders: {Target}, {Generated Sentence}, {Generated Translation}):")
        )
        layout.addWidget(self.prompt_template)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.setLayout(layout)

    def load_config(self):
        config = get_config()
        self.api_endpoint.setText(config.get("api_endpoint", "https://api.openai.com/v1/chat/completions"))
        self.api_key.setText(config.get("api_key", ""))
        self.model.setText(config.get("model", "gpt-3.5-turbo"))
        self.target_field.setText(config.get("target_field", "Word"))
        self.report_errors.setChecked(config.get("report_errors", False))
        self.prompt_template.setPlainText(config.get("prompt_template", ""))

    def get_new_config(self):
        return {
            "api_endpoint": self.api_endpoint.text(),
            "api_key": self.api_key.text(),
            "model": self.model.text(),
            "target_field": self.target_field.text(),
            "report_errors": self.report_errors.isChecked(),
            "prompt_template": self.prompt_template.toPlainText(),
        }


def on_settings():
    dialog = YujingSettingsDialog(mw)
    if dialog.exec():
        new_config = dialog.get_new_config()
        mw.addonManager.writeConfig(__name__, new_config)
        showInfo("Settings saved successfully.")


# Add to Anki tools menu
action = QAction("Yujing Settings", mw)
qconnect(action.triggered, on_settings)
mw.form.menuTools.addAction(action)

