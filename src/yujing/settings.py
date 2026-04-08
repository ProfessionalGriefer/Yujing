from aqt import mw
from aqt.qt import *
from aqt.utils import showInfo

# Import config helper
from .utils import get_config


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

        # Audio UI Elements
        self.generate_audio = QCheckBox("Generate Audio (TTS)")
        self.audio_voice = QComboBox()
        self.audio_voice.addItems(["alloy", "echo", "fable", "onyx", "nova", "shimmer"])

        self.prompt_template = QTextEdit()
        self.prompt_template.setAcceptRichText(False)
        self.prompt_template.setMinimumHeight(150)

        form.addRow("API Endpoint:", self.api_endpoint)
        form.addRow("API Key:", self.api_key)
        form.addRow("Model:", self.model)
        form.addRow("Target Word Field:", self.target_field)
        form.addRow("", self.generate_audio)
        form.addRow("Audio Voice:", self.audio_voice)

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

        # Load Audio config
        self.generate_audio.setChecked(config.get("generate_audio", True))
        voice = config.get("audio_voice", "alloy")
        index = self.audio_voice.findText(voice)
        if index >= 0:
            self.audio_voice.setCurrentIndex(index)

        self.prompt_template.setPlainText(config.get("prompt_template", ""))

    def get_new_config(self):
        return {
            "api_endpoint": self.api_endpoint.text(),
            "api_key": self.api_key.text(),
            "model": self.model.text(),
            "target_field": self.target_field.text(),
            "generate_audio": self.generate_audio.isChecked(),
            "audio_voice": self.audio_voice.currentText(),
            "prompt_template": self.prompt_template.toPlainText(),
        }


def on_settings():
    dialog = YujingSettingsDialog(mw)
    if dialog.exec():
        new_config = dialog.get_new_config()
        # Ensure we write to the correct root addon folder name
        addon_name = __name__.split(".")[0]
        mw.addonManager.writeConfig(addon_name, new_config)
        showInfo("Settings saved successfully.")
