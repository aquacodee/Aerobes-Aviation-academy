import os


def notify_admin_new_registration(applicant):
    # Hook for SMTP/provider integration. No credentials means safe no-op.
    # Configure an email provider and implement delivery here before production.
    recipient = os.getenv("ADMIN_NOTIFICATION_EMAIL")
    if not recipient:
        return False
    return False
