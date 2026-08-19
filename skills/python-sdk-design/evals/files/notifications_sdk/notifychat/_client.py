import requests

from ._models import Notification


class NotificationClient:
    """Client for the NotifyChat notifications service.

    :param endpoint: Service endpoint URL.
    :param credential: Credential object exposing get_token().
    :keyword timeout: Default request timeout in seconds.
    """

    def __init__(self, endpoint: str, credential, *, timeout: float = 30.0, **kwargs):
        if not endpoint:
            raise ValueError("endpoint must be a non-empty string")
        self._endpoint = endpoint.rstrip("/")
        self._credential = credential
        self._timeout = timeout
        self._session = requests.Session()

    def _headers(self) -> dict[str, str]:
        token = self._credential.get_token("https://notifychat.acme.com/.default")
        return {"Authorization": f"Bearer {token.token}"}

    def send_notification(self, notification: Notification, *, timeout: float | None = None) -> Notification:
        """Send a notification. Raises on failure."""
        resp = self._session.post(
            f"{self._endpoint}/notifications",
            json={
                "recipient": notification.recipient,
                "message": notification.message,
                "channel": str(notification.channel),
                "subject": notification.subject,
            },
            headers=self._headers(),
            timeout=timeout or self._timeout,
        )
        resp.raise_for_status()
        data = resp.json()
        notification.id = data["id"]
        notification.status = data["status"]
        return notification

    def get_notification(self, notification_id: str, *, timeout: float | None = None) -> Notification:
        """Get a previously sent notification. Raises if it does not exist."""
        if not notification_id:
            raise ValueError("notification_id must be a non-empty string")
        resp = self._session.get(
            f"{self._endpoint}/notifications/{notification_id}",
            headers=self._headers(),
            timeout=timeout or self._timeout,
        )
        resp.raise_for_status()
        data = resp.json()
        result = Notification(data["recipient"], data["message"])
        result.id = data["id"]
        result.status = data["status"]
        return result
