import json
import urllib.request
import urllib.error
import re
import time
from aqt import mw
from aqt.utils import showCritical

# Import from our new utils file
from .utils import get_config, update_note_fields


def _save_media_and_update(note_id, new_s, new_t, audio_filename, audio_data):
    """Helper to safely write media and update note on the main thread."""
    if audio_filename and audio_data:
        mw.col.media.write_data(audio_filename, audio_data)
    update_note_fields(note_id, new_s, new_t, audio_filename)


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
        endpoint = config.get("api_endpoint", "https://api.openai.com/v1/chat/completions")
        if not endpoint.endswith("/chat/completions") and "api.openai.com" in endpoint:
            endpoint = endpoint.rstrip("/") + "/chat/completions"

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

        # 1. GENERATE TEXT
        req = urllib.request.Request(
            url=endpoint, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST"
        )

        with urllib.request.urlopen(req, timeout=15) as response:
            response_body = response.read().decode("utf-8")
            response_json = json.loads(response_body)

        content = response_json["choices"][0]["message"]["content"]

        if content:
            parsed = json.loads(content)
            clean_s = parsed.get("sentence", "").strip()
            new_t = parsed.get("translation", "").strip()

            # Regex Wrapping Logic for text field
            pattern = re.compile(re.escape(target_word), re.IGNORECASE)
            new_s_html = pattern.sub(r"<b>\g<0></b>", clean_s)

            # 2. GENERATE AUDIO
            audio_filename = None
            audio_data = None
            if config.get("generate_audio", False):
                try:
                    tts_endpoint = "https://api.openai.com/v1/audio/speech"
                    tts_payload = {
                        "model": "tts-1",
                        "voice": config.get("audio_voice", "alloy"),
                        "input": clean_s,  # Send the clean string, not the <b> wrapped HTML
                    }
                    tts_req = urllib.request.Request(
                        url=tts_endpoint,
                        data=json.dumps(tts_payload).encode("utf-8"),
                        headers=headers,  # Reuse authorization headers
                        method="POST",
                    )
                    with urllib.request.urlopen(tts_req, timeout=15) as tts_res:
                        audio_data = tts_res.read()

                    # Sanitize target word to prevent file system errors (keeps alphanumeric & characters, replaces rest with _)
                    safe_target_word = re.sub(r"[^\w\-]", "_", target_word)

                    # Create a unique filename for Anki's media folder including the target word
                    audio_filename = f"yujing_{safe_target_word}_{note_id}_{int(time.time())}.mp3"
                except Exception as audio_e:
                    print(f"Yujing Audio Error: {str(audio_e)}")

            # Update the note in the main thread
            mw.taskman.run_on_main(
                lambda: _save_media_and_update(note_id, new_s_html, new_t, audio_filename, audio_data)
            )
        else:
            raise ValueError("Failed to retrieve generated content from API response.")

    except Exception as e:
        error_msg = str(e)
        if isinstance(e, urllib.error.HTTPError):
            try:
                error_body = e.read().decode("utf-8")
                error_msg += f"\nDetails: {error_body}"
            except Exception:
                pass

        print(f"Yujing Error: {error_msg}")
        mw.taskman.run_on_main(lambda: showCritical(f"Yujing Background Generation Failed:\n\n{error_msg}"))
