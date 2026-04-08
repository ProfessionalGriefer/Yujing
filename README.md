# Yujing (语境)

- Anki Extension
- Extension should only work on cards that have the fields `Generated Sentence` and `Generated Translation`.
- Provide OpenAPI compatible endpoint + API Key in the settings menu.
- You can also edit the prompt template in the settings menu, but it should contain `{Generated Sentence}` and `{Generated Translation}` as placeholders for the generated sentence and translation respectively.
- `{Generated Sentence}` and `{Generated Translation}` is empty for new cards.
- When the user enters *Again* or *Hard*, nothing happens.
- When the user enters *Good* or *Easy*, the extension will generate a new sentence and update the card's fields `Generated Sentence` and `Generated Translation` with the new values.
- The sentence generation should happen in the background, so that the user can continue reviewing without waiting for the generation to complete.
- A `i + 1` system would be best. That means that the word that the user should know all context words. The default prompt should mention that.

