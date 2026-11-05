from django.core.mail.backends.console import EmailBackend


class ConsoleEmailBackend(EmailBackend):
    """Print development emails without MIME wrapping verification links."""

    def write_message(self, message):
        self.stream.write(f"Subject: {message.subject}\n")
        self.stream.write(f"To: {', '.join(message.to)}\n\n")
        self.stream.write(f"{message.body}\n")
        self.stream.write("-" * 79 + "\n")
