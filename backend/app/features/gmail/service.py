import logging
import secrets
from datetime import datetime, timezone
from urllib.parse import urlparse
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.exceptions.http import ValidationError
from app.features.applications.model import JobApplication
from app.features.companies.model import Company
from app.features.gmail import oauth
from app.features.gmail.email_matcher import (
    ApplicationRef,
    CompanyRef,
    InterviewRef,
    MatchContext,
    RecruiterRef,
    is_recruiting_email,
    match_email,
)
from app.features.gmail.gmail_client import RawEmail, get_gmail_client
from app.features.gmail.models import EmailMessage, GmailAccount
from app.features.gmail.repository import (
    EmailMessageRepository,
    GmailAccountRepository,
)
from app.features.gmail.token_crypto import decrypt_token, encrypt_token
from app.features.interviews.model import Interview
from app.features.recruiters.model import Recruiter

logger = logging.getLogger(__name__)

_OFFER_HINTS = ("offer",)
_REJECTION_HINTS = ("reject", "unfortunately", "other candidates", "not moving forward")


def _domain_from_website(website: str | None) -> str | None:
    if not website:
        return None
    parsed = urlparse(website if "//" in website else f"//{website}")
    host = (parsed.netloc or parsed.path).strip().lower()
    return host[4:] if host.startswith("www.") else host or None


