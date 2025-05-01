import sys
import csv
import logging
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QMessageBox, QTextEdit, QDialogButtonBox
)
from PySide6.QtCore import Slot

logger = logging.getLogger(__name__)

class QuoteManagementDialog(QDialog):
    def __init__(self, quote_manager, parent=None):
        super().__init__(parent)
        self.quote_manager = quote_manager
        self.initUI()
        # Optionally load and display existing quotes - keep simple for now

    def initUI(self):
        self.setWindowTitle("Manage Quotes")
        self.setMinimumWidth(400)

        layout = QVBoxLayout(self)

        # Optional: Display existing quotes (could be slow for large files)
        # self.quotes_display = QTextEdit()
        # self.quotes_display.setReadOnly(True)
        # self.load_quotes_for_display()
        # layout.addWidget(QLabel("Current Quotes:"))
        # layout.addWidget(self.quotes_display)

        # Add New Quote Section
        add_layout = QVBoxLayout()
        add_layout.addWidget(QLabel("Add New Quote:"))

        quote_hbox = QHBoxLayout()
        quote_hbox.addWidget(QLabel("Quote:"))
        self.new_quote_edit = QLineEdit()
        self.new_quote_edit.setPlaceholderText("Enter the quote text")
        quote_hbox.addWidget(self.new_quote_edit)
        add_layout.addLayout(quote_hbox)

        author_hbox = QHBoxLayout()
        author_hbox.addWidget(QLabel("Author:"))
        self.new_author_edit = QLineEdit()
        self.new_author_edit.setPlaceholderText("(Optional) Enter the author")
        author_hbox.addWidget(self.new_author_edit)
        add_layout.addLayout(author_hbox)

        self.add_button = QPushButton("Add Quote")
        self.add_button.clicked.connect(self.add_new_quote)
        add_layout.addWidget(self.add_button)

        layout.addLayout(add_layout)

        # Dialog Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Close)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        self.setLayout(layout)

    # Optional: Method to load quotes into the display area
    # def load_quotes_for_display(self):
    #     try:
    #         quotes = self.quote_manager.get_all_quotes_raw() # Need method in QuoteManager
    #         display_text = "\n".join([f'"{q[0]}" - {q[1]}' for q in quotes])
    #         self.quotes_display.setText(display_text)
    #     except Exception as e:
    #         self.quotes_display.setText(f"Error loading quotes: {e}")
    #         logger.error(f"Error loading quotes for display: {e}", exc_info=True)

    @Slot()
    def add_new_quote(self):
        quote_text = self.new_quote_edit.text().strip()
        author_text = self.new_author_edit.text().strip()

        if not quote_text:
            QMessageBox.warning(self, "Input Error", "Quote text cannot be empty.")
            return

        # Author is optional, use placeholder if empty
        if not author_text:
            author_text = "Unknown"

        try:
            # Call the quote manager's add method (needs implementation)
            self.quote_manager.add_quote(quote_text, author_text)
            QMessageBox.information(self, "Success", "Quote added successfully!")
            self.new_quote_edit.clear()
            self.new_author_edit.clear()
            # Optionally refresh the display:
            # self.load_quotes_for_display()
        except AttributeError:
             logger.error("QuoteManager does not have an 'add_quote' method.")
             QMessageBox.critical(self, "Error", "Feature not fully implemented: QuoteManager cannot add quotes.")
        except Exception as e:
            logger.error(f"Error adding quote: {e}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Failed to add quote.\nError: {e}") 