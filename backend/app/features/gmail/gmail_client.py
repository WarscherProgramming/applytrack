"""Gmail data access behind an abstraction.

`GmailClient` is the seam every consumer codes against. Two implementations:
  - FakeGmailClient: seeds realistic job emails; used in simulation mode so the
    whole pipeline works locally with no Google account.
  - GoogleGmailClient: real Gmail REST access via httpx.

`get_gmail_client` picks the implementation from configuration, so swapping in
the real client (or a future provider) never touches the service or matcher.
"""

import base64
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

import httpx

from app.core.config import settings

GMAIL_API_BASE = "https://gmail.googleapis.com/gmail/v1/users/me"


@dataclass
class RawEmail:
    """Provider-agnostic email shape consumed by the matcher and service."""

    message_id: str
    thread_id: str
    subject: str | None
    sender: str
    sender_name: str | None
    recipients: list[str]
    sent_at: datetime
    body_preview: str | None
    direction: str  # 'inbound' | 'outbound'
    labels: list[str] = field(default_factory=list)
    attachments: list[dict] = field(default_factory=list)


class GmailClient(ABC):
    @abstractmethod
    def fetch_profile_email(self) -> str:
        """The connected account's email address."""

    @abstractmethod
    def fetch_messages(self, *, max_results: int = 50) -> list[RawEmail]:
        """Recent Inbox + Sent messages."""


# ---------------------------------------------------------------------------
# Fake client — simulation mode
# ---------------------------------------------------------------------------


def _ago(days: int, hour: int = 9) -> datetime:
    base = datetime.now(timezone.utc) - timedelta(days=days)
    return base.replace(hour=hour, minute=0, second=0, microsecond=0)


class FakeGmailClient(GmailClient):
    """Returns a fixed, realistic set of job-search emails spanning known
    companies, a recruiter, interview scheduling, an offer, and a rejection."""

    ACCOUNT_EMAIL = "jobseeker@gmail.com"

    def fetch_profile_email(self) -> str:
        return self.ACCOUNT_EMAIL

    def fetch_messages(self, *, max_results: int = 50) -> list[RawEmail]:
        me = self.ACCOUNT_EMAIL
        samples: list[RawEmail] = [
            RawEmail(
                message_id="sim-amazon-1",
                thread_id="thread-amazon",
                subject="Your application to Amazon — Software Development Engineer",
                sender="careers@amazon.com",
                sender_name="Amazon Recruiting",
                recipients=[me],
                sent_at=_ago(20),
                body_preview="Thank you for applying to the SDE role. Our team is reviewing your application.",
                direction="inbound",
                labels=["INBOX"],
            ),
            RawEmail(
                message_id="sim-recruiter-1",
                thread_id="thread-stripe",
                subject="Stripe — Backend Engineer opportunity",
                sender="jane.recruiter@stripe.com",
                sender_name="Jane Recruiter",
                recipients=[me],
                sent_at=_ago(14),
                body_preview="Hi! I'd love to chat about a Backend Engineer role on our payments team.",
                direction="inbound",
                labels=["INBOX"],
            ),
            RawEmail(
                message_id="sim-reply-1",
                thread_id="thread-stripe",
                subject="Re: Stripe — Backend Engineer opportunity",
                sender=me,
                sender_name="Job Seeker",
                recipients=["jane.recruiter@stripe.com"],
                sent_at=_ago(13),
                body_preview="Thanks Jane — I'm very interested. I'm available this week for a call.",
                direction="outbound",
                labels=["SENT"],
            ),
            RawEmail(
                message_id="sim-interview-1",
                thread_id="thread-stripe",
                subject="Stripe interview scheduled — Technical Screen",
                sender="scheduling@stripe.com",
                sender_name="Stripe Scheduling",
                recipients=[me],
                sent_at=_ago(9),
                body_preview="Your technical interview is confirmed. Meeting link enclosed.",
                direction="inbound",
                labels=["INBOX"],
                attachments=[
                    {"filename": "interview-prep.pdf", "mime_type": "application/pdf", "size": 84213}
                ],
            ),
            RawEmail(
                message_id="sim-google-1",
                thread_id="thread-google",
                subject="Google — Recruiter follow up",
                sender="recruiting@google.com",
                sender_name="Google Recruiting",
                recipients=[me],
                sent_at=_ago(6),
                body_preview="Following up regarding your interest in the L4 SWE position.",
                direction="inbound",
                labels=["INBOX"],
            ),
            RawEmail(
                message_id="sim-offer-1",
                thread_id="thread-stripe",
                subject="Stripe — Offer of Employment",
                sender="offers@stripe.com",
                sender_name="Stripe Talent",
                recipients=[me],
                sent_at=_ago(2),
                body_preview="Congratulations! We are pleased to extend an offer for the Backend Engineer role.",
                direction="inbound",
                labels=["INBOX"],
                attachments=[
                    {"filename": "offer-letter.pdf", "mime_type": "application/pdf", "size": 120544}
                ],
            ),
            RawEmail(
                message_id="sim-reject-1",
                thread_id="thread-amazon",
                subject="Update on your Amazon application",
                sender="no-reply@amazon.com",
                sender_name="Amazon Recruiting",
                recipients=[me],
                sent_at=_ago(1),
                body_preview="Thank you for your interest. We have decided to move forward with other candidates.",
                direction="inbound",
                labels=["INBOX"],
            ),
        ]
        return samples[:max_results]


