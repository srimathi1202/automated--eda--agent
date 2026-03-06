"""
agents/email_agent.py
---------------------
Dispatches the EDA report dashboard via email.
"""

from __future__ import annotations
from typing import Any

from agents.base_agent import BaseAgent
from tools.email_tools import EmailTools


class EmailAgent(BaseAgent):
    """Sends the EDA HTML dashboard to specified recipients."""

    def __init__(self, verbose: bool = False):
        super().__init__("EmailAgent", verbose)
        self.email = EmailTools()

    def run(self, context: dict) -> dict[str, Any]:
        recipient      = context.get("email_recipient", "")
        filename       = context.get("filename", "dataset")
        profile        = context.get("profile", {})
        insights       = context.get("insights", {})
        dashboard_path = context.get("dashboard_path", "")
        method         = context.get("email_method", "smtp")

        if not recipient:
            self.log_step(
                "Skipping email — no recipient provided"
            )
            return {
                "email_sent": False,
                "reason": "no_recipient"
            }

        self.log_step("Building email body")
        html_body = self.email.build_email_body(
            filename=filename,
            overview=profile.get("overview", {}),
            quality=profile.get("data_quality", {}),
            insights=insights.get("key_insights", []),
        )

        subject = f"📊 EDA Report Ready — {filename}"
        self.log_step("Sending email", f"→ {recipient}")

        result = self.email.send(
            recipient=recipient,
            subject=subject,
            html_body=html_body,
            attachments=(
                [dashboard_path] if dashboard_path else []
            ),
            method=method,
        )

        if result.get("success"):
            self.log_step("Email sent ✅", recipient)
        else:
            self.log_step(
                "Email failed ❌",
                result.get("error", "Unknown error")
            )

        return {
            "email_sent":   result.get("success", False),
            "email_result": result,
        }
.csv
