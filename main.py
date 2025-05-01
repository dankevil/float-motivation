import sys
import os
import logging
from PySide6.QtWidgets import QApplication, QMenu
from PySide6.QtCore import QCoreApplication, Slot, QPoint
from PySide6.QtGui import QAction

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Ensure the motivator package can be found
# This might be needed if running main.py directly from the root folder
# instead of installing the package.
try:
    from core.quote_manager import QuoteManager
    from core.timer import QuoteTimer
    from ui.widget import MotivationalWidget
    from ui.floating_icon import FloatingIconWidget
    from core.config_manager import ConfigManager
except ImportError:
    # If running from root, add motivator to path (adjust if structure differs)
    PACKAGE_PARENT = '..'
    SCRIPT_DIR = os.path.dirname(os.path.realpath(os.path.join(os.getcwd(), os.path.expanduser(__file__))))
    parent_dir = os.path.normpath(os.path.join(SCRIPT_DIR, PACKAGE_PARENT))
    if parent_dir not in sys.path:
         sys.path.append(os.path.dirname(SCRIPT_DIR)) # Add the directory containing 'motivator'
    logger.info(f"Adjusted sys.path: {sys.path}")
    try:
        from motivator.core.quote_manager import QuoteManager
        from motivator.core.timer import QuoteTimer
        from motivator.ui.widget import MotivationalWidget
        from motivator.ui.floating_icon import FloatingIconWidget
        from motivator.core.config_manager import ConfigManager
    except ImportError as e:
        logger.error(f"Failed to import modules even after path adjustment: {e}")
        sys.exit(1)

# --- Constants ---
# Moved default paths/intervals to ConfigManager defaults

def save_window_geometry(widget, config_manager):
    """Saves the window's current geometry to the config."""
    # Check if widget is still valid before accessing geometry
    if widget and not widget.isWindow():
        # It might have been closed already during shutdown
        logger.warning("Widget seems closed, skipping geometry save.")
        return
    try:
        geometry = widget.geometry()
        config_manager.set_setting("window_geometry", [
            geometry.x(), geometry.y(), geometry.width(), geometry.height()
        ])
        config_manager.save_config() # Save immediately on close
        logger.info(f"Saved window geometry: {config_manager.get_setting('window_geometry')}")
    except RuntimeError as e:
         logger.error(f"Error saving geometry, widget likely deleted: {e}")

def main():
    logger.info("Starting Motivational Widget Application...")
    # Set Organization and Application Name for QSettings compatibility if needed later
    QCoreApplication.setOrganizationName("YourAppNameOrAuthor")
    QCoreApplication.setApplicationName("MotivationalWidget")

    app = QApplication(sys.argv)

    # --- Initialize Config Manager ---
    config_manager = ConfigManager()
    app_settings = config_manager.get_all_settings()
    
    # --- Check for icon mode setting ---
    use_icon_mode = app_settings.get("use_icon_mode", True)  # Default to icon mode

    # --- Get settings ---
    csv_path = app_settings.get("csv_path")
    interval_ms = app_settings.get("interval_ms")

    # --- Create Dummy CSV if the configured one doesn't exist ---
    if not os.path.exists(csv_path) and csv_path == config_manager._get_default_settings()["csv_path"]:
        logger.warning(f"Default CSV '{csv_path}' not found. Creating a dummy file.")
        try:
            import csv
            with open(csv_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f, delimiter=';')
                writer.writerow(["Welcome to the Motivational Widget!", "System"])
                writer.writerow(["Configure your quotes via the settings.", "System"])
                writer.writerow(["The journey of a thousand miles begins with one step.", "Lao Tzu"])
        except Exception as e:
            logger.error(f"Failed to create dummy CSV: {e}")
            # Reset to a known non-functional state or alert user
            config_manager.set_setting("csv_path", "error_creating_dummy.csv")

    # --- Initialize Core Components ---
    logger.info(f"Loading quotes from: {csv_path}")
    quote_manager = QuoteManager(csv_path=csv_path)

    logger.info(f"Initializing timer with interval: {interval_ms}ms")
    quote_timer = QuoteTimer()

    # --- Initialize UI ---
    logger.info("Initializing UI Widget and Floating Icon...")
    
    # Create the main widget
    widget = MotivationalWidget(
        config_manager=config_manager,
        quote_manager=quote_manager,
        quote_timer=quote_timer,
        icon_mode=use_icon_mode
    )

    # Create the floating icon widget if using icon mode
    floating_icon = None
    if use_icon_mode:
        floating_icon = FloatingIconWidget()
        
        # Connect signals between floating icon and main widget
        floating_icon.icon_hovered.connect(widget.show_on_hover)
        floating_icon.icon_left.connect(widget.hide_on_leave)

    # --- Restore Window Geometry ---
    saved_geometry = app_settings.get("window_geometry")
    if isinstance(saved_geometry, list) and len(saved_geometry) == 4:
        logger.info(f"Restoring window geometry: {saved_geometry}")
        widget.setGeometry(*saved_geometry) # Unpack list [x, y, w, h]
    else:
        logger.info("No saved window geometry found or invalid format, using default.")
        # Optional: Center window on first launch if no geometry saved
        # screen_geometry = QApplication.primaryScreen().availableGeometry()
        # widget.move(screen_geometry.center() - widget.rect().center())

    # --- Connect Signals and Slots ---
    @Slot()
    def show_next_quote():
        logger.debug("Timer timeout signal received, getting next quote.")
        next_quote = quote_manager.get_next_quote()
        widget.update_quote(next_quote)

    quote_timer.timeout.connect(show_next_quote)

    # Connect application's aboutToQuit signal to save geometry
    app.aboutToQuit.connect(lambda: save_window_geometry(widget, config_manager))

    # --- Initial Setup ---
    show_next_quote()  # Show the first quote immediately
    
    # Show the appropriate interface based on mode
    if use_icon_mode:
        floating_icon.show()
        # Widget will be shown when icon is hovered
    else:
        widget.show()  # Show the widget directly if not in icon mode
        
    quote_timer.start(interval_ms)

    logger.info("Application started. Entering main event loop.")
    exit_code = app.exec()
    logger.info(f"Application finished with exit code: {exit_code}")
    sys.exit(exit_code)

if __name__ == '__main__':
    main() 