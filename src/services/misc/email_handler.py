import imaplib
import email
import os
from email.header import decode_header
import re
import time


class EmailHandler:

  def get_indeed_one_time_code_from_mdc(self, timeout=10) -> str:
    USERNAME = os.getenv("MAIL_DOT_COM_EMAIL")
    PASSWORD = os.getenv("MAIL_DOT_COM_PASS")
    assert USERNAME
    assert PASSWORD

    imap = imaplib.IMAP4_SSL("imap.mail.com")
    imap.login(USERNAME, PASSWORD)
    imap.select("INBOX")

    start_time = time.time()
    while time.time() - start_time < timeout:
      _, raw_ids = imap.search(None, 'UNSEEN')
      email_ids = raw_ids[0].split()
      if email_ids:
        latest_id = email_ids[-1]
        _, msg_data = imap.fetch(latest_id, "(RFC822)")
        raw_email = msg_data[0][1] if msg_data and msg_data[0] else None

        if isinstance(raw_email, bytes):
          msg = email.message_from_bytes(raw_email)
          subject, encoding = decode_header(msg["Subject"])[0]
          if isinstance(subject, bytes):
            subject = subject.decode(encoding or "utf-8")
          raw_code = re.search(r"[0-9]+", subject)
          assert raw_code
          code = raw_code.group()
          imap.store(latest_id, '+FLAGS', '\\Deleted')
          imap.expunge()
          imap.logout()
          return code
    imap.logout()
    raise TimeoutError("Timed out waiting for one-time code.")
