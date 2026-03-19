import logging
from collections import deque
from typing import List

class LogBufferHandler(logging.Handler):
    """
    [Ω-AUDIT] Custom Log Handler that keeps the last N lines in a thread-safe buffer.
    Allows the AuditEngine to dump context for specific trades.
    """
    def __init__(self, capacity: int = 1000):
        super().__init__()
        self.buffer = deque(maxlen=capacity)
        self.formatter = logging.Formatter(
            '[DubaiMatrixASI] %(asctime)s.%(msecs)03d %(levelname)8s │ %(message)s',
            datefmt='%H:%M:%S'
        )

    def emit(self, record):
        try:
            msg = self.format(record)
            self.buffer.append(msg)
        except Exception:
            self.handleError(record)

    def get_logs(self) -> List[str]:
        return list(self.buffer)

    def clear(self):
        self.buffer.clear()

# Global Buffer Instance
LOG_BUFFER = LogBufferHandler(capacity=10000)
