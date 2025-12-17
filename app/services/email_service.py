import os
import smtplib
from email.message import EmailMessage


def send_email(to_address: str, subject: str, body: str) -> bool:
    
    """Envio simples de email via SMTP; retorna True se enviado."""

    host = os.getenv('SMTP_HOST')
    port = int(os.getenv('SMTP_PORT', '587'))
    user = os.getenv('SMTP_USER')
    password = os.getenv('SMTP_PASS')
    use_tls = os.getenv('SMTP_TLS', 'true').lower() == 'true'
    from_address = os.getenv('SMTP_FROM', user or 'no-reply@example.com')

    if not host or not user or not password:
        print('[email] SMTP não configurado; ignorando envio')
        return False

    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = from_address
    msg['To'] = to_address
    msg.set_content(body)

    try:
        with smtplib.SMTP(host, port, timeout=10) as server:
            if use_tls:
                server.starttls()
            server.login(user, password)
            server.send_message(msg)
        return True
    except Exception as exc:
        print(f'[email] falha ao enviar: {exc}')
        return False