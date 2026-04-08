import threading
from aqt import mw, gui_hooks
from aqt.qt import QAction, qconnect

# Local imports from our newly created files
from .utils import get_config
from .api import generate_sentence_task
from .settings import on_settings


def on_answer(reviewer, card, ease):
    if ease < 3:
        return

    note = card.note()

    if "Generated Sentence" not in note or "Generated Translation" not in note:
        return

    config = get_config()
    target_field = config.get("target_field", "")

    if not target_field or target_field not in note:
        target_field = note.keys()[0]

    target_word = note[target_field] if target_field in note else "Unknown Word"
    prev_s = note["Generated Sentence"]
    prev_t = note["Generated Translation"]

    thread = threading.Thread(target=generate_sentence_task, args=(note.id, target_word, prev_s, prev_t), daemon=True)
    thread.start()


# Register the hook
gui_hooks.reviewer_did_answer_card.append(on_answer)

# Add to Anki tools menu
action = QAction("Yujing Settings", mw)
qconnect(action.triggered, on_settings)
mw.form.menuTools.addAction(action)
