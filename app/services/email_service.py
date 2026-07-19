import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.config import settings
from app.schemas import BillResult

logger = logging.getLogger("billing.email")
logging.basicConfig(level=logging.INFO)


def _render_invoice_text(bill: BillResult) -> str:
    lines = [
        f"Invoice #{bill.purchase_id}",
        f"Customer: {bill.customer_email}",
        f"Date: {bill.created_at.isoformat()}",
        "",
        "Items:",
    ]
    for item in bill.items:
        lines.append(
            f"  {item.product_id} | {item.product_name} | qty={item.quantity} "
            f"| unit={item.unit_price:.2f} | tax%={item.tax_percentage:.2f} "
            f"| tax={item.tax_payable:.2f} | total={item.total_price:.2f}"
        )
    lines += [
        "",
        f"Total (without tax): {settings.currency_symbol} {bill.total_price_without_tax:.2f}",
        f"Total tax payable:   {settings.currency_symbol} {bill.total_tax_payable:.2f}",
        f"Net price:           {settings.currency_symbol} {bill.net_price:.2f}",
        f"Rounded net price:   {settings.currency_symbol} {bill.rounded_net_price:.2f}",
        f"Cash paid:           {settings.currency_symbol} {bill.cash_paid:.2f}",
        f"Balance returned:    {settings.currency_symbol} {bill.balance_amount:.2f}",
        "",
        "Change denomination breakdown:",
    ]
    for cd in bill.change_denominations:
        lines.append(f"  {cd.value} x {cd.count}")
    return "\n".join(lines)


def send_invoice_email(bill: BillResult) -> None:
    body = _render_invoice_text(bill)

    if not settings.smtp_host:
        logger.info("SMTP not configured — logging invoice instead of emailing.\n%s", body)
        return

    msg = MIMEMultipart()
    msg["From"] = settings.smtp_from_email
    msg["To"] = bill.customer_email
    msg["Subject"] = f"Your invoice #{bill.purchase_id}"
    msg.attach(MIMEText(body, "plain"))

    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10) as server:
            if settings.smtp_use_tls:
                server.starttls()
            if settings.smtp_username:
                server.login(settings.smtp_username, settings.smtp_password)
            server.sendmail(settings.smtp_from_email, [bill.customer_email], msg.as_string())
        logger.info("Invoice #%s emailed to %s", bill.purchase_id, bill.customer_email)
    except Exception:
        logger.exception("Failed to send invoice #%s to %s", bill.purchase_id, bill.customer_email)
