import json
import threading
import requests
from aqt import mw, gui_hooks
from aqt.utils import showInfo, showCritical
from aqt.qt import *

# --- Configuration Loader ---


def get_config():
    return mw.addonManager.getConfig(__name__)


# --- API Logic ---


def generate_sentence_task(note_id, target_word, prev_sentence, prev_translation):
    config = get_config()

    # Prepare the prompt
    prompt = config["prompt_template"].format(
        Target=target_word, **{"Generated Sentence": prev_sentence, "Generated Translation": prev_translation}
    )

    headers = {"Authorization": f"Bearer {config['api_key']}", "Content-Type": "application/json"}

    data = {
        "model": config.get("model", "gpt-3.5-turbo"),
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7,
    }

    try:
        response = requests.post(config["api_endpoint"], headers=headers, json=data, timeout=15)
        response.raise_for_status()
        result = response.json()["choices"][0]["message"]["content"].strip()

        # Expecting format: Sentence | Translation
        if "|" in result:
            new_s, new_t = result.split("|", 1)
            # Update the note in the main thread
            mw.taskman.run_on_main(lambda: update_note_fields(note_id, new_s.strip(), new_t.strip()))

    except Exception as e:
        print(f"Yujing Error: {str(e)}")


def update_note_fields(note_id, new_sentence, new_translation):
    note = mw.col.get_note(note_id)
    if "Generated Sentence" in note and "Generated Translation" in note:
        note["Generated Sentence"] = new_sentence
        note["Generated Translation"] = new_translation
        note.flush()
        # Visual feedback in the status bar if desired
        mw.taskman.run_on_main(lambda: mw.web.eval("console.log('Yujing: Card Updated');"))


# --- Hooks ---


def on_answer(reviewer, card, ease):
    # Check if ease is Good (3) or Easy (4)
    if ease < 3:
        return

    note = card.note()

    # Requirement: Fields must exist
    if "Generated Sentence" not in note or "Generated Translation" not in note:
        return

    # Determine the target word (using the configured Target field or first field)
    target_field = get_config().get("target_field", note.keys()[0])
    target_word = note.get(target_field, "Unknown Word")

    prev_s = note["Generated Sentence"]
    prev_t = note["Generated Translation"]

    # Run generation in background thread to prevent UI freezing
    thread = threading.Thread(target=generate_sentence_task, args=(note.id, target_word, prev_s, prev_t), daemon=True)
    thread.start()


gui_hooks.reviewer_did_answer_card.append(on_answer)

# --- Settings Menu ---


def on_settings():
    # Simple dialog to edit config via Anki's built-in JSON editor
    mw.addonManager.onConfiguration(mw)


# Add to Anki tools menu
action = QAction("Yujing Settings", mw)
qconnect(action.triggered, on_settings)
mw.form.menuTools.addAction(action)
