"""
Email utility functions
"""
import logging
from pathlib import Path
from typing import Any, Dict, Optional

import emails
from emails.template import JinjaTemplate
from jose import jwt

from app.core.config import settings


def send_email(
    email_to: str,
    subject: str = "",
    html_template: str = "",
    environment: Dict[str, Any] = {},
) -> None:
    """
    Email gönderme fonksiyonu.
    
    Args:
        email_to: Alıcı email adresi
        subject: Email konusu
        html_template: HTML içeriği
        environment: Template değişkenleri
    """
    # SMTP yapılandırması olmaması durumunda sadece log yazıyoruz
    if not settings.SMTP_HOST or settings.EMAILS_FROM_EMAIL is None:
        logging.info(f"SMTP yapılandırması olmadığından, email gönderilmiyor: {email_to}")
        return

    message = emails.Message(
        subject=subject,
        html=html_template,
        mail_from=(settings.EMAILS_FROM_NAME, settings.EMAILS_FROM_EMAIL),
    )
    smtp_options = {"host": settings.SMTP_HOST, "port": settings.SMTP_PORT}
    if settings.SMTP_TLS:
        smtp_options["tls"] = True
    if settings.SMTP_USER:
        smtp_options["user"] = settings.SMTP_USER
    if settings.SMTP_PASSWORD:
        smtp_options["password"] = settings.SMTP_PASSWORD
    response = message.send(to=email_to, render=environment, smtp=smtp_options)
    logging.info(f"Email gönderimi: {email_to}, başarılı: {response.status_code == 250}")


def send_test_email(email_to: str) -> None:
    """
    Test email'i gönderir.
    
    Args:
        email_to: Alıcı email adresi
    """
    project_name = settings.PROJECT_NAME
    subject = f"{project_name} - Test email"
    html_template = """
        <p>Test email from {project_name}</p>
        <p>Bu bir test email'idir.</p>
    """
    send_email(
        email_to=email_to,
        subject=subject,
        html_template=html_template,
        environment={"project_name": project_name},
    )


def send_reset_password_email(email_to: str, email: str, token: str) -> None:
    """
    Şifre sıfırlama email'i gönderir.
    
    Args:
        email_to: Alıcı email adresi
        email: Kullanıcı email adresi (log için)
        token: Şifre sıfırlama tokeni
    """
    project_name = settings.PROJECT_NAME
    subject = f"{project_name} - Şifre Sıfırlama"
    server_host = settings.SERVER_HOST
    link = f"{server_host}/reset-password?token={token}"
    html_template = """
        <p>Merhaba,</p>
        <p>
            <a href="{link}">
                Şifrenizi sıfırlamak için tıklayınız
            </a>
        </p>
        <p>Bu linkin geçerlilik süresi sınırlıdır.</p>
        <p>İşlemi siz talep etmediyseniz, bu email'i dikkate almayınız.</p>
        <p>Saygılarımızla,</p>
        <p>{project_name}</p>
    """
    send_email(
        email_to=email_to,
        subject=subject,
        html_template=html_template,
        environment={
            "project_name": project_name,
            "username": email,
            "link": link,
        },
    ) 