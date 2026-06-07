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


class CsvEmailReader:
    def __init__(self, path=None):
        self.path = path or os.getenv("CSV_MOCK_FILE", MOCK_CSV_FILE)
        self.emails = []
        with open(self.path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                self.emails.append({
                    "id": row["id"],
                    "sender": row["sender"],
                    "subject": row["subject"],
                    "body": row["body"],
                    "received_at": row["received_at"],
                })
        self.cursor = 0
        self.total = len(self.emails)
        self.exhausted = False
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
    def __init__(self):
        self.host = os.getenv("IMAP_HOST", "imap.gmail.com")
        self.port = int(os.getenv("IMAP_PORT", "993"))
        self.user = os.getenv("IMAP_USER", "")
        self.password = os.getenv("IMAP_PASSWORD", "")

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

            _, data = mail.search(None, "UNSEEN")
            results = []
            for num in data[0].split():
                _, msg_data = mail.fetch(num, "(RFC822)")
                raw_email = msg_data[0][1]
                msg = email_lib.message_from_bytes(raw_email)
                email_id = str(num.decode())
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


def get_reader():
    mode = os.getenv("EMAIL_MODE", "mock")
    if mode == "imap":
        logger.info("Using IMAP email reader")
        return IMAPEmailReader()
    if mode == "csv":
        logger.info("Using CSV email reader")
        return CsvEmailReader()
    logger.info("Using mock email reader")
    return MockEmailReader()
