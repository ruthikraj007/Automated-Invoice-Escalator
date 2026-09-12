import logging
from typing import Dict, Any, Tuple
import resend
from app.core.config import settings

logger = logging.getLogger("app.services.email")

# HTML Email Templates for 3 Escalation Tiers
TIER_TEMPLATES = {
    1: {
        "subject": "Payment Reminder: Invoice from {{company_name}} is due",
        "badge": "Payment Reminder",
        "badge_color": "#2563eb",
        "badge_bg": "#eff6ff",
        "headline": "Friendly Reminder Regarding Your Invoice",
        "tone_notice": "This is a courtesy reminder that your payment is past due.",
        "body": """
            <p style="margin: 0 0 16px 0; color: #334155; font-size: 15px; line-height: 1.6;">
                Hi <strong>{{customer_name}}</strong>,
            </p>
            <p style="margin: 0 0 16px 0; color: #334155; font-size: 15px; line-height: 1.6;">
                We wanted to follow up on your account with <strong>{{company_name}}</strong>. Our records indicate that your invoice for <strong>{{amount_due}}</strong> was due on <strong>{{due_date}}</strong> and has not yet been marked as paid.
            </p>
            <p style="margin: 0 0 24px 0; color: #334155; font-size: 15px; line-height: 1.6;">
                We understand things get busy! You can review and settle your balance immediately through our secure Stripe portal below.
            </p>
        """,
        "button_text": "Pay Invoice Online",
        "button_bg": "#2563eb",
        "footer_note": "If you have already settled this balance within the last 24 hours, please disregard this notice."
    },
    2: {
        "subject": "Second Notice: Overdue Balance with {{company_name}} - Action Required",
        "badge": "Second Notice - Urgent",
        "badge_color": "#d97706",
        "badge_bg": "#fef3c7",
        "headline": "Action Required: Overdue Account Balance",
        "tone_notice": "Important notice regarding uninterrupted account service and impending late fees.",
        "body": """
            <p style="margin: 0 0 16px 0; color: #334155; font-size: 15px; line-height: 1.6;">
                Dear <strong>{{customer_name}}</strong>,
            </p>
            <p style="margin: 0 0 16px 0; color: #334155; font-size: 15px; line-height: 1.6;">
                Your account with <strong>{{company_name}}</strong> is now <strong>over a week past due</strong>. The outstanding balance of <strong>{{amount_due}}</strong> was due on <strong>{{due_date}}</strong>.
            </p>
            <p style="margin: 0 0 16px 0; color: #334155; font-size: 15px; line-height: 1.6;">
                To maintain uninterrupted service access and prevent automatic late assessment fees from being applied, please resolve this balance today.
            </p>
            <p style="margin: 0 0 24px 0; color: #334155; font-size: 15px; line-height: 1.6;">
                If you have questions or need to arrange a payment schedule, please reply directly to this email immediately.
            </p>
        """,
        "button_text": "Settle Outstanding Balance",
        "button_bg": "#d97706",
        "footer_note": "Maintaining good standing ensures continued uninterrupted access to {{company_name}} services."
    },
    3: {
        "subject": "FINAL DEMAND: Imminent Service Suspension on Invoice from {{company_name}}",
        "badge": "Final Demand Notice",
        "badge_color": "#dc2626",
        "badge_bg": "#fee2e2",
        "headline": "Final Demand Prior to Account Suspension",
        "tone_notice": "CRITICAL: Account access scheduled for suspension within 48 business hours.",
        "body": """
            <p style="margin: 0 0 16px 0; color: #334155; font-size: 15px; line-height: 1.6;">
                Attention <strong>{{customer_name}}</strong>,
            </p>
            <p style="margin: 0 0 16px 0; color: #b91c1c; font-weight: 600; font-size: 15px; line-height: 1.6;">
                This is your final formal demand notice from {{company_name}}.
            </p>
            <p style="margin: 0 0 16px 0; color: #334155; font-size: 15px; line-height: 1.6;">
                Your outstanding invoice of <strong>{{amount_due}}</strong> is now <strong>14+ days delinquent</strong> (originally due on <strong>{{due_date}}</strong>). Despite previous notifications, this balance remains unpaid.
            </p>
            <p style="margin: 0 0 24px 0; color: #334155; font-size: 15px; line-height: 1.6;">
                Unless payment is received within <strong>48 hours</strong>, your services will be immediately suspended and the account will be transferred to our external collections and recovery agency.
            </p>
        """,
        "button_text": "Pay Now to Prevent Suspension",
        "button_bg": "#dc2626",
        "footer_note": "Failure to remit payment will trigger account termination and formal recovery procedures."
    }
}


class EmailService:
    def __init__(self):
        if settings.RESEND_API_KEY:
            resend.api_key = settings.RESEND_API_KEY
            self.configured = True
            logger.info("Resend API key initialized.")
        else:
            self.configured = False
            logger.info("Resend API key not configured; operating with console logger fallback.")

    def render_template(self, tier: int, variables: Dict[str, str]) -> Tuple[str, str]:
        """
        Interpolate dynamic variables into responsive HTML template for specified tier.
        Dynamic variables supported:
          - {{customer_name}}
          - {{amount_due}}
          - {{due_date}}
          - {{payment_link}}
          - {{company_name}}
        """
        template = TIER_TEMPLATES.get(tier, TIER_TEMPLATES[1])

        subject = template["subject"]
        body_content = template["body"]
        footer_note = template["footer_note"]

        # Default company name fallback
        if "company_name" not in variables or not variables["company_name"]:
            variables["company_name"] = settings.APP_NAME

        # Substitute all dynamic variables
        for key, value in variables.items():
            placeholder = f"{{{{{key}}}}}"
            subject = subject.replace(placeholder, str(value))
            body_content = body_content.replace(placeholder, str(value))
            footer_note = footer_note.replace(placeholder, str(value))

        payment_link = variables.get("payment_link", "#")

        html_email = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{subject}</title>
