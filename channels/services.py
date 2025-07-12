import requests
from django.conf import settings
from django.utils.translation import gettext_lazy as _


def verify_telegram_channel(username: str):
    """
    بررسی می‌کند که آیا ربات تلگرام توانایی ارسال پیام در کانال را دارد یا خیر.
    """
    token = settings.TELEGRAM_BOT_TOKEN
    test_message = "در حال بررسی دسترسی ربات برای ارسال پست..."
    api_url = f"https://api.telegram.org/bot{token}/sendMessage"

    try:
        response = requests.post(api_url, json={
            "chat_id": username,
            "text": test_message
        }, timeout=5)

        if response.status_code == 200:
            return True, ""
        else:
            error_text = response.json().get("description", "خطای ناشناخته از سمت تلگرام")
            return False, error_text

    except requests.exceptions.RequestException as e:
        return False, f"خطا در اتصال به سرور تلگرام: {str(e)}"


def verify_bale_channel(username: str):
    """
    در آینده: بررسی اتصال ربات بله به کانال.
    فعلاً به صورت پیش‌فرض غیرفعال است.
    """
    return False, _("فعلاً اتصال به بله پیاده‌سازی نشده است.")


def verify_channel(platform: str, username: str):
    """
    تابع سوییچ بین پلتفرم‌ها برای اعتبارسنجی کانال.
    """
    if platform == "telegram":
        return verify_telegram_channel(username)
    elif platform == "bale":
        return verify_bale_channel(username)
    else:
        return False, _("پلتفرم ناشناخته است.")
