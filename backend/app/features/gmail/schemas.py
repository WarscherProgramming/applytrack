from datetime import datetime
from uuid import UUID

from app.shared.base_schema import AppBaseModel, EntitySchema


class GmailStatusResponse(AppBaseModel):
    connected: bool
    email_address: str | None = None
    last_sync_at: datetime | None = None
    last_sync_status: str | None = None
    email_count: int = 0
    # True when running against the fake client (no real Google credentials).
    simulation: bool = True


class GmailConnectResponse(AppBaseModel):
    connected: bool
    # Present in real OAuth mode: the URL to redirect the user to for consent.
    authorization_url: str | None = None
    message: str


class GmailSyncResponse(AppBaseModel):
    imported: int
    updated: int
    matched: int
    total_processed: int
    last_sync_at: datetime


class EmailAttachment(AppBaseModel):
    filename: str
    mime_type: str | None = None
    size: int = 0


class EmailMessageResponse(EntitySchema):
    message_id: str
    thread_id: str
    subject: str | None
    sender: str
    sender_name: str | None
    recipients: list[str]
    sent_at: datetime
    body_preview: str | None
    direction: str
    labels: list[str]
    attachments: list[EmailAttachment]
    company_id: UUID | None
    application_id: UUID | None
    recruiter_id: UUID | None
    interview_id: UUID | None
    match_confidence: float
    match_reason: str | None


class EmailListResponse(AppBaseModel):
    items: list[EmailMessageResponse]
    total: int
    skip: int
    limit: int


class TimelineEvent(AppBaseModel):
    """A single point on a unified, cross-entity timeline."""

    id: str
    kind: str  # application | recruiter | interview | email | offer | rejection
    title: str
    subtitle: str | None = None
    timestamp: datetime


class TimelineResponse(AppBaseModel):
    items: list[TimelineEvent]
