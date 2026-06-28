from datetime import UTC, datetime

from app.features.calendar_integration.schemas import CalendarEventPayload


def export_ics(events: list[CalendarEventPayload]) -> str:
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//ApplyTrack//Calendar Integration//EN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
    ]
    for event in events:
        lines.extend(_event_lines(event))
    lines.append("END:VCALENDAR")
    return "\r\n".join(lines) + "\r\n"


def _event_lines(event: CalendarEventPayload) -> list[str]:
    uid = f"{event.item_type.value}-{event.item_id}@applytrack.local"
    rows = [
        "BEGIN:VEVENT",
        f"UID:{_escape(uid)}",
        f"DTSTAMP:{_stamp(datetime.now(UTC))}",
        f"DTSTART:{_stamp(event.start_at)}",
        f"DTEND:{_stamp(event.end_at)}",
        f"SUMMARY:{_escape(event.title)}",
        (
            "STATUS:CANCELLED"
            if event.status in {"cancelled", "completed", "skipped"}
            else "STATUS:CONFIRMED"
        ),
    ]
    if event.description:
        rows.append(f"DESCRIPTION:{_escape(event.description)}")
    if event.location:
        rows.append(f"LOCATION:{_escape(event.location)}")
    rows.append("END:VEVENT")
    return rows


def _stamp(value: datetime) -> str:
    utc = value.astimezone(UTC) if value.tzinfo else value.replace(tzinfo=UTC)
    return utc.strftime("%Y%m%dT%H%M%SZ")


def _escape(value: str) -> str:
    return (
        value.replace("\\", "\\\\")
        .replace("\n", "\\n")
        .replace(",", "\\,")
        .replace(";", "\\;")
    )
