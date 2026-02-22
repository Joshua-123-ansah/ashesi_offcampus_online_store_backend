"""
SMTP backend that skips SSL verification (for local dev when system certs fail).
Set EMAIL_SSL_VERIFY=0 in .env to use it. Do not use in production.
"""
import ssl

from django.core.mail.backends.smtp import EmailBackend as SMTPBackend


class SMTPBackendNoVerify(SMTPBackend):
    """Same as SMTP but uses unverified SSL context so sending works without system certs."""

    @property
    def ssl_context(self):
        return ssl._create_unverified_context()
