import json
import logging
from urllib.error import URLError
from urllib.request import Request, urlopen

from django.db import transaction

from .models import ExpoPushToken, Notification

logger = logging.getLogger(__name__)
EXPO_PUSH_URL = "https://exp.host/--/api/v2/push/send"


def _send_expo_push(notification_id):
    notification = (
        Notification.objects.select_related("actor", "publication")
        .filter(pk=notification_id)
        .first()
    )
    if notification is None:
        return

    tokens = list(
        ExpoPushToken.objects.filter(user=notification.recipient).values_list(
            "token", flat=True
        )
    )
    if not tokens:
        return

    actor_name = notification.actor.username
    if notification.notification_type == Notification.Type.LIKE:
        title = "Nouveau J’aime"
        body = f"{actor_name} a aimé votre publication."
        data = {"type": "publication", "publication_id": notification.publication_id}
    elif notification.notification_type == Notification.Type.COMMENT:
        title = "Nouveau commentaire"
        body = f"{actor_name} a commenté votre publication."
        data = {"type": "publication", "publication_id": notification.publication_id}
    elif notification.notification_type == Notification.Type.FOLLOW:
        title = "Nouvel abonnement"
        body = f"{actor_name} a commencé à vous suivre."
        data = {"type": "profile", "user_id": notification.actor_id}
    else:
        return

    messages = [
        {
            "to": token,
            "title": title,
            "body": body,
            "sound": "default",
            "channelId": "default",
            "data": data,
        }
        for token in tokens
    ]
    request = Request(
        EXPO_PUSH_URL,
        data=json.dumps(messages).encode("utf-8"),
        headers={
            "Accept": "application/json",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urlopen(request, timeout=5) as response:
            result = json.loads(response.read().decode("utf-8"))
    except (URLError, TimeoutError, ValueError) as error:
        logger.warning("Expo push request failed for notification %s: %s", notification_id, error)
        return

    tickets = result.get("data", [])
    for token, ticket in zip(tokens, tickets):
        details = ticket.get("details") or {}
        if ticket.get("status") == "error" and details.get("error") == "DeviceNotRegistered":
            ExpoPushToken.objects.filter(token=token).delete()


def create_notification(*, recipient, actor, notification_type, publication=None):
    if recipient.pk == actor.pk:
        return None
    notification = Notification.objects.create(
        recipient=recipient,
        actor=actor,
        notification_type=notification_type,
        publication=publication,
    )
    transaction.on_commit(lambda: _send_expo_push(notification.pk))
    return notification
