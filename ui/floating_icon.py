import sys
import os
import logging
from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout, QApplication
from PySide6.QtCore import Qt, QPoint, QSize, QTimer, Signal, QEvent
from PySide6.QtGui import QColor, QFont, QPalette, QIcon, QPixmap, QCursor

logger = logging.getLogger(__name__)

class FloatingIconWidget(QWidget):
    """A small floating widget with an icon that shows the main widget on hover."""
    
    # Signal to notify when the icon is hovered
    icon_hovered = Signal()
    icon_left = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Window properties
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Tool | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAutoFillBackground(False)
        self.setStyleSheet("background: transparent;")
        
        # Fixed size for the icon - slightly larger for better visibility
        self.setFixedSize(56, 56)
        
        # Default position - right side of screen
        desktop = QApplication.primaryScreen().geometry()
        self.move(desktop.width() - self.width() - 20, desktop.height() // 2 - 50)
        
        self.initUI()
        
        # Track mouse position and hover state
        self.setMouseTracking(True)
        self.hover_timer = QTimer(self)
        self.hover_timer.setSingleShot(True)
        self.hover_timer.timeout.connect(self._on_hover_timeout)
        self.is_hovered = False
        
        # For dragging
        self._drag_pos = QPoint()
        
    def initUI(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Create icon label
        self.icon_label = QLabel(self)
        self.icon_label.setAlignment(Qt.AlignCenter)
        
        # Try to load buddha.png from assets directory
        buddha_path = self._find_buddha_icon()
        
        if buddha_path and os.path.exists(buddha_path):
            pixmap = QPixmap(buddha_path)
            if not pixmap.isNull():
                # Scale the pixmap to fit our icon size while preserving aspect ratio
                pixmap = pixmap.scaled(44, 44, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.icon_label.setPixmap(pixmap)
                logger.info(f"Successfully loaded buddha.png from {buddha_path}")
            else:
                logger.warning(f"Failed to load buddha.png from {buddha_path}")
                self._set_fallback_icon()
        else:
            logger.warning(f"Buddha icon not found at {buddha_path}")
            self._set_fallback_icon()
        
        # Add a circular background with soft glow effect for better visibility
        
        
        layout.addWidget(self.icon_label)
        
        # Set tooltip
        self.setToolTip("Hover to show motivational quote")
    
    def _find_buddha_icon(self):
        """Attempt to find the buddha.png file in various locations."""
        # Try several possible paths
        possible_paths = [
            # Direct path from current directory
            os.path.join("assets", "buddha.png"),
            # Path relative to application directory
            os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "buddha.png"),
            # Path for packaged app
            os.path.join(os.path.dirname(sys.executable), "assets", "buddha.png"),
            # Path relative to motivator package
            os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "buddha.png"),
        ]
        
        # Check each possible path
        for path in possible_paths:
            if os.path.exists(path):
                return path
        
        return None
    
    def _set_fallback_icon(self):
        """Use system icons if buddha.png cannot be loaded."""
        # Use a quote icon or any other appropriate icon from system
        icon = QIcon.fromTheme("accessories-dictionary") # Fallback to system theme icon
        
        # If system theme icon is not available, try Qt standard icons
        if icon.isNull():
            from PySide6.QtWidgets import QStyle
            icon = self.style().standardIcon(QStyle.SP_MessageBoxInformation)
        
        pixmap = icon.pixmap(QSize(32, 32))
        self.icon_label.setPixmap(pixmap)
        
    def enterEvent(self, event):
        """Handle mouse entering the widget area."""
        self.is_hovered = True
        self.hover_timer.start(300)  # Small delay before showing to avoid accidental triggers
        super().enterEvent(event)
        
    def leaveEvent(self, event):
        """Handle mouse leaving the widget area."""
        self.is_hovered = False
        self.hover_timer.stop()
        
        # Signal that we left the icon - delay to allow moving to the main widget
        QTimer.singleShot(300, self._check_if_still_left)
        super().leaveEvent(event)
    
    def _check_if_still_left(self):
        """Check if we're still outside to avoid flickering."""
        if not self.is_hovered:
            self.icon_left.emit()
    
    def _on_hover_timeout(self):
        """Emit signal when hover timeout occurs."""
        if self.is_hovered:
            self.icon_hovered.emit()
    
    def mousePressEvent(self, event):
        """Enable dragging the floating icon."""
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
        else:
            super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        """Move the widget with drag."""
        if event.buttons() == Qt.LeftButton:
            # Calculate new position
            new_pos = event.globalPosition().toPoint() - self._drag_pos
            
            # Get screen dimensions
            screen = QApplication.screenAt(event.globalPosition().toPoint())
            if not screen:
                screen = QApplication.primaryScreen()
            
            screen_rect = screen.availableGeometry()
            
            # Ensure the widget stays within screen boundaries
            # Left edge
            if new_pos.x() < screen_rect.left():
                new_pos.setX(screen_rect.left())
            
            # Right edge (accounting for widget width)
            if new_pos.x() + self.width() > screen_rect.right():
                new_pos.setX(screen_rect.right() - self.width())
            
            # Top edge
            if new_pos.y() < screen_rect.top():
                new_pos.setY(screen_rect.top())
            
            # Bottom edge (accounting for widget height)
            if new_pos.y() + self.height() > screen_rect.bottom():
                new_pos.setY(screen_rect.bottom() - self.height())
            
            self.move(new_pos)
            event.accept()
        else:
            super().mouseMoveEvent(event) 