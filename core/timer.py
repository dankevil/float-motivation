from PySide6.QtCore import QObject, QTimer, Signal
import logging

logger = logging.getLogger(__name__)

class QuoteTimer(QObject):
    timeout = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._timer = QTimer(self)
        self._timer.timeout.connect(self.timeout.emit)
        self._interval_ms = 10000 # Default interval: 10 seconds

    def start(self, interval_ms=None):
        """Starts the timer with the specified interval in milliseconds."""
        if interval_ms is not None:
            self.set_interval(interval_ms)

        if self._interval_ms > 0:
            self._timer.start(self._interval_ms)
            logger.info(f"Timer started with interval {self._interval_ms} ms.")
        else:
             logger.warning("Timer interval is zero or negative, timer not started.")

    def stop(self):
        """Stops the timer."""
        self._timer.stop()
        logger.info("Timer stopped.")

    def set_interval(self, interval_ms):
        """Sets the timer interval in milliseconds."""
        self._interval_ms = max(100, int(interval_ms)) # Ensure minimum interval (e.g., 100ms)
        logger.info(f"Timer interval set to {self._interval_ms} ms.")
        if self._timer.isActive():
            # Restart timer with new interval if it's already running
            self.stop()
            self.start()

    def get_interval(self):
        """Returns the current interval in milliseconds."""
        return self._interval_ms

    def is_active(self):
        """Returns True if the timer is currently running."""
        return self._timer.isActive() 