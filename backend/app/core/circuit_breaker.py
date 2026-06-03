import time
import logging
from threading import Lock

logger = logging.getLogger(__name__)

class CircuitBreaker:
    def __init__(self, name: str, failure_threshold: int = 5, recovery_timeout: float = 60.0):
        self.name = name
        self._failures = 0
        self._last_failure = 0.0
        self._threshold = failure_threshold
        self._recovery_timeout = recovery_timeout
        self._lock = Lock()
        self._state = "CLOSED"  # CLOSED, OPEN, HALF-OPEN

    @property
    def is_open(self) -> bool:
        with self._lock:
            now = time.monotonic()
            if self._failures >= self._threshold:
                if now - self._last_failure > self._recovery_timeout:
                    if self._state != "HALF-OPEN":
                        logger.warning(
                            "circuit_breaker_state_transition: name=%s, old_state=%s, new_state=HALF-OPEN, reason=recovery_timeout_expired",
                            self.name, self._state
                        )
                        self._state = "HALF-OPEN"
                    return False
                if self._state != "OPEN":
                    logger.warning(
                        "circuit_breaker_state_transition: name=%s, old_state=%s, new_state=OPEN, reason=threshold_exceeded",
                        self.name, self._state
                    )
                    self._state = "OPEN"
                return True
            if self._state != "CLOSED":
                logger.info(
                    "circuit_breaker_state_transition: name=%s, old_state=%s, new_state=CLOSED, reason=failures_reset",
                    self.name, self._state
                )
                self._state = "CLOSED"
            return False

    def record_failure(self):
        with self._lock:
            self._failures += 1
            self._last_failure = time.monotonic()
            logger.warning(
                "circuit_breaker_failure_recorded: name=%s, failures=%d, threshold=%d",
                self.name, self._failures, self._threshold
            )

    def record_success(self):
        with self._lock:
            if self._failures > 0:
                logger.info(
                    "circuit_breaker_success_reset: name=%s, previous_failures=%d",
                    self.name, self._failures
                )
            self._failures = 0
            self._state = "CLOSED"

gemini_breaker = CircuitBreaker(name="gemini_embedding", failure_threshold=5, recovery_timeout=60.0)
