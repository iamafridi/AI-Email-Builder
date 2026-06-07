import json
import csv
import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

MOCK_FILE = os.path.join(os.path.dirname(__file__), "mock_emails.json")
MOCK_CSV_FILE = os.path.join(os.path.dirname(__file__), "mock_emails.csv")


class MockEmailReader:
    def __init__(self):
        with open(MOCK_FILE, "r") as f:
            self.emails = json.load(f)
        self.cursor = 0
        self.total = len(self.emails)
        self.exhausted = False
        logger.info("Loaded %d mock emails", self.total)

    def get_new_emails(self):
        if self.exhausted:
            return []
        start = self.cursor
        end = min(start + 2, self.total)
        if start >= self.total:
            self.exhausted = True
            return []
        batch = self.emails[start:end]
        self.cursor = end
        logger.info("Delivering %d new mock emails (cursor: %d/%d)", len(batch), self.cursor, self.total)
        return batch


COLUMN_ALIASES = {
    "sender": ["sender", "from", "from_email"],
    "received_at": ["received_at", "timestamp", "date", "datetime", "received"],
}

class CsvEmailReader:
    def __init__(self, path=None):
        self.path = path or os.getenv("CSV_MOCK_FILE", MOCK_CSV_FILE)
        self.emails = []
        self.cursor = 0
        self.total = 0
        self.exhausted = False
        try:
            with open(self.path, "r", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                if not reader.fieldnames:
                    raise ValueError("CSV file is empty or has no header row")
                normalized = {}
                for col in reader.fieldnames:
                    for canonical, aliases in COLUMN_ALIASES.items():
                        if col.lower() in [a.lower() for a in aliases]:
                            normalized[col] = canonical
                            break
                    else:
                        normalized[col] = col
                normalized_headers = set(normalized.values())
                required = {"id", "sender", "subject", "body", "received_at"}
                missing = required - normalized_headers
                if missing:
                    raise ValueError(
                        f"CSV missing required columns: {', '.join(sorted(missing))}. "
                        f"Found: {', '.join(reader.fieldnames)}"
                    )
                for row in reader:
                    mapped = {}
                    for col, val in row.items():
                        mapped[normalized.get(col, col)] = val
                    self.emails.append({
                        "id": mapped["id"],
                        "sender": mapped["sender"],
                        "subject": mapped["subject"],
                        "body": mapped["body"],
                        "received_at": mapped["received_at"],
                    })
        except Exception as e:
            logger.error("Failed to load CSV: %s", e)
            raise
        self.total = len(self.emails)
        logger.info("Loaded %d emails from CSV", self.total)

    def get_new_emails(self):
        if self.exhausted:
            return []
        start = self.cursor
        end = min(start + 2, self.total)
        if start >= self.total:
            self.exhausted = True
            return []
        batch = self.emails[start:end]
        self.cursor = end
        logger.info("Delivering %d new CSV emails (cursor: %d/%d)", len(batch), self.cursor, self.total)
        return batch


class IMAPEmailReader:
    def __init__(self, host=None, port=None, user=None, password=None):
        self.host = host or os.getenv("IMAP_HOST", "imap.gmail.com")
        self.port = int(port or os.getenv("IMAP_PORT", "993"))
        self.user = user or os.getenv("IMAP_USER", "")
        self.password = password or os.getenv("IMAP_PASSWORD", "")

    def get_new_emails(self):
        import imaplib
        import email as email_lib
        from email.utils import parsedate_to_datetime

        if not self.user or not self.password:
            logger.warning("IMAP credentials not configured")
            return []

        try:
            mail = imaplib.IMAP4_SSL(self.host, self.port)
            mail.login(self.user, self.password)
            mail.select("INBOX")

            _, data = mail.uid('search', None, "UNSEEN")
            results = []
            for uid in data[0].split():
                _, msg_data = mail.uid('fetch', uid, "(RFC822)")
                raw_email = msg_data[0][1]
                msg = email_lib.message_from_bytes(raw_email)
                email_id = uid.decode()
                sender = msg.get("From", "unknown")
                subject = msg.get("Subject", "(no subject)")
                received_at = parsedate_to_datetime(msg.get("Date")).isoformat()
                body = ""
                if msg.is_multipart():
                    for part in msg.walk():
                        if part.get_content_type() == "text/plain":
                            body = part.get_payload(decode=True).decode(errors="ignore")
                            break
                else:
                    body = msg.get_payload(decode=True).decode(errors="ignore")
                results.append({
                    "id": email_id,
                    "sender": sender,
                    "subject": subject,
                    "body": body[:500],
                    "received_at": received_at,
                })
            mail.logout()
            return results
        except Exception as e:
            logger.error("IMAP fetch failed: %s", e)
            return []


def get_reader(mode=None, **kwargs):
    mode = mode or os.getenv("EMAIL_MODE", "mock")
    if mode == "imap":
        logger.info("Using IMAP email reader")
        return IMAPEmailReader(**kwargs)
    if mode == "csv":
        logger.info("Using CSV email reader")
        path = kwargs.get("path")
        return CsvEmailReader(path=path)
    logger.info("Using mock email reader")
    return MockEmailReader()
