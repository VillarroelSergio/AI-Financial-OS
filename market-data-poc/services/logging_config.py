import logging


class _DefaultsFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        for field in ("provider", "endpoint", "latency_ms", "success", "error", "fallback_used"):
            if not hasattr(record, field):
                setattr(record, field, "")
        return True


def configure_logging(level: int = logging.INFO) -> None:
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s %(message)s provider=%(provider)s endpoint=%(endpoint)s latency_ms=%(latency_ms)s result=%(success)s error=%(error)s fallback_used=%(fallback_used)s",
    )
    logging.getLogger().addFilter(_DefaultsFilter())
