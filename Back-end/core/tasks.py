from celery import shared_task
import logging

task_logger = logging.getLogger('core.task')

@shared_task
def daily_log_report():
    from django.core.mail import send_mail
    from pathlib import Path
    from django.conf import settings
    from datetime import datetime

    LOGS_DIR = Path(settings.BASE_DIR) / 'logs'
    log_file = LOGS_DIR / 'all.log'
    today_str = datetime.now().strftime('%Y-%m-%d')

    task_logger.info(f"Starting daily log report for {today_str}")

    report = {
        "users": {
            "login_count": 0,
            "failed_logins": 0,
            "registrations": 0,
            "top_ips": {},
        },
        "posts": {
            "scheduled": 0,
            "cancelled": 0,
            "retried": 0,
            "failed": 0,
            "sent": 0,
        },
        "chat": {
            "sessions_created": 0,
            "messages_sent": 0,
            "ai_errors": 0
        },
        "system": {
            "error_count": 0,
            "warning_count": 0,
        },
    }

    if not log_file.exists():
        task_logger.warning("Log file not found!")
        return "Log file not found."

    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            for line in f:
                if today_str not in line:
                    continue

                if 'registered successfully' in line and 'User' in line:
                    report["users"]["registrations"] += 1
                    ip = extract_value(line, 'IP=')
                    report["users"]["top_ips"][ip] = report["users"]["top_ips"].get(ip, 0) + 1
                if 'logged in successfully' in line and 'User' in line:
                    report["users"]["login_count"] += 1
                    ip = extract_value(line, 'IP=')
                    report["users"]["top_ips"][ip] = report["users"]["top_ips"].get(ip, 0) + 1
                if 'Failed login attempt' in line and 'IP=' in line:
                    report["users"]["failed_logins"] += 1
                    ip = extract_value(line, 'IP=')
                    report["users"]["top_ips"][ip] = report["users"]["top_ips"].get(ip, 0) + 1
                if 'Post ' in line and 'created by user' in line and 'User' in line:
                    report["posts"]["created"] += 1
                if 'scheduled for' in line and 'Post ' in line:
                    report["posts"]["scheduled"] += 1
                if 'cancelled by user' in line:
                    report["posts"]["cancelled"] += 1
                if 'posts' in line and 'retry' in line:
                    report["posts"]["retried"] += 1
                if 'send_post_task failed' in line or 'Failed to send post' in line:
                    report["posts"]["failed"] += 1
                if 'sent successfully to' in line and 'Post ' in line:
                    report["posts"]["sent"] += 1
                if 'created chat session' in line and 'User' in line:
                    report["chat"]["sessions_created"] += 1
                if 'sending message to AI' in line and 'User' in line:
                    report["chat"]["messages_sent"] += 1
                if 'Connection error to AI service' in line or 'AI service timeout' in line:
                    report["chat"]["ai_errors"] += 1
                if '[ERROR]' in line and 'django' not in line and 'core.task' not in line:
                    report["system"]["error_count"] += 1
                if '[WARNING]' in line and 'django' not in line and 'core.task' not in line:
                    report["system"]["warning_count"] += 1

    except Exception as e:
        task_logger.error(f"Error reading log file: {e}")
        return f"Failed to read log: {e}"

    message = f"""
<html>
<head>
    <style>
        body {{ font-family: Tahoma, sans-serif; direction: rtl; background: #f9f9f9; padding: 20px; }}
        .container {{ max-width: 800px; margin: auto; background: white; padding: 30px; border-radius: 12px; box-shadow: 0 0 15px rgba(0,0,0,0.1); }}
        h1 {{ color: #2c3e50; text-align: center; border-bottom: 2px solid #3498db; padding-bottom: 10px; }}
        h2 {{ color: #2980b9; margin-top: 20px; }}
        ul {{ list-style-type: none; padding: 0; }}
        li {{ margin: 8px 0; padding: 8px; background: #f1f8ff; border-right: 4px solid #3498db; border-radius: 6px; }}
        .error {{ background: #fdf2f2; border-right-color: #e74c3c; }}
        .warning {{ background: #fff9e6; border-right-color: #f39c12; }}
        .summary {{ background: #e8f5e8; padding: 15px; border-radius: 8px; margin: 20px 0; }}
        .footer {{ text-align: center; font-size: 0.9em; color: #7f8c8d; margin-top: 30px; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>گزارش روزانه عملکرد</h1>
        <p><strong>تاریخ:</strong> {today_str}</p>

        <div class="summary">
            <strong>خلاصه کلی:</strong><br>
            پست‌های ارسالی: {report["posts"]["sent"]}<br>
            ارسال مجدد: {report["posts"]["retried"]}<br>
            خطاها: {report["system"]["error_count"]} | اخطارها: {report["system"]["warning_count"]}
        </div>

        <h2>کاربران</h2>
        <ul>
            <li><strong>ورود موفق:</strong> {report["users"]["login_count"]}</li>
            <li><strong>ثبت‌نام:</strong> {report["users"]["registrations"]}</li>
            <li class="error" ><strong>تلاش ناموفق ورود:</strong> {report["users"]["failed_logins"]}</li>
        </ul>

        <h2>پست‌ها</h2>
        <ul>
            <li><strong>ارسال شده:</strong> {report["posts"]["sent"]}</li>
            <li><strong>زمان‌بندی شده:</strong> {report["posts"]["scheduled"]}</li>
            <li><strong>لغو شده:</strong> {report["posts"]["cancelled"]}</li>
            <li><strong>ارسال مجدد:</strong> {report["posts"]["retried"]}</li>
            <li class="error"><strong>ناموفق:</strong> {report["posts"]["failed"]}</li>
        </ul>

        <h2>چت هوش مصنوعی</h2>
        <ul>
            <li><strong>سشن‌های ایجاد شده:</strong> {report["chat"]["sessions_created"]}</li>
            <li><strong>پیام‌های ارسالی:</strong> {report["chat"]["messages_sent"]}</li>
            <li class="error"><strong>خطاهای هوش مصنوعی:</strong> {report["chat"]["ai_errors"]}</li>
        </ul>

        <h2>IPهای پرتردد</h2>
        <ul>
            {chr(10).join(f'<li><strong>{ip}:</strong> {cnt} بار</li>' for ip, cnt in sorted(report["users"]["top_ips"].items(), key=lambda x: -x[1])[:5])}
        </ul>

        <h2>سلامت سیستم</h2>
        <ul>
            <li><strong>خطاها:</strong> {report["system"]["error_count"]}</li>
            <li><strong>اخطارها:</strong> {report["system"]["warning_count"]}</li>
        </ul>

        <div class="footer">
            این گزارش به صورت خودکار تولید شده است — {datetime.now().strftime('%H:%M')}
        </div>
    </div>
</body>
</html>
"""

    try:
        send_mail(
            subject=f"گزارش روزانه سرویس شبکه اجتماعی - {today_str}",
            message="لطفاً از مرورگر خود برای مشاهده گزارش استفاده کنید.",
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[settings.LOGGING_EMAIL_RECIPIENTS],
            fail_silently=False,
            html_message=message
        )
        task_logger.info("Daily report email sent successfully.")
    except Exception as e:
        task_logger.error(f"Failed to send email: {e}")

    return f"Daily report completed for {today_str}."

def extract_value(line, key):
    try:
        return line.split(key)[1].split(' ')[0]
    except:
        return 'Unknown'

@shared_task
def health_check():
    import psutil
    from django.db import connection

    memory = psutil.virtual_memory().percent
    cpu = psutil.cpu_percent(interval=1)

    with connection.cursor() as cursor:
        cursor.execute("SELECT 1")
        db_ok = bool(cursor.fetchone())

    logger = logging.getLogger('core.system')
    status = f"CPU={cpu}%, Mem={memory}%, DB={'OK' if db_ok else 'ERROR'}"
    logger.info(f"Health Check: {status}")

    if memory > 85:
        logger.warning(f"High memory usage: {memory}%")
    if cpu > 90:
        logger.warning(f"High CPU usage: {cpu}%")