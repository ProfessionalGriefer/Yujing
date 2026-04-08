from aqt import mw
from aqt.utils import tooltip


def get_config():
    # Extracts the root add-on folder name safely
    addon_name = __name__.split(".")[0]
    return mw.addonManager.getConfig(addon_name)


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