</head>
<body style="margin: 0; padding: 0; background-color: #f1f5f9; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;">
    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="background-color: #f1f5f9; padding: 32px 16px;">
        <tr>
            <td align="center">
                <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="max-width: 580px; background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);">
                    <!-- Header -->
                    <tr>
                        <td style="padding: 32px 32px 20px 32px; border-bottom: 1px solid #f1f5f9;">
                            <span style="display: inline-block; background-color: {template['badge_bg']}; color: {template['badge_color']}; font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; padding: 4px 10px; border-radius: 9999px; margin-bottom: 12px;">
                                Tier {tier}: {template['badge']}
                            </span>
                            <h1 style="margin: 0; color: #0f172a; font-size: 22px; font-weight: 700; line-height: 1.3;">
                                {template['headline']}
                            </h1>
                        </td>
                    </tr>
                    <!-- Content -->
                    <tr>
                        <td style="padding: 28px 32px;">
                            {body_content}

                            <!-- Invoice Details Box -->
                            <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; margin-bottom: 28px;">
                                <tr>
                                    <td style="padding: 16px 20px;">
                                        <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0">
                                            <tr>
                                                <td style="color: #64748b; font-size: 13px; font-weight: 500;">Amount Due:</td>
                                                <td align="right" style="color: #0f172a; font-size: 18px; font-weight: 700;">{variables.get('amount_due', '')}</td>
                                            </tr>
                                            <tr>
                                                <td style="color: #64748b; font-size: 13px; padding-top: 8px;">Original Due Date:</td>
                                                <td align="right" style="color: #334155; font-size: 13px; font-weight: 600; padding-top: 8px;">{variables.get('due_date', '')}</td>
                                            </tr>
                                        </table>
                                    </td>
                                </tr>
                            </table>

                            <!-- Action Button -->
                            <table role="presentation" cellspacing="0" cellpadding="0" border="0" align="center" style="margin: 0 auto;">
                                <tr>
                                    <td align="center" style="border-radius: 8px; background-color: {template['button_bg']};">
                                        <a href="{payment_link}" target="_blank" style="display: inline-block; padding: 14px 32px; font-size: 15px; font-weight: 600; color: #ffffff; text-decoration: none; border-radius: 8px; letter-spacing: 0.02em;">
                                            {template['button_text']} &rarr;
                                        </a>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                    <!-- Footer -->
                    <tr>
                        <td style="padding: 24px 32px; background-color: #fafafa; border-top: 1px solid #f1f5f9;">
                            <p style="margin: 0 0 8px 0; color: #64748b; font-size: 12px; line-height: 1.5;">
                                {footer_note}
                            </p>
                            <p style="margin: 0; color: #94a3b8; font-size: 11px;">
                                Sent automatically by <strong>{variables.get('company_name', '')}</strong> via EscalatePay Billing Orchestration.
                            </p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>"""
        return subject, html_email

    def send_escalation_email(
        self,
        recipient_email: str,
        customer_name: str,
        invoice_id: str,
        amount_due: str,
        due_date: str,
        payment_link: str,
        tier: int,
        company_name: str = ""
    ) -> Dict[str, Any]:
        """
        Render dynamic HTML template and dispatch email via Resend (or console logger fallback).
        """
        variables = {
            "customer_name": customer_name,
            "amount_due": amount_due,
            "due_date": due_date,
            "payment_link": payment_link,
            "company_name": company_name or settings.APP_NAME,
        }

        subject, html_content = self.render_template(tier, variables)

        # Fallback console logger when Resend API key is not configured
        if not self.configured:
            logger.info("=" * 60)
            logger.info(f"[EMAIL SERVICE - CONSOLE DISPATCH (Tier {tier})]")
            logger.info(f"To: {recipient_email}")
            logger.info(f"Subject: {subject}")
            logger.info(f"Customer: {customer_name} | Amount: {amount_due} | Due: {due_date}")
            logger.info(f"Payment URL: {payment_link}")
            logger.info("=" * 60)
            return {
                "id": f"email_sim_{invoice_id}_tier{tier}",
                "status": "delivered_console",
                "recipient": recipient_email,
                "tier": tier,
                "subject": subject,
            }

        try:
            params = {
                "from": settings.DEFAULT_SENDER_EMAIL,
                "to": [recipient_email],
                "subject": subject,
                "html": html_content,
            }
            email_resp = resend.Emails.send(params)
            logger.info(f"Dispatched Tier {tier} email to {recipient_email} via Resend. ID: {email_resp.get('id')}")
            return {
                "id": email_resp.get("id"),
                "status": "sent",
                "recipient": recipient_email,
                "tier": tier,
                "subject": subject,
            }
        except Exception as e:
            logger.error(f"Failed to dispatch email via Resend: {e}")
            raise e


email_service = EmailService()
