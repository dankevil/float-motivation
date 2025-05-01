import sys
import os
from PySide6.QtWidgets import (
    QApplication, QDialog, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QPushButton, QSpinBox, QCheckBox, QFileDialog,
    QColorDialog, QDialogButtonBox, QGroupBox, QRadioButton, QMessageBox,
    QFontComboBox, QSpacerItem, QSizePolicy, QComboBox, QListWidget
)
from PySide6.QtGui import QColor, QPalette, QIntValidator, QFont
from PySide6.QtCore import Signal, Slot, QUrl

# Assuming ConfigManager is in core
# from core.config_manager import ConfigManager
from .quote_management_dialog import QuoteManagementDialog # Import needed here too

# Define supported video file extensions
VIDEO_FILE_FILTERS = "Video Files (*.mp4 *.avi *.mov *.mkv *.wmv);;All Files (*)"

class SettingsDialog(QDialog):
    # Signal emitting the updated settings dictionary when Apply/OK is clicked
    settings_applied = Signal(dict)

    def __init__(self, config_manager, quote_manager, parent=None):
        super().__init__(parent)
        self.config_manager = config_manager
        self.quote_manager = quote_manager # Store quote manager instance
        self.current_settings = self.config_manager.get_all_settings() # Keep a working copy
        self.initUI()
        self.load_settings()

    def initUI(self):
        self.setWindowTitle("Widget Settings")
        self.setMinimumWidth(450)

        layout = QVBoxLayout(self)

        # --- Quotes Section ---
        quotes_group = QGroupBox("Quotes Source")
        quotes_layout = QGridLayout(quotes_group)

        self.csv_path_label = QLabel("Quotes CSV File:")
        self.csv_path_edit = QLineEdit()
        self.csv_path_edit.setPlaceholderText("Path to your .csv file")
        self.browse_csv_button = QPushButton("Browse...")
        self.browse_csv_button.clicked.connect(self.browse_csv)

        self.interval_label = QLabel("Quote Display Interval (seconds):")
        self.interval_spinbox = QSpinBox()
        self.interval_spinbox.setRange(1, 3600) # 1 second to 1 hour
        self.interval_spinbox.setSuffix(" s")

        quotes_layout.addWidget(self.csv_path_label, 0, 0)
        quotes_layout.addWidget(self.csv_path_edit, 0, 1)
        quotes_layout.addWidget(self.browse_csv_button, 0, 2)
        quotes_layout.addWidget(self.interval_label, 1, 0)
        quotes_layout.addWidget(self.interval_spinbox, 1, 1, 1, 2) # Span 2 columns

        # Add Manage Quotes button
        self.manage_quotes_button = QPushButton("Manage Quotes...")
        self.manage_quotes_button.clicked.connect(self.open_quote_manager)
        quotes_layout.addWidget(self.manage_quotes_button, 2, 0, 1, 3) # Span all columns

        layout.addWidget(quotes_group)
        layout.addSpacerItem(QSpacerItem(20, 10, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))

        # --- Appearance Section (Using QGridLayout for better alignment) ---
        appearance_group = QGroupBox("Appearance")
        appearance_layout = QGridLayout(appearance_group)

        # Background Type (Row 0)
        bg_type_label = QLabel("Background:")
        self.bg_color_radio = QRadioButton("Color")
        self.bg_image_radio = QRadioButton("Image")
        self.bg_video_radio = QRadioButton("Video")
        self.bg_color_radio.setChecked(True) # Default
        self.bg_color_radio.toggled.connect(self.update_background_controls)
        self.bg_image_radio.toggled.connect(self.update_background_controls)
        self.bg_video_radio.toggled.connect(self.update_background_controls)

        bg_type_inner_layout = QHBoxLayout()
        bg_type_inner_layout.addWidget(self.bg_color_radio)
        bg_type_inner_layout.addWidget(self.bg_image_radio)
        bg_type_inner_layout.addWidget(self.bg_video_radio)
        bg_type_inner_layout.addStretch()

        appearance_layout.addWidget(bg_type_label, 0, 0)
        appearance_layout.addLayout(bg_type_inner_layout, 0, 1)

        # Background Value (Row 1) - Spans across columns
        self.bg_value_widget = QWidget() # Container for different controls
        self.bg_value_layout = QHBoxLayout(self.bg_value_widget)
        self.bg_value_layout.setContentsMargins(0, 5, 0, 5) # Add some vertical margin

        # Color controls
        # Use QHBoxLayout internally, but add the whole widget to the grid
        self.bg_color_label = QLabel("Value:") # Changed label slightly
        self.bg_color_button = QPushButton("Choose Color...")
        self.bg_color_preview = QLabel()
        self.bg_color_preview.setFixedSize(80, 25)
        self.bg_color_button.clicked.connect(self.choose_bg_color)
        color_widget = QWidget()
        color_layout = QHBoxLayout(color_widget)
        color_layout.setContentsMargins(0,0,0,0)
        color_layout.addWidget(self.bg_color_label)
        color_layout.addWidget(self.bg_color_button)
        color_layout.addWidget(self.bg_color_preview)
        color_layout.addStretch()
        self.bg_value_layout.addWidget(color_widget)
        self.color_widget = color_widget

        # Image controls
        self.bg_image_label = QLabel("File:") # Changed label slightly
        self.bg_image_path_edit = QLineEdit()
        self.bg_image_path_edit.setPlaceholderText("Path to background image")
        self.bg_browse_image_button = QPushButton("Browse...")
        self.bg_browse_image_button.clicked.connect(self.browse_bg_image)
        image_widget = QWidget()
        # Use VBoxLayout for image path and mode selection
        image_outer_layout = QVBoxLayout(image_widget)
        image_outer_layout.setContentsMargins(0,0,0,0)
        
        # Single image path row
        image_path_layout = QHBoxLayout()
        image_path_layout.addWidget(self.bg_image_label)
        image_path_layout.addWidget(self.bg_image_path_edit)
        image_path_layout.addWidget(self.bg_browse_image_button)
        image_outer_layout.addLayout(image_path_layout)
        
        # Add Multiple Images section
        multiple_images_group = QGroupBox("Multiple Background Images")
        multiple_images_layout = QVBoxLayout(multiple_images_group)
        
        # List widget to show added images
        self.images_list = QListWidget()
        self.images_list.setSelectionMode(QListWidget.SingleSelection)
        self.images_list.setMinimumHeight(100)
        
        # Buttons for managing the list
        image_buttons_layout = QHBoxLayout()
        self.add_image_button = QPushButton("Add Current Image")
        self.remove_image_button = QPushButton("Remove Selected")
        self.clear_images_button = QPushButton("Clear All")
        
        self.add_image_button.clicked.connect(self.add_current_image)
        self.remove_image_button.clicked.connect(self.remove_selected_image)
        self.clear_images_button.clicked.connect(self.clear_all_images)
        
        image_buttons_layout.addWidget(self.add_image_button)
        image_buttons_layout.addWidget(self.remove_image_button)
        image_buttons_layout.addWidget(self.clear_images_button)
        
        multiple_images_layout.addWidget(QLabel("When multiple images are added, they will cycle along with the quotes"))
        multiple_images_layout.addWidget(self.images_list)
        multiple_images_layout.addLayout(image_buttons_layout)
        
        image_outer_layout.addWidget(multiple_images_group)

        # Add Image Mode selection
        image_mode_layout = QHBoxLayout()
        self.bg_image_mode_label = QLabel("Mode:")
        self.bg_image_mode_combo = QComboBox()
        self.bg_image_mode_combo.addItems(["Stretch", "Cover", "Contain"]) # Add modes
        image_mode_layout.addWidget(self.bg_image_mode_label)
        image_mode_layout.addWidget(self.bg_image_mode_combo)
        image_mode_layout.addStretch()
        image_outer_layout.addLayout(image_mode_layout)

        self.bg_value_layout.addWidget(image_widget)
        self.image_widget = image_widget
        self.image_widget.setVisible(False)

        # Video controls
        self.bg_video_label = QLabel("File:") # Changed label slightly
        self.bg_video_path_edit = QLineEdit()
        self.bg_video_path_edit.setPlaceholderText("Path to background video")
        self.bg_browse_video_button = QPushButton("Browse...")
        self.bg_browse_video_button.clicked.connect(self.browse_bg_video)
        video_widget = QWidget()
        video_layout = QHBoxLayout(video_widget)
        video_layout.setContentsMargins(0,0,0,0)
        video_layout.addWidget(self.bg_video_label)
        video_layout.addWidget(self.bg_video_path_edit)
        video_layout.addWidget(self.bg_browse_video_button)
        self.bg_value_layout.addWidget(video_widget)
        self.video_widget = video_widget
        self.video_widget.setVisible(False)

        self.bg_value_layout.addStretch()
        appearance_layout.addWidget(self.bg_value_widget, 1, 0, 1, 2) # Add to grid, span 2 cols

        # Image Mode (Row 2)
        self.image_mode_widget = QWidget() # Container for image mode controls
        image_mode_layout = QHBoxLayout(self.image_mode_widget)
        image_mode_layout.setContentsMargins(0, 0, 0, 0)
        self.bg_image_mode_label = QLabel("Image Mode:")
        self.bg_image_mode_combo = QComboBox()
        self.bg_image_mode_combo.addItems(["Stretch", "Cover", "Contain"]) # Add modes
        image_mode_layout.addWidget(self.bg_image_mode_label)
        image_mode_layout.addWidget(self.bg_image_mode_combo)
        image_mode_layout.addStretch()
        appearance_layout.addWidget(self.image_mode_widget, 2, 0, 1, 2) # Add below bg value
        self.image_mode_widget.setVisible(False) # Initially hidden

        # Text Color (Row 3)
        self.text_color_label = QLabel("Text Color:")
        self.text_color_button = QPushButton("Choose Color...")
        self.text_color_preview = QLabel()
        self.text_color_preview.setFixedSize(80, 25)
        self.text_color_button.clicked.connect(self.choose_text_color)

        text_color_inner_layout = QHBoxLayout()
        text_color_inner_layout.addWidget(self.text_color_button)
        text_color_inner_layout.addWidget(self.text_color_preview)
        text_color_inner_layout.addStretch()

        appearance_layout.addWidget(self.text_color_label, 3, 0)
        appearance_layout.addLayout(text_color_inner_layout, 3, 1)

        # Font Selection (Row 4)
        self.font_family_label = QLabel("Font:") # Combined label
        self.font_family_combo = QFontComboBox()
        self.font_family_combo.setEditable(False)
        self.font_size_spinbox = QSpinBox()
        self.font_size_spinbox.setRange(8, 72) # Example range
        self.font_size_spinbox.setSuffix(" pt")
        self.font_size_spinbox.setFixedWidth(70) # Give font size fixed width

        font_inner_layout = QHBoxLayout()
        font_inner_layout.addWidget(self.font_family_combo, 1)
        font_inner_layout.addWidget(self.font_size_spinbox)
        font_inner_layout.addStretch()

        appearance_layout.addWidget(self.font_family_label, 4, 0)
        appearance_layout.addLayout(font_inner_layout, 4, 1)

        # Set column stretch for the grid layout
        appearance_layout.setColumnStretch(1, 1)

        layout.addWidget(appearance_group)
        layout.addSpacerItem(QSpacerItem(20, 10, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))

        # --- Window Behavior --- 
        behavior_group = QGroupBox("Window Behavior")
        behavior_layout = QVBoxLayout(behavior_group)
        self.always_on_top_checkbox = QCheckBox("Keep widget always on top")
        behavior_layout.addWidget(self.always_on_top_checkbox)
        
        # Add icon mode checkbox
        self.icon_mode_checkbox = QCheckBox("Use floating icon mode (show widget on hover)")
        self.icon_mode_checkbox.setToolTip("When enabled, the widget is hidden and appears when hovering over a small floating icon")
        behavior_layout.addWidget(self.icon_mode_checkbox)
        
        # Add note about needing to restart
        icon_mode_note = QLabel("Note: Changes to icon mode require restarting the application")
        icon_mode_note.setStyleSheet("color: gray; font-size: 10px;")
        behavior_layout.addWidget(icon_mode_note)
        
        layout.addWidget(behavior_group)
        layout.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))

        # --- Dialog Buttons --- 
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel | QDialogButtonBox.Apply)
        self.button_box.accepted.connect(self.accept_settings)
        self.button_box.rejected.connect(self.reject)
        self.button_box.button(QDialogButtonBox.Apply).clicked.connect(self.apply_settings)

        layout.addWidget(self.button_box)

        self.setLayout(layout)
        self.update_background_controls()

    def load_settings(self):
        """Loads settings from the working copy into the UI controls."""
        self.csv_path_edit.setText(self.current_settings.get("csv_path", ""))

        interval_ms = self.current_settings.get("interval_ms", 10000)
        self.interval_spinbox.setValue(interval_ms // 1000) # Convert ms to s

        bg_type = self.current_settings.get("background_type", "color")
        bg_value = self.current_settings.get("background_value", "#1E1E1E")
        image_mode = self.current_settings.get("image_mode", "Stretch") # Load image mode

        if bg_type == "color":
            self.bg_color_radio.setChecked(True)
            self._set_color_preview(self.bg_color_preview, bg_value)
        elif bg_type == "image":
            self.bg_image_radio.setChecked(True)
            self.bg_image_path_edit.setText(bg_value)
            self.bg_image_mode_combo.setCurrentText(image_mode) # Set combo box value
            
            # Load multiple image paths if available
            self.images_list.clear()
            image_paths = self.current_settings.get("image_paths", [])
            for path in image_paths:
                if os.path.isfile(path):
                    self.images_list.addItem(path)
        elif bg_type == "video":
            self.bg_video_radio.setChecked(True)
            self.bg_video_path_edit.setText(bg_value)

        self.update_background_controls() # Ensures correct widget visibility

        text_color_value = self.current_settings.get("text_color", "#DCDCDC")
        self._set_color_preview(self.text_color_preview, text_color_value)

        # Load Font Settings
        font_family = self.current_settings.get("font_family", "Arial")
        font_size = self.current_settings.get("font_size", 14)
        self.font_family_combo.setCurrentFont(QFont(font_family))
        self.font_size_spinbox.setValue(font_size)

        self.always_on_top_checkbox.setChecked(self.current_settings.get("always_on_top", True))
        
        # Load icon mode setting
        self.icon_mode_checkbox.setChecked(self.current_settings.get("use_icon_mode", True))

    def save_settings_to_dict(self):
        """Saves the current UI control values into the self.current_settings dictionary."""
        self.current_settings["csv_path"] = self.csv_path_edit.text()
        self.current_settings["interval_ms"] = self.interval_spinbox.value() * 1000 # Convert s to ms

        if self.bg_color_radio.isChecked():
            self.current_settings["background_type"] = "color"
            color_hex = self._get_color_from_preview(self.bg_color_preview)
            self.current_settings["background_value"] = color_hex
        elif self.bg_image_radio.isChecked():
            self.current_settings["background_type"] = "image"
            self.current_settings["background_value"] = self.bg_image_path_edit.text()
            self.current_settings["image_mode"] = self.bg_image_mode_combo.currentText() # Save image mode
            
            # Save multiple image paths
            image_paths = []
            for i in range(self.images_list.count()):
                image_paths.append(self.images_list.item(i).text())
            self.current_settings["image_paths"] = image_paths
        elif self.bg_video_radio.isChecked():
            self.current_settings["background_type"] = "video"
            self.current_settings["background_value"] = self.bg_video_path_edit.text()

        text_color_hex = self._get_color_from_preview(self.text_color_preview)
        self.current_settings["text_color"] = text_color_hex

        # Save Font Settings
        selected_font = self.font_family_combo.currentFont()
        self.current_settings["font_family"] = selected_font.family()
        self.current_settings["font_size"] = self.font_size_spinbox.value()

        self.current_settings["always_on_top"] = self.always_on_top_checkbox.isChecked()
        
        # Save icon mode setting
        self.current_settings["use_icon_mode"] = self.icon_mode_checkbox.isChecked()

    @Slot()
    def apply_settings(self):
        """Applies the current settings without closing the dialog."""
        self.save_settings_to_dict()
        # Persist changes immediately
        self.config_manager.settings.update(self.current_settings)
        self.config_manager.save_config()
        self.settings_applied.emit(self.current_settings.copy())
        print("Settings applied") # For debugging

    @Slot()
    def accept_settings(self):
        """Applies the settings and closes the dialog."""
        self.apply_settings()
        self.accept()

    @Slot()
    def browse_csv(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Quotes CSV File", "", "CSV Files (*.csv);;Text Files (*.txt);;All Files (*)")
        if file_path:
            self.csv_path_edit.setText(file_path)

    @Slot()
    def choose_bg_color(self):
        current_color_hex = self._get_color_from_preview(self.bg_color_preview)
        initial_color = QColor(current_color_hex) if QColor.isValidColor(current_color_hex) else QColor("#1E1E1E")

        color = QColorDialog.getColor(initial_color, self, "Choose Background Color", options=QColorDialog.ShowAlphaChannel)
        if color.isValid():
            hex_color = color.name(QColor.HexArgb if color.alpha() != 255 else QColor.HexRgb)
            self._set_color_preview(self.bg_color_preview, hex_color)

    @Slot()
    def choose_text_color(self):
        current_color_hex = self._get_color_from_preview(self.text_color_preview)
        initial_color = QColor(current_color_hex) if QColor.isValidColor(current_color_hex) else QColor("#DCDCDC")

        color = QColorDialog.getColor(initial_color, self, "Choose Text Color", options=QColorDialog.ShowAlphaChannel)
        if color.isValid():
            hex_color = color.name(QColor.HexArgb if color.alpha() != 255 else QColor.HexRgb)
            self._set_color_preview(self.text_color_preview, hex_color)

    @Slot()
    def browse_bg_image(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Background Image", "", "Image Files (*.png *.jpg *.jpeg *.bmp *.gif);;All Files (*)")
        if file_path:
            self.bg_image_path_edit.setText(file_path)

    @Slot()
    def browse_bg_video(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Background Video", "", VIDEO_FILE_FILTERS)
        if file_path:
            self.bg_video_path_edit.setText(file_path)

    def _set_color_preview(self, preview_label, color_hex):
        """Sets the background color of a QLabel to visualize a color."""
        try:
            color = QColor(color_hex)
            if not color.isValid():
                raise ValueError("Invalid color format")
            preview_label.setStyleSheet(f"background-color: {color.name(QColor.HexArgb)}; border: 1px solid grey;")
            preview_label.setToolTip(color_hex) # Show the hex value on hover
        except ValueError:
            preview_label.setStyleSheet("background-color: grey; border: 1px solid red;")
            preview_label.setToolTip(f"Invalid color: {color_hex}")

    def _get_color_from_preview(self, preview_label):
        """Extracts the hex color string from the preview label's tooltip or style."""
        tooltip = preview_label.toolTip()
        if tooltip and QColor.isValidColor(tooltip):
            # Ensure format includes alpha if present
            color = QColor(tooltip)
            return color.name(QColor.HexArgb if color.alpha() != 255 else QColor.HexRgb)
        # Fallback: Try parsing stylesheet (less reliable)
        style = preview_label.styleSheet()
        try:
            color_part = style.split("background-color:")[-1].split(";")[0].strip()
            if QColor.isValidColor(color_part):
                color = QColor(color_part)
                return color.name(QColor.HexArgb if color.alpha() != 255 else QColor.HexRgb)
        except Exception:
            pass
        # Return default if parsing fails
        if preview_label == self.bg_color_preview:
            return "#1E1E1E"
        else:
            return "#DCDCDC"

    @Slot(bool)
    def update_background_controls(self):
        """Shows/hides the relevant background value controls based on the selected radio button."""
        is_color = self.bg_color_radio.isChecked()
        is_image = self.bg_image_radio.isChecked()
        is_video = self.bg_video_radio.isChecked()

        self.color_widget.setVisible(is_color)
        self.image_widget.setVisible(is_image)
        self.video_widget.setVisible(is_video)
        self.image_mode_widget.setVisible(is_image) # Show/hide image mode with image path

        # Ensure the layout recalculates size if needed
        self.bg_value_widget.updateGeometry()
        self.adjustSize()

    def adjustSize(self):
        super().adjustSize()

    @Slot()
    def open_quote_manager(self):
        # Open the quote management dialog, passing the quote manager instance
        try:
            dialog = QuoteManagementDialog(self.quote_manager, self)
            dialog.exec()
            # Optional: Maybe force a quote refresh in main widget if needed
            # but QuoteManager updates its internal list, so next cycle should be fine.
        except Exception as e:
             logger.error(f"Failed to open Quote Management Dialog: {e}", exc_info=True)
             QMessageBox.critical(self, "Error", f"Could not open the quote manager.\nError: {e}")

    @Slot()
    def add_current_image(self):
        """Adds the current image path to the multiple images list"""
        image_path = self.bg_image_path_edit.text().strip()
        if not image_path:
            QMessageBox.warning(self, "Empty Path", "Please select an image file first")
            return
            
        if not os.path.isfile(image_path):
            QMessageBox.warning(self, "Invalid Path", "The selected image file does not exist")
            return
            
        # Check if the image is already in the list to avoid duplicates
        for i in range(self.images_list.count()):
            if self.images_list.item(i).text() == image_path:
                QMessageBox.information(self, "Duplicate", "This image is already in the list")
                return
                
        # Add the image to the list
        self.images_list.addItem(image_path)
        
    @Slot()
    def remove_selected_image(self):
        """Removes the selected image from the list"""
        selected_items = self.images_list.selectedItems()
        if not selected_items:
            QMessageBox.information(self, "No Selection", "Please select an image to remove")
            return
            
        for item in selected_items:
            self.images_list.takeItem(self.images_list.row(item))
            
    @Slot()
    def clear_all_images(self):
        """Clears all images from the list"""
        if self.images_list.count() == 0:
            return
            
        confirm = QMessageBox.question(
            self, 
            "Confirm Clear", 
            "Are you sure you want to remove all images from the list?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if confirm == QMessageBox.Yes:
            self.images_list.clear()

# --- To Run this Dialog Directly (for testing) ---
if __name__ == '__main__':
    # Dummy ConfigManager for testing
    class DummyConfigManager:
        def __init__(self):
            self._settings = {
                "csv_path": "test_quotes.csv",
                "interval_ms": 15000,
                "background_type": "video",
                "background_value": "C:/test/my_video.mp4",
                "text_color": "#FFFFFF",
                "always_on_top": False,
                "window_geometry": [100, 100, 300, 100],
                "font_family": "Arial",
                "font_size": 14
            }
            self.settings = self._settings.copy()

        def get_setting(self, key, default=None):
            return self.settings.get(key, default)

        def set_setting(self, key, value):
            self.settings[key] = value

        def get_all_settings(self):
            return self.settings.copy()

        def save_config(self):
            print("DummyConfigManager: Pretending to save settings:", self.settings)
            self._settings = self.settings.copy() # Update base settings for next load

    app = QApplication(sys.argv)
    dummy_config = DummyConfigManager()
    dialog = SettingsDialog(config_manager=dummy_config)

    @Slot(dict)
    def on_settings_applied(settings):
        print("\nSettings Applied Signal Received:")
        import json
        print(json.dumps(settings, indent=2))

    dialog.settings_applied.connect(on_settings_applied)

    result = dialog.exec()

    if result == QDialog.Accepted:
        print("\nDialog Accepted (OK clicked).")
        final_settings = dummy_config.get_all_settings()
        print("Final settings in dummy config manager:")
        import json
        print(json.dumps(final_settings, indent=2))
    else:
        print("\nDialog Cancelled or Closed.")
        final_settings = dummy_config.get_all_settings()
        print("Final settings in dummy config manager (might be unchanged if cancelled without Apply):")
        import json
        print(json.dumps(final_settings, indent=2))

    sys.exit() 