# ---------------------------------------------------------------------------
# Real client — Gmail REST via httpx
# ---------------------------------------------------------------------------


class GoogleGmailClient(GmailClient):
    def __init__(self, access_token: str) -> None:
        self._headers = {"Authorization": f"Bearer {access_token}"}

    def fetch_profile_email(self) -> str:
        resp = httpx.get(
            f"{GMAIL_API_BASE}/profile", headers=self._headers, timeout=15
        )
        resp.raise_for_status()
        return resp.json()["emailAddress"]

    def fetch_messages(self, *, max_results: int = 50) -> list[RawEmail]:
        # Restrict to Inbox + Sent per the import policy.
        listing = httpx.get(
            f"{GMAIL_API_BASE}/messages",
            headers=self._headers,
            params={"q": "in:inbox OR in:sent", "maxResults": max_results},
            timeout=20,
        )
        listing.raise_for_status()
        ids = [m["id"] for m in listing.json().get("messages", [])]

        emails: list[RawEmail] = []
        for message_id in ids:
            detail = httpx.get(
                f"{GMAIL_API_BASE}/messages/{message_id}",
                headers=self._headers,
                params={"format": "full"},
                timeout=20,
            )
            detail.raise_for_status()
            emails.append(self._parse(detail.json()))
        return emails

    @staticmethod
    def _parse(payload: dict) -> RawEmail:
        headers = {
            h["name"].lower(): h["value"]
            for h in payload.get("payload", {}).get("headers", [])
        }
        label_ids = payload.get("labelIds", [])
        sender_raw = headers.get("from", "")
        sender_name, sender_email = _split_address(sender_raw)
        internal_ms = int(payload.get("internalDate", "0"))
        return RawEmail(
            message_id=payload["id"],
            thread_id=payload.get("threadId", payload["id"]),
            subject=headers.get("subject"),
            sender=sender_email,
            sender_name=sender_name,
            recipients=_split_recipients(headers.get("to", "")),
            sent_at=datetime.fromtimestamp(internal_ms / 1000, tz=timezone.utc),
            body_preview=payload.get("snippet"),
            direction="outbound" if "SENT" in label_ids else "inbound",
            labels=label_ids,
            attachments=_extract_attachments(payload.get("payload", {})),
        )


def _split_address(raw: str) -> tuple[str | None, str]:
    """'Jane Doe <jane@x.com>' → ('Jane Doe', 'jane@x.com')."""
    raw = raw.strip()
    if "<" in raw and ">" in raw:
        name = raw[: raw.index("<")].strip().strip('"') or None
        email = raw[raw.index("<") + 1 : raw.index(">")].strip().lower()
        return name, email
    return None, raw.lower()


def _split_recipients(raw: str) -> list[str]:
    return [_split_address(part)[1] for part in raw.split(",") if part.strip()]


def _extract_attachments(part: dict) -> list[dict]:
    out: list[dict] = []
    filename = part.get("filename")
    body = part.get("body", {})
    if filename:
        out.append(
            {
                "filename": filename,
                "mime_type": part.get("mimeType"),
                "size": body.get("size", 0),
            }
        )
    for sub in part.get("parts", []) or []:
        out.extend(_extract_attachments(sub))
    return out


# Keep import-time analysers from flagging the helper as unused.
_ = base64


def get_gmail_client(access_token: str | None) -> GmailClient:
    """Pick the client implementation from configuration."""
    if settings.gmail_simulation or not access_token:
        return FakeGmailClient()
    return GoogleGmailClient(access_token)
