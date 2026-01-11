from aqt.qt import *
from dotenv import set_key

from project_paths import dotenv_path


class GitHubCopilotTokenDialog(QDialog):
    """Dialog for managing GitHub Copilot API token"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("GitHub Copilot Token")
        self.resize(500, 200)
        
        self.callback = None
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()

        # Instruction label
        instruction_label = QLabel(
            "Enter your GitHub Copilot API token.\n"
            "You can obtain this from GitHub Copilot settings or by using the GitHub CLI."
        )
        instruction_label.setWordWrap(True)
        layout.addWidget(instruction_label)

        # Token input
        self.token_input = QLineEdit()
        self.token_input.setPlaceholderText("GitHub Copilot Token")
        self.token_input.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self.token_input)

        # Show/Hide password checkbox
        self.show_token_checkbox = QCheckBox("Show token")
        self.show_token_checkbox.stateChanged.connect(self.toggle_token_visibility)
        layout.addWidget(self.show_token_checkbox)

        # Buttons
        button_layout = QHBoxLayout()
        
        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self.save_token)
        button_layout.addWidget(self.save_button)
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)
        
        layout.addLayout(button_layout)
        
        # Help link
        help_label = QLabel(
            '<a href="https://docs.github.com/en/copilot">GitHub Copilot Documentation</a>'
        )
        help_label.setOpenExternalLinks(True)
        layout.addWidget(help_label)

        self.setLayout(layout)

    def toggle_token_visibility(self, state):
        if state == Qt.CheckState.Checked.value:
            self.token_input.setEchoMode(QLineEdit.EchoMode.Normal)
        else:
            self.token_input.setEchoMode(QLineEdit.EchoMode.Password)

    def save_token(self):
        token = self.token_input.text().strip()
        
        if not token:
            QMessageBox.warning(self, "Invalid Token", "Please enter a valid GitHub Copilot token.")
            return
        
        # Save to .env file
        set_key(dotenv_path, 'GITHUB_COPILOT_TOKEN', token)
        
        # Call the callback if set
        if self.callback:
            self.callback(token)
        
        self.accept()

    def on_token_save(self, callback):
        """Set callback function to be called when token is saved"""
        self.callback = callback
