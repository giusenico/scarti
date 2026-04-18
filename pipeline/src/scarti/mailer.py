"""Weekly newsletter sender.

Flow:
  1. Query Supabase for confirmed subscribers.
  2. Build a minimal per-locale email body with the report headline + link.
  3. Send via Resend, one request per recipient (Resend has no bulk API but
     supports ~10 req/s for free tiers — plenty for a small list).
  4. Update last_sent_at so re-runs don't double-send.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime, timezone

from scarti.models import Report

SITE_URL = os.getenv("SCARTI_SITE_URL", "https://scarti.example")
FROM_EMAIL = os.getenv("SCARTI_FROM_EMAIL", "Scarti <newsletter@scarti.example>")


@dataclass
class SendResult:
    sent: int
    skipped: int
    failed: int


def _subject_for(report: Report, locale: str) -> str:
    body = report.it if locale == "it" else report.en
    return body.headline


def _text_for(report: Report, locale: str, unsub_token: str) -> str:
    body = report.it if locale == "it" else report.en
    report_url = f"{SITE_URL}{'' if locale == 'it' else '/en'}/report/{report.slug}"
    unsub_url = f"{SITE_URL}/api/unsubscribe?token={unsub_token}"
    if locale == "it":
        return (
            f"{body.headline}\n\n"
            f"{body.lede}\n\n"
            f"Leggi il report: {report_url}\n\n"
            f"---\n"
            f"Annulla l'iscrizione: {unsub_url}\n"
        )
    return (
        f"{body.headline}\n\n"
        f"{body.lede}\n\n"
        f"Read the report: {report_url}\n\n"
        f"---\n"
        f"Unsubscribe: {unsub_url}\n"
    )


def _html_for(report: Report, locale: str, unsub_token: str) -> str:
    body = report.it if locale == "it" else report.en
    report_url = f"{SITE_URL}{'' if locale == 'it' else '/en'}/report/{report.slug}"
    unsub_url = f"{SITE_URL}/api/unsubscribe?token={unsub_token}"
    cta = "Leggi il report" if locale == "it" else "Read the report"
    unsub = "Annulla l'iscrizione" if locale == "it" else "Unsubscribe"
    return f"""<div style="font-family:Georgia,serif;max-width:560px;margin:0 auto;padding:24px;color:#111;line-height:1.6">
  <h1 style="font-size:22px;margin:0 0 12px">{body.headline}</h1>
  <p style="font-size:16px;color:#555">{body.lede}</p>
  <p style="margin:24px 0">
    <a href="{report_url}" style="background:#b00020;color:#fff;padding:10px 18px;border-radius:4px;text-decoration:none;font-family:system-ui,sans-serif;font-size:14px">{cta} →</a>
  </p>
  <hr style="border:none;border-top:1px solid #eee;margin:32px 0 16px">
  <p style="color:#999;font-size:12px;font-family:system-ui,sans-serif">
    <a href="{unsub_url}" style="color:#999">{unsub}</a>
  </p>
</div>"""


def send_newsletter(report: Report) -> SendResult:
    try:
        import resend
        from supabase import create_client
    except ImportError as e:
        raise ImportError(
            "Install with: pip install -e '.[mail,subscribers]'"
        ) from e

    resend.api_key = os.environ["RESEND_API_KEY"]
    sb = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_ROLE_KEY"])

    rows = (
        sb.table("subscribers")
        .select("email, locale, unsub_token")
        .not_.is_("confirmed_at", "null")
        .execute()
    )
    subscribers = rows.data or []

    sent = skipped = failed = 0
    now_iso = datetime.now(timezone.utc).isoformat()

    for sub in subscribers:
        email = sub["email"]
        locale = sub["locale"]
        unsub_token = sub["unsub_token"]
        try:
            resend.Emails.send(
                {
                    "from": FROM_EMAIL,
                    "to": [email],
                    "subject": _subject_for(report, locale),
                    "text": _text_for(report, locale, unsub_token),
                    "html": _html_for(report, locale, unsub_token),
                    "headers": {
                        "List-Unsubscribe": f"<{SITE_URL}/api/unsubscribe?token={unsub_token}>",
                        "List-Unsubscribe-Post": "List-Unsubscribe=One-Click",
                    },
                }
            )
            sb.table("subscribers").update({"last_sent_at": now_iso}).eq("email", email).execute()
            sent += 1
        except Exception as e:
            print(f"[warn] failed to send to {email}: {e}")
            failed += 1

    return SendResult(sent=sent, skipped=skipped, failed=failed)
