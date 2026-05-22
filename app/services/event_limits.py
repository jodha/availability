class EventLimitError(Exception):
    pass


def ensure_event_count_allowed(count: int, maximum: int) -> None:
    if count > maximum:
        raise EventLimitError(f"Poll cannot have more than {maximum} events")
