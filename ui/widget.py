import sys
import os # Added os
import logging # Added logging
from PySide6.QtWidgets import (
    QApplication, QWidget, QLabel, QVBoxLayout, QMenu, QMessageBox, QStackedLayout, QStyle, # Added QStyle
    QSizeGrip, QPushButton, QHBoxLayout, QGridLayout # Added QSizeGrip, QPushButton, QHBoxLayout, QGridLayout
)
from PySide6.QtCore import Qt, QPoint, Slot, QUrl, QSize, QTimer # Added QUrl, QSize, QTimer
from PySide6.QtGui import QPalette, QColor, QFont, QAction, QPixmap, QIcon, QCursor # Added QAction, QPixmap, QIcon, QCursor
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput # Added QMediaPlayer, QAudioOutput
from PySide6.QtMultimediaWidgets import QVideoWidget # Added QVideoWidget

# Assuming imports from sibling directories work or sys.path is adjusted
# from core.config_manager import ConfigManager
# from core.quote_manager import QuoteManager
# from core.timer import QuoteTimer
from .settings_dialog import SettingsDialog # Use relative import for sibling module
from .quote_management_dialog import QuoteManagementDialog # Import quote management dialog

logger = logging.getLogger(__name__) # Setup logger

class MotivationalWidget(QWidget):
    # Add quote_manager, quote_timer parameters to __init__
    def __init__(self, config_manager, quote_manager, quote_timer, parent=None, icon_mode=False):
        super().__init__(parent)
        self.config_manager = config_manager
        self.quote_manager = quote_manager
        self.quote_timer = quote_timer
        self.settings_dialog = None # To hold the settings dialog instance
        self.icon_mode = icon_mode # Whether this widget is shown via a floating icon
        
        # Track mouse position and auto-hide behavior
        self.is_mouse_over = False
        self.hide_timer = QTimer(self)
        self.hide_timer.setSingleShot(True)
        self.hide_timer.timeout.connect(self.auto_hide_if_needed)

        # --- Media Player Setup ---
        self.media_player = None
        self.video_widget = None
        self.audio_output = None
        self._setup_media_player()
        
        # Track current image index for multiple images
        self.current_image_index = 0
        self.image_paths = []

        self.initUI()
        self.apply_settings() # Apply initial settings from config
        
        # Initially hide the widget if in icon mode
        if self.icon_mode:
            self.hide()

    def _setup_media_player(self):
        """Initializes the media player and video widget."""
        self.media_player = QMediaPlayer()
        self.audio_output = QAudioOutput() # Required even if muted
        self.media_player.setAudioOutput(self.audio_output)
        self.audio_output.setMuted(True) # Mute by default
        self.media_player.setLoops(QMediaPlayer.Loops.Infinite) # Loop video

        self.video_widget = QVideoWidget()
        self.media_player.setVideoOutput(self.video_widget)
        self.video_widget.setVisible(False) # Initially hidden

        # Handle potential errors
        self.media_player.errorOccurred.connect(self._handle_media_error)

    def initUI(self):
        # --- Window Properties ---
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Tool) # Initial flags, AlwaysOnTop set in apply_settings
        # Make the main widget transparent, background will be handled by a child widget
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAutoFillBackground(False) # Do not fill the main widget background
        self.setStyleSheet("background:transparent;") # Ensure transparency via stylesheet

        self.setContextMenuPolicy(Qt.CustomContextMenu) # Enable context menu
        self.customContextMenuRequested.connect(self.show_context_menu)

        # --- Default Appearance (will be overridden by apply_settings) ---
        self.resize(400, 150)

        # --- Layout and Content ---
        # Overall layout for the entire widget (content + grip)
        overall_layout = QVBoxLayout(self)
        overall_layout.setContentsMargins(0, 0, 0, 0) # No margins for the outermost layout

        # Create the central content area using QStackedLayout
        content_widget = QWidget() # Container for the stack
        content_widget.setStyleSheet("background:transparent;") # Ensure container is transparent
        self.main_layout = QStackedLayout(content_widget)
        self.main_layout.setStackingMode(QStackedLayout.StackingMode.StackAll)
        # Margins for the content area itself (where background/text appears)
        content_widget.setContentsMargins(10, 10, 10, 10) # Adjust as needed

        # Layer 0: Background Widget (specific background applied here)
        self.background_widget = QWidget()
        self.background_widget.setAutoFillBackground(True) # This widget will be colored/styled
        # Add rounded corners to the background - adjust radius as desired
        self.background_widget.setStyleSheet("border-radius: 10px;")
        self.main_layout.addWidget(self.background_widget)

        # Layer 1: Video Widget (initially hidden)
        # Make video widget transparent initially, background set in apply_settings
        self.video_widget.setStyleSheet("background:transparent; border-radius: 10px;")
        self.video_widget.setVisible(False)
        self.main_layout.addWidget(self.video_widget)

        # Layer 2: Text Content Container (with transparent background and navigation)
        self.text_container_widget = QWidget()
        self.text_container_widget.setAutoFillBackground(False) # Let stack manage background
        self.text_container_widget.setStyleSheet("background:transparent;")
        
        # Use a Grid layout for text container with navigation arrows
        text_layout = QGridLayout(self.text_container_widget)
        text_layout.setContentsMargins(10, 10, 10, 10) # Padding inside the text area
        
        # Navigation buttons with improved visibility
        # Previous quote button - left side
        self.prev_button = QPushButton()
        self.prev_button.setIcon(QIcon(self.style().standardPixmap(QStyle.StandardPixmap.SP_MediaSkipBackward)))
        self.prev_button.setIconSize(QSize(24, 24))
        self.prev_button.setFixedSize(36, 36)
        # Style buttons for better visibility with semi-transparent background
        self.prev_button.setStyleSheet("background-color: rgba(0, 0, 0, 0.3); border: none; border-radius: 18px; padding: 6px;")
        self.prev_button.clicked.connect(self.show_prev_quote_action)
        text_layout.addWidget(self.prev_button, 1, 0, Qt.AlignLeft | Qt.AlignVCenter)
        
        # Next quote button - right side
        self.next_button = QPushButton()
        self.next_button.setIcon(QIcon(self.style().standardPixmap(QStyle.StandardPixmap.SP_MediaSkipForward)))
        self.next_button.setIconSize(QSize(24, 24))
        self.next_button.setFixedSize(36, 36)
        # Style buttons for better visibility with semi-transparent background
        self.next_button.setStyleSheet("background-color: rgba(0, 0, 0, 0.3); border: none; border-radius: 18px; padding: 6px;")
        self.next_button.clicked.connect(self.show_next_quote_action)
        text_layout.addWidget(self.next_button, 1, 2, Qt.AlignRight | Qt.AlignVCenter)
        
        # Quote and author labels in center column
        self.quote_label = QLabel("Loading quote...", self.text_container_widget)
        self.quote_label.setAlignment(Qt.AlignCenter)
        self.quote_label.setWordWrap(True)
        self.quote_label.setStyleSheet("background:transparent;") # Explicitly transparent
        text_layout.addWidget(self.quote_label, 0, 0, 1, 3) # span all columns
        
        self.author_label = QLabel("- Author", self.text_container_widget)
        self.author_label.setAlignment(Qt.AlignRight | Qt.AlignBottom)
        self.author_label.setVisible(False)
        self.author_label.setStyleSheet("background:transparent;") # Explicitly transparent
        text_layout.addWidget(self.author_label, 2, 0, 1, 3, Qt.AlignRight) # span all columns, align right
        
        # Set column stretches for better layout
        text_layout.setColumnStretch(0, 1)  # Left column (prev button)
        text_layout.setColumnStretch(1, 10) # Center column (takes most space)
        text_layout.setColumnStretch(2, 1)  # Right column (next button)
        
        # Add text container to stack (on top)
        self.main_layout.addWidget(self.text_container_widget)

        # Ensure text container is the topmost visible widget initially
        self.main_layout.setCurrentWidget(self.text_container_widget)

        overall_layout.addWidget(content_widget, 1)  # Add content stack to overall layout, stretchable

        # Size grip at the bottom-right corner
        bottom_layout = QHBoxLayout()
        bottom_layout.setContentsMargins(0, 0, 5, 5) # Adjust margins for grip placement
        bottom_layout.addStretch(1)

        size_grip = QSizeGrip(self) # Create size grip as child of main window
        size_grip.setFixedSize(16, 16) # Ensure consistent size
        # Style grip to be subtle - maybe adjust color based on theme later
        size_grip.setStyleSheet("background-color: rgba(0, 0, 0, 0.2);")
        bottom_layout.addWidget(size_grip)

        overall_layout.addLayout(bottom_layout) # Add grip layout to the bottom

        # --- Dragging Functionality ---
        self._drag_pos = QPoint(0, 0)

    # --- Context Menu --- 
    def show_context_menu(self, position):
        # Temporarily disable hide timer if in icon mode to prevent glitches
        hide_timer_was_active = False
        if self.icon_mode and self.hide_timer.isActive():
            hide_timer_was_active = True
            self.hide_timer.stop()
            
        contextMenu = QMenu(self)

        # Get standard icons
        style = self.style()
        settings_icon = QIcon(style.standardPixmap(QStyle.StandardPixmap.SP_FileDialogDetailedView)) # Cogwheel-like
        next_icon = QIcon(style.standardPixmap(QStyle.StandardPixmap.SP_MediaSkipForward))
        prev_icon = QIcon(style.standardPixmap(QStyle.StandardPixmap.SP_MediaSkipBackward))
        exit_icon = QIcon(style.standardPixmap(QStyle.StandardPixmap.SP_DialogCloseButton))

        # Create actions with icons
        settings_action = QAction(settings_icon, "Settings...", self)
        prev_quote_action = QAction(prev_icon, "Previous Quote", self)
        next_quote_action = QAction(next_icon, "Next Quote", self)
        exit_action = QAction(exit_icon, "Exit", self)

        settings_action.triggered.connect(self.open_settings_dialog)
        prev_quote_action.triggered.connect(self.show_prev_quote_action)
        next_quote_action.triggered.connect(self.show_next_quote_action) # Trigger next quote manually
        exit_action.triggered.connect(self.close_widget) # Use a specific close method

        contextMenu.addAction(prev_quote_action)
        contextMenu.addAction(next_quote_action)
        contextMenu.addAction(settings_action)
        contextMenu.addSeparator()
        contextMenu.addAction(exit_action)

        contextMenu.exec(self.mapToGlobal(position))
        
        # Re-enable hide timer if it was stopped and mouse isn't over widget
        if hide_timer_was_active and not self.is_mouse_over:
            self.hide_timer.start(500) # Resume auto-hide check

    @Slot()
    def show_prev_quote_action(self):
        """Gets and displays the previous quote immediately."""
        logger.debug("Manual 'Previous Quote' action triggered.")
        prev_quote = self.quote_manager.get_prev_quote()
        self.update_quote(prev_quote)

    @Slot()
    def show_next_quote_action(self):
        """Gets and displays the next quote immediately."""
        logger.debug("Manual 'Next Quote' action triggered.")
        next_quote = self.quote_manager.get_next_quote()
        self.update_quote(next_quote)
        # Optionally restart timer if needed, though usually not required for manual next
        # self.quote_timer.start() # Restarts with current interval

    @Slot()
    def open_settings_dialog(self):
        # Create dialog if it doesn't exist or reuse if desired (simpler to recreate)
        # Pass both config_manager and quote_manager
        self.settings_dialog = SettingsDialog(self.config_manager, self.quote_manager, self)
        self.settings_dialog.settings_applied.connect(self.handle_settings_applied)

        self.settings_dialog.show()
        self.settings_dialog.activateWindow() # Bring it to the front
        self.settings_dialog.raise_()

    @Slot(dict)
    def handle_settings_applied(self, updated_settings):
        """Slot to receive applied settings from the dialog."""
        logger.info(f"Received settings_applied signal: {updated_settings}")
        # Stop media player before potentially changing source or hiding widget
        if self.media_player and self.media_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
             self.media_player.stop()

        # 1. Apply visual settings immediately (will handle starting player if needed)
        self.apply_settings()

        # 2. Update timer interval
        new_interval_ms = updated_settings.get("interval_ms")
        if new_interval_ms is not None and new_interval_ms != self.quote_timer.get_interval():
            logger.info(f"Updating timer interval to {new_interval_ms} ms")
            self.quote_timer.set_interval(new_interval_ms)

        # 3. Reload quotes if CSV path changed
        new_csv_path = updated_settings.get("csv_path")
        # Check if the path actually changed from what the manager currently uses
        # This requires the quote_manager to expose its current path or reload logic
        # For simplicity, reload if the path in settings is different from the one used at launch
        # A better approach would be for QuoteManager to handle the reload.
        current_csv_path = self.quote_manager.csv_path # Assuming QuoteManager stores this
        if new_csv_path is not None and new_csv_path != current_csv_path:
             logger.info(f"CSV path changed to {new_csv_path}. Reloading quotes.")
             try:
                 self.quote_manager.load_quotes(new_csv_path)
                 self.show_next_quote_action() # Show a quote from the new list immediately
             except Exception as e:
                 logger.error(f"Failed to reload quotes from {new_csv_path}: {e}", exc_info=True)
                 QMessageBox.warning(self, "Quote Load Error", f"Failed to load quotes from:\n{new_csv_path}\n\nPlease check the path and file format.\nError: {e}")
                 # Optionally revert csv_path setting in config if load fails?

    @Slot()
    def close_widget(self):
        """Closes the widget cleanly."""
        logger.info("Close action triggered from context menu.")
        # Optional: Add confirmation dialog
        # reply = QMessageBox.question(self, 'Exit Widget', "Are you sure you want to exit?",
        #                            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        # if reply == QMessageBox.Yes:
        #     self.close() # Triggers closeEvent
        self.close()

    # --- Event Handlers ---
    def mousePressEvent(self, event):
        # Handle left-click drag OR right-click for context menu
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
        # Right-click is handled by customContextMenuRequested signal
        # elif event.button() == Qt.RightButton:
            # self.show_context_menu(event.pos())
            # event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            new_pos = event.globalPosition().toPoint() - self._drag_pos
            self.move(new_pos)
            event.accept()
        else:
             super().mouseMoveEvent(event)

    def enterEvent(self, event):
        """Handle mouse entering widget area."""
        self.is_mouse_over = True
        # Cancel any pending hide timer
        if self.hide_timer.isActive():
            self.hide_timer.stop()
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        """Handle mouse leaving widget area."""
        self.is_mouse_over = False
        # Start timer to auto-hide if in icon mode
        if self.icon_mode:
            self.hide_timer.start(500)  # Hide after 500ms if mouse doesn't return
        super().leaveEvent(event)
    
    def auto_hide_if_needed(self):
        """Hide the widget if mouse is still outside and we're in icon mode."""
        if not self.is_mouse_over and self.icon_mode:
            self.hide()
    
    def show_on_hover(self):
        """Show the widget (used when floating icon is hovered)."""
        if not self.isVisible():
            # Position next to the cursor but don't overlap it
            cursor_pos = QCursor.pos()
            
            # Get screen dimensions
            screen = QApplication.screenAt(cursor_pos)
            if not screen:
                screen = QApplication.primaryScreen()
            
            screen_rect = screen.availableGeometry()
            
            # Calculate desired position
            desired_x = cursor_pos.x() - self.width() - 20
            desired_y = cursor_pos.y() - (self.height() // 2)
            
            # Adjust if widget would go off screen edges
            # Left edge check
            if desired_x < screen_rect.left():
                desired_x = cursor_pos.x() + 20  # Place on right side of cursor instead
            
            # Right edge check (after potentially flipping to right side)
            if desired_x + self.width() > screen_rect.right():
                desired_x = screen_rect.right() - self.width()
            
            # Top edge check
            if desired_y < screen_rect.top():
                desired_y = screen_rect.top()
            
            # Bottom edge check
            if desired_y + self.height() > screen_rect.bottom():
                desired_y = screen_rect.bottom() - self.height()
            
            # Move to adjusted position
            self.move(desired_x, desired_y)
            self.show()
            self.raise_()
            self.activateWindow()
    
    def hide_on_leave(self):
        """Hide the widget when floating icon is left and mouse is not over widget."""
        if not self.is_mouse_over:
            self.hide()

    def closeEvent(self, event):
        logger.info("Widget close event triggered.")
        # Clean up settings dialog if it exists and is open
        if self.settings_dialog and self.settings_dialog.isVisible():
            self.settings_dialog.close()
        # Stop timer explicitly if needed (though app exit should handle it)
        if self.quote_timer and self.quote_timer.is_active():
            self.quote_timer.stop()
        if self.media_player:
            self.media_player.stop() # Stop playback
            self.media_player = None # Allow garbage collection

        # Save current window geometry to config - but only if not in icon mode
        if not self.icon_mode:
            geometry = self.frameGeometry()
            window_geometry = [geometry.x(), geometry.y(), geometry.width(), geometry.height()]
            self.config_manager.set_setting("window_geometry", window_geometry)
            self.config_manager.save_config()
        
        super().closeEvent(event)

    # --- Public Methods for Updates ---
    def update_quote(self, quote_data):
        """Updates the quote text and author label."""
        self.quote_label.setText(quote_data.get("quote", "Quote not found"))
        author = quote_data.get("author", "")
        is_known_author = author and author.lower() != "unknown"
        self.author_label.setText(f"- {author}" if is_known_author else "")
        self.author_label.setVisible(is_known_author)
        
        # If using multiple background images, cycle to the next one
        settings = self.config_manager.get_all_settings()
        if settings.get("background_type") == "image" and self.image_paths:
            # Move to the next image in the list
            self.current_image_index = (self.current_image_index + 1) % len(self.image_paths)
            image_path = self.image_paths[self.current_image_index]
            
            # Apply the new background image
            if os.path.isfile(image_path):
                image_mode = settings.get("image_mode", "Stretch")
                self._apply_background_image(image_path, image_mode)
            else:
                # If image file no longer exists, remove it from the list
                logger.warning(f"Background image not found: {image_path}. Removing from rotation.")
                self.image_paths.pop(self.current_image_index)
                if self.image_paths:  # If there are still images left
                    self.current_image_index = self.current_image_index % len(self.image_paths)
                    self._apply_background_image(self.image_paths[self.current_image_index], settings.get("image_mode", "Stretch"))
    
    def _apply_background_image(self, image_path, image_mode):
        """Helper method to apply a background image with the specified mode"""
        if not os.path.isfile(image_path):
            logger.warning(f"Background image not found: {image_path}")
            return
            
        # Make sure background widget is visible and video is hidden
        self.background_widget.setVisible(True)
        self.video_widget.setVisible(False)
        
        # Escape backslashes for CSS
        image_path_css = image_path.replace("\\", "/")
        
        # Reset image styles before applying new mode
        bg_stylesheet = "border-radius: 10px; background-color: transparent;" # Start fresh, keep shape
        
        if image_mode == "Stretch":
            # Use border-image for stretching
            bg_stylesheet += f' border-image: url("{image_path_css}") 0 0 0 0 stretch stretch;'
        elif image_mode == "Cover":
            # Use background- properties for cover
            bg_stylesheet += f' background-image: url("{image_path_css}");'
            bg_stylesheet += ' background-repeat: no-repeat;'
            bg_stylesheet += ' background-position: center;'
            bg_stylesheet += ' background-size: cover;'
        elif image_mode == "Contain":
            # Use background- properties for contain
            bg_stylesheet += f' background-image: url("{image_path_css}");'
            bg_stylesheet += ' background-repeat: no-repeat;'
            bg_stylesheet += ' background-position: center;'
            bg_stylesheet += ' background-size: contain;'
        else: # Default to stretch if mode is unknown
            bg_stylesheet += f' border-image: url("{image_path_css}") 0 0 0 0 stretch stretch;'
            
        # Apply the stylesheet
        self.background_widget.setStyleSheet(bg_stylesheet)

    def apply_settings(self):
        """Applies settings from ConfigManager to the widget."""
        logger.debug("Applying settings...")
        settings = self.config_manager.get_all_settings()

        # --- Window Behavior ---
        always_on_top = settings.get("always_on_top", False)
        if always_on_top:
            self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
        else:
            self.setWindowFlags(self.windowFlags() & ~Qt.WindowStaysOnTopHint)
        self.show() # Re-show to apply window flag changes

        # --- Restore Geometry ---
        geometry = settings.get("window_geometry")
        if geometry:
            try:
                self.restoreGeometry(bytes.fromhex(geometry))
            except Exception as e:
                logger.warning(f"Failed to restore geometry: {e}")

        # --- Text Appearance ---
        text_color_hex = settings.get("text_color", "#FFFFFF") # Default white
        font_family = settings.get("font_family", "Arial")
        font_size = settings.get("font_size", 14)
        text_color = QColor(text_color_hex)
        font = QFont(font_family, font_size)

        # Apply to quote and author labels with background shade
        text_base_style = f"color: {text_color_hex};" \
                          f"background-color: rgba(0, 0, 0, 0.5);" \
                          f"border-radius: 5px;" \
                          f"padding: 5px;" 
                          
        self.quote_label.setFont(font)
        self.quote_label.setStyleSheet(text_base_style)
        self.author_label.setFont(font)
        # Add specific alignment style for author
        self.author_label.setStyleSheet(text_base_style + " padding-top: 0px; padding-bottom: 2px; margin-top: 5px;")

        # Apply styling to navigation buttons for better visibility
        # Use a higher contrast background with the same text color
        button_style = f"""
            background-color: rgba(40, 40, 40, 0.5); 
            border: none; 
            border-radius: 18px; 
            padding: 6px;
            color: {text_color_hex};
        """
        self.prev_button.setStyleSheet(button_style)
        self.next_button.setStyleSheet(button_style)
        
        # Re-set icons with proper coloring
        self.prev_button.setIcon(QIcon(self.style().standardPixmap(QStyle.StandardPixmap.SP_MediaSkipBackward)))
        self.next_button.setIcon(QIcon(self.style().standardPixmap(QStyle.StandardPixmap.SP_MediaSkipForward)))

        # --- Background Appearance (Applied to background_widget) ---
        bg_type = settings.get("background_type", "color")
        bg_value = settings.get("background_value", "#333333") # Default dark grey

        # Stop any existing media playback before changing background
        if self.media_player and self.media_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.media_player.stop()

        self.video_widget.setVisible(False) # Hide video by default
        self.main_layout.setCurrentWidget(self.text_container_widget) # Ensure text is top visible layer

        # Make the dedicated background widget visible and apply styles
        self.background_widget.setVisible(True)
        bg_stylesheet = "border-radius: 10px;" # Base style with rounded corners

        if bg_type == "color":
            bg_color = QColor(bg_value)
            if not bg_color.isValid():
                logger.warning(f"Invalid background color value: {bg_value}. Using default.")
                bg_color = QColor("#333333")
                self.config_manager.set_setting("background_value", "#333333") # Fix config
            bg_stylesheet += f" background-color: {bg_color.name()};"
            
            # Clear image paths since we're not using images
            self.image_paths = []

        elif bg_type == "image":
            # Load image paths from settings
            self.image_paths = settings.get("image_paths", [])
            if not self.image_paths and bg_value:
                # If no image paths but we have a main image, add it to the list
                self.image_paths.append(bg_value)
                
            # Filter out non-existent image paths
            self.image_paths = [path for path in self.image_paths if os.path.isfile(path)]
                
            # Reset image index
            self.current_image_index = 0
            
            # Apply the first image if available
            image_mode = settings.get("image_mode", "Stretch")
            if self.image_paths:
                self._apply_background_image(self.image_paths[0], image_mode)
            elif os.path.isfile(bg_value):
                # If no valid images in paths but main image exists, use it
                self._apply_background_image(bg_value, image_mode)
            else:
                logger.warning(f"Background image not found: {bg_value}. Using default color.")
                bg_stylesheet += " background-color: #333333;"
                # Inform user and revert settings
                if self.isVisible(): # Only show message box if widget is actually visible
                    QMessageBox.warning(self, "Image Load Error", f"Failed to load background image:\n{bg_value}\n\nReverting to default color.")
                self.config_manager.set_setting("background_type", "color")
                self.config_manager.set_setting("background_value", "#333333")

        elif bg_type == "video":
            video_path = bg_value
            if os.path.isfile(video_path):
                logger.info(f"Setting video source to: {video_path}")
                self.media_player.setSource(QUrl.fromLocalFile(video_path))
                if self.media_player.error() == QMediaPlayer.Error.NoError:
                    self.video_widget.setVisible(True)
                    # Ensure video widget is stacked correctly (below text, above background color/image)
                    self.main_layout.setCurrentWidget(self.video_widget)
                    self.main_layout.addWidget(self.text_container_widget) # Ensure text is added again on top
                    self.main_layout.setCurrentWidget(self.text_container_widget) # Activate text layer

                    self.media_player.play()
                    # Hide the static background widget if video plays
                    self.background_widget.setVisible(False)
                    bg_stylesheet = "border-radius: 10px; background-color: transparent;" # Keep shape, hide bg
                else:
                     # Error handled by _handle_media_error slot
                    logger.warning("Error occurred immediately after setting video source.")
                    bg_stylesheet += " background-color: #333333;" # Fallback color
                    self.background_widget.setVisible(True)
            else:
                logger.warning(f"Background video not found: {video_path}. Using default color.")
                bg_stylesheet += " background-color: #333333;"
                if self.isVisible():
                    QMessageBox.warning(self, "Video Load Error", f"Failed to load background video:\n{video_path}\n\nReverting to default color.")
                self.config_manager.set_setting("background_type", "color")
                self.config_manager.set_setting("background_value", "#333333")
                self.background_widget.setVisible(True)
                
            # Clear image paths since we're not using images
            self.image_paths = []

        # Apply the final stylesheet to the background widget (if not already applied by _apply_background_image)
        if bg_type != "image" or not self.image_paths:
            self.background_widget.setStyleSheet(bg_stylesheet)

        # Ensure the main widget itself remains transparent
        self.setStyleSheet("background: transparent;")

        logger.debug("Settings applied.")

    @Slot(QMediaPlayer.Error, str)
    def _handle_media_error(self, error, error_string):
        """Logs media player errors and shows a message to the user."""
        logger.error(f"Media player error: {error} ({error_string})")
        # Show message to user
        QMessageBox.warning(self, "Media Playback Error", 
                            f"Could not play the background video.\n\nError: {error_string}")
        # Fallback to default background
        self.video_widget.setVisible(False)
        self.setAutoFillBackground(True)
        palette = self.palette()
        palette.setColor(QPalette.Window, QColor(30, 30, 30, 230))
        self.setPalette(palette)

# --- Standalone Test --- 
if __name__ == '__main__':
    # Need dummy versions of all required managers
    class DummyManager:
        def __init__(self):
            self._settings = {
                "always_on_top": True,
                "background_type": "color",
                "background_value": "#334455AA", # Added alpha
                "text_color": "#EEEEEE",
                "interval_ms": 5000,
                "csv_path": "dummy_quotes.csv"
            }
            self.settings = self._settings.copy()
            self.csv_path = self._settings["csv_path"] # For checking path change

        def get_setting(self, key, default=None):
            return self.settings.get(key, default)
        def get_all_settings(self):
             return self.settings.copy()
        def save_config(self): print("Dummy Save")
        def set_setting(self, key, value): self.settings[key] = value
        # Dummy QuoteManager methods
        def get_next_quote(self): return {"quote": "Dummy quote for testing.", "author": "Dummy"}
        def get_prev_quote(self): return {"quote": "Previous dummy quote.", "author": "Dummy"}
        def load_quotes(self, path): print(f"Dummy Load Quotes: {path}"); self.csv_path = path
        # Dummy Timer methods
        def get_interval(self): return self.settings["interval_ms"]
        def set_interval(self, ms): print(f"Dummy Set Interval: {ms}"); self.settings["interval_ms"] = ms
        def start(self): print("Dummy Timer Start")
        def stop(self): print("Dummy Timer Stop")
        def is_active(self): return True

    app = QApplication(sys.argv)
    dummy_manager = DummyManager()
    widget = MotivationalWidget(config_manager=dummy_manager,
                                quote_manager=dummy_manager,
                                quote_timer=dummy_manager)
    widget.show()
    sys.exit(app.exec()) 