class GmailService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.accounts = GmailAccountRepository(db)
        self.emails = EmailMessageRepository(db)

    # -- Status ------------------------------------------------------------

    def get_status(self) -> dict:
        account = self.accounts.get_account()
        email_count = 0
        if account:
            email_count = len(self.emails.all_for_account(account.id))
        return {
            "connected": account is not None,
            "email_address": account.email_address if account else None,
            "last_sync_at": account.last_sync_at if account else None,
            "last_sync_status": account.last_sync_status if account else None,
            "email_count": email_count,
            "simulation": settings.gmail_simulation,
        }

    # -- Connect / disconnect ---------------------------------------------

    def connect(self) -> dict:
        """In simulation mode, immediately establish a connected account. In
        real mode, return the Google consent URL (account is created on callback)."""
        if settings.gmail_simulation:
            account = self.accounts.get_account()
            if account is None:
                client = get_gmail_client(None)
                account = self.accounts.create(
                    {
                        "email_address": client.fetch_profile_email(),
                        "status": "connected",
                    }
                )
            return {
                "connected": True,
                "authorization_url": None,
                "message": "Connected in simulation mode.",
            }

        state = secrets.token_urlsafe(16)
        return {
            "connected": False,
            "authorization_url": oauth.build_authorization_url(state),
            "message": "Redirect to Google to authorize access.",
        }

    def handle_callback(self, code: str) -> GmailAccount:
        """Real OAuth: exchange the code, fetch the profile, persist tokens."""
        tokens = oauth.exchange_code(code)
        client = get_gmail_client(tokens.access_token)
        email_address = client.fetch_profile_email()

        data = {
            "email_address": email_address,
            "status": "connected",
            "refresh_token_encrypted": encrypt_token(tokens.refresh_token),
            "access_token_encrypted": encrypt_token(tokens.access_token),
            "token_expires_at": tokens.expires_at,
        }
        existing = self.accounts.get_account()
        if existing:
            return self.accounts.update(existing, data)
        return self.accounts.create(data)

    def disconnect(self) -> None:
        account = self.accounts.get_account()
        if account:
            # Emails cascade-delete via the FK.
            self.accounts.delete(account)

    # -- Sync --------------------------------------------------------------

    def sync(self, *, max_results: int = 50) -> dict:
        account = self.accounts.get_account()
        if account is None:
            raise ValidationError("Gmail is not connected. Connect an account first.")

        access_token = self._valid_access_token(account)
        client = get_gmail_client(access_token)
        raw_emails = client.fetch_messages(max_results=max_results)

        context = self._build_match_context()

        imported = 0
        updated = 0
        matched = 0
        processed: list[tuple[RawEmail, dict]] = []

        for raw in raw_emails:
            # Import policy: Inbox + Sent only, recruiting emails only.
            if not ({"INBOX", "SENT"} & set(raw.labels)):
                continue
            if not is_recruiting_email(raw.subject, raw.body_preview, raw.sender):
                continue
            result = match_email(
                subject=raw.subject, sender=raw.sender, context=context
            )
            fields = {
                "company_id": result.company_id,
                "application_id": result.application_id,
                "recruiter_id": result.recruiter_id,
                "interview_id": result.interview_id,
                "match_confidence": result.confidence,
                "match_reason": result.reason,
            }
            processed.append((raw, fields))

        # Thread inheritance: give every message in a thread the best match
        # found anywhere in that thread (subject/sender vary across replies).
        self._propagate_thread_matches(processed)

        for raw, fields in processed:
            if fields["company_id"] or fields["recruiter_id"]:
                matched += 1
            existing = self.emails.get_by_message_id(account.id, raw.message_id)
            payload = {**_raw_to_columns(raw, account.id), **fields}
            if existing:
                self.emails.update(existing, payload)
                updated += 1
            else:
                self.emails.create(payload)
                imported += 1

        now = datetime.now(timezone.utc)
        self.accounts.update(
            account, {"last_sync_at": now, "last_sync_status": "success"}
        )

        return {
            "imported": imported,
            "updated": updated,
            "matched": matched,
            "total_processed": len(processed),
            "last_sync_at": now,
        }

    def _valid_access_token(self, account: GmailAccount) -> str | None:
        if settings.gmail_simulation:
            return None
        access = decrypt_token(account.access_token_encrypted)
        expired = (
            account.token_expires_at is None
            or account.token_expires_at <= datetime.now(timezone.utc)
        )
        if expired:
            refresh = decrypt_token(account.refresh_token_encrypted)
            if not refresh:
                raise ValidationError("Gmail session expired. Reconnect the account.")
            tokens = oauth.refresh_access_token(refresh)
            self.accounts.update(
                account,
                {
                    "access_token_encrypted": encrypt_token(tokens.access_token),
                    "token_expires_at": tokens.expires_at,
                },
            )
            return tokens.access_token
        return access

    @staticmethod
    def _propagate_thread_matches(
        processed: list[tuple[RawEmail, dict]],
    ) -> None:
        best: dict[str, dict] = {}
        for raw, fields in processed:
            current = best.get(raw.thread_id)
            if current is None or fields["match_confidence"] > current["match_confidence"]:
                best[raw.thread_id] = fields
        for raw, fields in processed:
            winner = best[raw.thread_id]
            if winner is fields:
                continue
            # Only fill gaps; never downgrade a stronger direct match.
            if fields["match_confidence"] < winner["match_confidence"]:
                for key in (
                    "company_id",
                    "application_id",
                    "recruiter_id",
                    "interview_id",
                ):
                    if not fields[key] and winner[key]:
                        fields[key] = winner[key]
                if winner["match_reason"]:
                    fields["match_reason"] = f"{winner['match_reason']} (thread)"

    def _build_match_context(self) -> MatchContext:
        companies = self.db.scalars(select(Company)).all()
        recruiters = self.db.scalars(select(Recruiter)).all()
        applications = self.db.scalars(select(JobApplication)).all()
        interviews = self.db.scalars(select(Interview)).all()
        return MatchContext(
            companies=tuple(
                CompanyRef(c.id, c.name, _domain_from_website(c.website))
                for c in companies
            ),
            recruiters=tuple(
                RecruiterRef(r.id, r.email, r.company_id) for r in recruiters
            ),
            applications=tuple(
                ApplicationRef(a.id, a.company_id, a.job_title) for a in applications
            ),
            interviews=tuple(
                InterviewRef(i.id, i.application_id) for i in interviews
            ),
        )

    # -- Reads -------------------------------------------------------------

    def list_emails(self, **filters) -> tuple[list[EmailMessage], int]:
        return self.emails.list_filtered(**filters)

    def get_timeline(self, application_id: UUID) -> list[dict]:
        """A unified chronological timeline for one application."""
        application = self.db.get(JobApplication, application_id)
        if application is None:
            return []

        events: list[dict] = [
            {
                "id": f"app-{application.id}",
                "kind": "application",
                "title": "Application created",
                "subtitle": application.job_title,
                "timestamp": application.created_at,
            }
        ]

        interviews = self.db.scalars(
            select(Interview).where(Interview.application_id == application_id)
        ).all()
        for interview in interviews:
            events.append(
                {
                    "id": f"int-{interview.id}",
                    "kind": "interview",
                    "title": "Interview scheduled",
                    "subtitle": interview.interview_type,
                    "timestamp": interview.scheduled_at,
                }
            )

        emails, _ = self.emails.list_filtered(
            application_id=application_id, limit=200
        )
        for email in emails:
            events.append(
                {
                    "id": f"mail-{email.id}",
                    "kind": _email_kind(email.subject),
                    "title": email.subject or "(no subject)",
                    "subtitle": email.sender,
                    "timestamp": email.sent_at,
                }
            )

        events.sort(key=lambda e: e["timestamp"])
        return events


def _email_kind(subject: str | None) -> str:
    lowered = (subject or "").lower()
    if any(h in lowered for h in _OFFER_HINTS):
        return "offer"
    if any(h in lowered for h in _REJECTION_HINTS):
        return "rejection"
    return "email"


def _raw_to_columns(raw: RawEmail, account_id: UUID) -> dict:
    return {
        "account_id": account_id,
        "message_id": raw.message_id,
        "thread_id": raw.thread_id,
        "subject": raw.subject,
        "sender": raw.sender,
        "sender_name": raw.sender_name,
        "recipients": raw.recipients,
        "sent_at": raw.sent_at,
        "body_preview": raw.body_preview,
        "direction": raw.direction,
        "labels": raw.labels,
        "attachments": raw.attachments,
    }
