"""
tools/email_tools.py
---------------------
Email dispatch utilities.
Supports Gmail SMTP (default) and SendGrid (optional).
"""

from __future__ import annotations

import smtplib
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from pathlib import Path

from config.settings import (
    EMAIL_SENDER,
    EMAIL_PASSWORD,
    SMTP_HOST,
    SMTP_PORT,
    SENDGRID_API_KEY,
)


class EmailTools:
    """Send EDA reports via email with HTML body and attachments."""

    # ── Gmail SMTP ─────────────────────────────────────────────────────

    def send_smtp(
        self,
        recipient:   str,
        subject:     str,
        html_body:   str,
        attachments: list[str] | None = None,
    ) -> dict:
        """Send an email via Gmail SMTP (TLS)."""
        if not EMAIL_SENDER or not EMAIL_PASSWORD:
            return {
                "success": False,
                "error": (
                    "EMAIL_SENDER and EMAIL_PASSWORD "
                    "must be set in .env"
                ),
            }

        try:
            msg = MIMEMultipart("alternative")
            msg["From"]    = EMAIL_SENDER
            msg["To"]      = recipient
            msg["Subject"] = subject

            msg.attach(MIMEText(html_body, "html"))

            for path_str in (attachments or []):
                path = Path(path_str)
                if not path.exists():
                    continue
                with open(path, "rb") as f:
                    part = MIMEBase("application", "octet-stream")
                    part.set_payload(f.read())
                encoders.encode_base64(part)
                part.add_header(
                    "Content-Disposition",
                    f"attachment; filename={path.name}",
                )
                msg.attach(part)

            with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
                server.ehlo()
                server.starttls()
                server.login(EMAIL_SENDER, EMAIL_PASSWORD)
                server.sendmail(
                    EMAIL_SENDER, recipient, msg.as_string()
                )

            return {
                "success":   True,
                "recipient": recipient,
                "method":    "smtp",
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    # ── SendGrid ───────────────────────────────────────────────────────

    def send_sendgrid(
        self,
        recipient:   str,
        subject:     str,
        html_body:   str,
        attachments: list[str] | None = None,
    ) -> dict:
        """Send email via SendGrid API."""
        if not SENDGRID_API_KEY:
            return {
                "success": False,
                "error":   "SENDGRID_API_KEY not set in .env",
            }

        try:
            import sendgrid
            from sendgrid.helpers.mail import (
                Mail, Attachment, FileContent,
                FileName, FileType, Disposition,
            )
            import base64

            message = Mail(
                from_email=EMAIL_SENDER,
                to_emails=recipient,
                subject=subject,
                html_content=html_body,
            )

            for path_str in (attachments or []):
                path = Path(path_str)
                if not path.exists():
                    continue
                with open(path, "rb") as f:
                    data = base64.b64encode(f.read()).decode()
                attachment = Attachment(
                    FileContent(data),
                    FileName(path.name),
                    FileType("text/html"),
                    Disposition("attachment"),
                )
                message.attachment = attachment

            sg       = sendgrid.SendGridAPIClient(
                api_key=SENDGRID_API_KEY
            )
            response = sg.send(message)
            return {
                "success":   response.status_code in [200, 201, 202],
                "status":    response.status_code,
                "recipient": recipient,
                "method":    "sendgrid",
            }

        except ImportError:
            return {
                "success": False,
                "error": (
                    "sendgrid package not installed. "
                    "Run: pip install sendgrid"
                ),
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ── Dispatcher ─────────────────────────────────────────────────────

    def send(
        self,
        recipient:   str,
        subject:     str,
        html_body:   str,
        attachments: list[str] | None = None,
        method:      str = "smtp",
    ) -> dict:
        """Auto-dispatch to SMTP or SendGrid."""
        if method == "sendgrid" and SENDGRID_API_KEY:
            return self.send_sendgrid(
                recipient, subject, html_body, attachments
            )
        return self.send_smtp(
            recipient, subject, html_body, attachments
        )

    # ── Email body builder ─────────────────────────────────────────────

    def build_email_body(
        self,
        filename:  str,
        overview:  dict,
        quality:   dict,
        insights:  list[str],
    ) -> str:
        """Build a styled HTML email body."""
        rows        = overview.get("rows", 0)
        cols        = overview.get("columns", 0)
        missing_pct = overview.get("missing_pct", 0)
        score       = quality.get("overall_score", 0)
        grade       = quality.get("grade", "?")
        score_color = (
            "#4ade80" if score >= 90 else
            "#facc15" if score >= 75 else
            "#fb923c" if score >= 60 else
            "#f87171"
        )

        insight_items = "".join(
            f"<li style='margin:8px 0;color:#cbd5e1'>{i}</li>"
            for i in insights[:6]
        )

        return f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>
  body{{font-family:'Segoe UI',sans-serif;
        background:#0f1117;color:#e2e8f0;
        margin:0;padding:20px}}
  .container{{max-width:680px;margin:0 auto;
              background:#1a1d2e;border-radius:16px;
              overflow:hidden}}
  .header{{background:linear-gradient(135deg,#1e3a5f,#312e81);
           padding:32px;text-align:center}}
  .header h1{{margin:0;font-size:24px;color:#fff;
              letter-spacing:-0.5px}}
  .header p{{margin:8px 0 0;color:#94a3b8;font-size:14px}}
  .body{{padding:32px}}
  .stats-grid{{display:grid;
               grid-template-columns:1fr 1fr 1fr;
               gap:16px;margin:24px 0}}
  .stat-box{{background:#0f1117;border-radius:12px;
             padding:20px;text-align:center;
             border:1px solid #2d3748}}
  .stat-box .value{{font-size:28px;font-weight:700;
                    color:#38bdf8}}
  .stat-box .label{{font-size:12px;color:#64748b;
                    margin-top:4px;text-transform:uppercase;
                    letter-spacing:1px}}
  .quality-box{{background:#0f1117;border-radius:12px;
                padding:24px;margin:24px 0;
                border:1px solid #2d3748;text-align:center}}
  .grade{{font-size:64px;font-weight:900;
          color:{score_color};line-height:1}}
  .score{{font-size:18px;color:{score_color}}}
  .insights{{background:#0f1117;border-radius:12px;
             padding:24px;margin:24px 0;
             border:1px solid #2d3748}}
  .insights h3{{margin:0 0 16px;color:#a78bfa;
                font-size:14px;text-transform:uppercase;
                letter-spacing:1px}}
  .insights ul{{margin:0;padding-left:20px}}
  .footer{{padding:20px 32px;
           border-top:1px solid #2d3748;
           text-align:center;color:#475569;font-size:12px}}
</style>
</head>
<body>
<div class="container">
  <div class="header">
    <h1>📊 EDA Report Ready</h1>
    <p>{filename}</p>
  </div>
  <div class="body">
    <div class="stats-grid">
      <div class="stat-box">
        <div class="value">{rows:,}</div>
        <div class="label">Rows</div>
      </div>
      <div class="stat-box">
        <div class="value">{cols}</div>
        <div class="label">Columns</div>
      </div>
      <div class="stat-box">
        <div class="value">{missing_pct:.1f}%</div>
        <div class="label">Missing</div>
      </div>
    </div>
    <div class="quality-box">
      <div class="grade">{grade}</div>
      <div class="score">{score:.1f} / 100 — Data Quality</div>
    </div>
    <div class="insights">
      <h3>🤖 AI Insights</h3>
      <ul>{insight_items}</ul>
    </div>
  </div>
  <div class="footer">
    Generated by Automated EDA Agent · Powered by Claude AI
  </div>
</div>
</body>
</html>
"""
