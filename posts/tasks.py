from celery import shared_task
from django.utils import timezone
from .models import Post, MediaAttachment
from channels.services import send_message_to_channel


@shared_task
def send_post_task(post_id):
    try:
        post = Post.objects.get(id=post_id)
        if post.status == 'sent':
            return "Already sent."

        attachments = post.attachments.all()
        text = post.content or ""

        success, error = False, ""

        if post.types == 'text':
            success, error = send_message_to_channel(post.channel, text)

        elif post.types == 'media':
            first_media = attachments.first()
            if first_media:
                caption = f"\n\n{first_media.caption}" if first_media.caption else ''
                full_text = text + caption
                success, error = send_message_to_channel(
                    post.channel, full_text, file=first_media.file.path
                )
            else:
                error = "No media provided."

        else:
            error = "Unsupported post type."

        if success:
            post.status = 'sent'
            post.sent_at = timezone.now()
            post.error_message = ''
        else:
            post.status = 'failed'
            post.error_message = error or 'Unknown error.'

        post.save()
        return "Sent" if success else f"Failed: {error}"

    except Post.DoesNotExist:
        return "Post not found"
