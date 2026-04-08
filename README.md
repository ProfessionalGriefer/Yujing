# Yujing (语境)
### AI-Powered Example Sentence and Audio Generator for Anki

Yujing (语境) is an Anki add-on designed to provide dynamic context for language learners. It utilizes the OpenAI API to generate new example sentences and corresponding audio for specific cards during the review process. This prevents the "stagnation" of seeing the same example sentence repeatedly, ensuring that each time a word is reviewed, it is presented in a fresh context.

---

## Core Features

- **Background Generation**: Sentence and audio generation occurs in a background thread. This allows the user to continue their review session without waiting for the API response.
- **i+1 Principle**: The default prompt instructs the AI to generate sentences using simple vocabulary, ensuring that the target word is the only unfamiliar element in the sentence.
- **Text-to-Speech (TTS)**: The add-on uses OpenAI’s `audio/speech` endpoint to generate high-quality MP3 files, which are saved to the Anki media folder and linked to the card.
- **Automatic Highlighting**: The add-on identifies the target word within the new sentence and applies `<b>` tags automatically for visual clarity.
- **Configurable Settings**: Users can modify the API endpoint, model (e.g., GPT-4o-mini), prompt template, and TTS voice (e.g., Alloy, Nova) via the settings menu.

## Technical Requirements

### Required Fields
For this add-on to function, the Note Type being used must include the following three fields:
1. `Generated Sentence`
2. `Generated Translation`
3. `Generated Audio`

### API Access
An **OpenAI API Key** with a positive account balance is required. Users are responsible for their own API usage costs.

---

## Card Template Integration

To display the generated content on your cards with a fallback to your original deck's content, add the following logic to your **Back Template**:

```html
{{#Generated Sentence}}
  <div class="ai-sentence">{{Generated Sentence}}</div>
  <div class="ai-translation">{{Generated Translation}}</div>
  <hr />
{{/Generated Sentence}}

{{^Generated Sentence}}
  <div class="original-sentence">{{Sentence}}</div>
  <div class="original-translation">{{Translation}}</div>
  <hr />
{{/Generated Sentence}}

<div class="media">
  {{#Generated Audio}}
    {{Generated Audio}}
  {{/Generated Audio}}
  {{^Generated Audio}}
    {{SentenceAudio}}
  {{/Generated Audio}}
</div>
