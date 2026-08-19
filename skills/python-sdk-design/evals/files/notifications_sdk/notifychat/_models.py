from enum import Enum


class NotificationChannel(str, Enum):
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"


class Notification:
    """A notification to be delivered to a recipient.

    :param recipient: Address of the recipient (email, phone number, or device id).
    :param message: The message body.
    :keyword channel: Delivery channel. Defaults to EMAIL.
    :keyword subject: Optional subject line (email only).
    """

    def __init__(self, recipient: str, message: str, *,
                 channel: NotificationChannel = NotificationChannel.EMAIL,
                 subject: str | None = None):
        self.recipient = recipient
        self.message = message
        self.channel = channel
        self.subject = subject
        self.id: str | None = None  # server-assigned
        self.status: str | None = None  # server-assigned

    def __repr__(self) -> str:
        return (f"Notification(id={self.id!r}, recipient={self.recipient!r}, "
                f"channel={self.channel!r})")[:1024]
