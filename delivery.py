import os
import re
import smtplib
import ssl
from email.message import EmailMessage
from pathlib import Path

MAX_ATTACHMENT_BYTES = 17 * 1024 * 1024
DRIVE_SCOPE = "https://www.googleapis.com/auth/drive.file"


class InvalidRecipient(ValueError):
    pass


class DeliveryConfigurationError(RuntimeError):
    pass


class DeliveryError(RuntimeError):
    pass


def _validate_recipient(recipient):
    if not isinstance(recipient, str) or len(recipient) > 254:
        raise InvalidRecipient("Vul een geldig e-mailadres in.")
    if not re.fullmatch(r"[^@\s<>]+@[^@\s<>]+\.[^@\s<>]+", recipient):
        raise InvalidRecipient("Vul een geldig e-mailadres in.")
    return recipient


def _smtp_settings():
    username = os.environ.get("SMTP_USER", "").strip()
    password = os.environ.get("SMTP_PASSWORD", "")
    if not username or not password:
        raise DeliveryConfigurationError(
            "Stel SMTP_USER en SMTP_PASSWORD in je lokale .env-bestand in. "
            "Gebruik voor Gmail een app-wachtwoord."
        )
    try:
        port = int(os.environ.get("SMTP_PORT", "587"))
    except ValueError as exc:
        raise DeliveryConfigurationError("SMTP_PORT moet een getal zijn.") from exc
    sender = os.environ.get("SMTP_FROM", username).strip()
    if not re.fullmatch(r"[^@\s<>]+@[^@\s<>]+\.[^@\s<>]+", sender):
        raise DeliveryConfigurationError("SMTP_FROM moet een geldig e-mailadres zijn.")
    return (
        os.environ.get("SMTP_HOST", "smtp.gmail.com").strip(),
        port,
        username,
        password,
        sender,
    )


def _send_smtp(message, settings):
    host, port, username, password, _ = settings
    try:
        if port == 465:
            with smtplib.SMTP_SSL(
                host, port, timeout=30, context=ssl.create_default_context()
            ) as server:
                server.login(username, password)
                server.send_message(message)
        else:
            with smtplib.SMTP(host, port, timeout=30) as server:
                server.ehlo()
                server.starttls(context=ssl.create_default_context())
                server.ehlo()
                server.login(username, password)
                server.send_message(message)
    except (OSError, smtplib.SMTPException) as exc:
        raise DeliveryError(f"E-mail verzenden mislukt: {exc}") from exc


def _drive_link(path, recipient):
    try:
        from google.auth.exceptions import GoogleAuthError
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from httplib2 import HttpLib2Error
        from googleapiclient.discovery import build
        from googleapiclient.errors import HttpError
        from googleapiclient.http import MediaIoBaseUpload
    except ImportError as exc:
        raise DeliveryConfigurationError(
            "Google Drive-ondersteuning ontbreekt. Start ClipAPP opnieuw om dependencies te installeren."
        ) from exc

    config_dir = Path.home() / ".clipapp"
    client_file = Path(
        os.environ.get(
            "GOOGLE_OAUTH_CLIENT_FILE",
            str(config_dir / "google_oauth_client.json"),
        )
    ).expanduser()
    token_file = config_dir / "google_drive_token.json"
    try:
        config_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
        if os.name != "nt":
            config_dir.chmod(0o700)
        if not client_file.is_file():
            raise DeliveryConfigurationError(
                f"Plaats je OAuth-desktopclientbestand hier: {client_file}"
            )

        credentials = None
        if token_file.is_file():
            try:
                credentials = Credentials.from_authorized_user_file(
                    str(token_file), [DRIVE_SCOPE]
                )
            except (OSError, ValueError) as exc:
                raise DeliveryConfigurationError(
                    f"Het lokale Google-tokenbestand is ongeldig: {token_file}"
                ) from exc

        if not credentials or not credentials.valid:
            if credentials and credentials.expired and credentials.refresh_token:
                credentials.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    str(client_file), [DRIVE_SCOPE]
                )
                credentials = flow.run_local_server(port=0, open_browser=True)
            token_file.write_text(credentials.to_json(), encoding="utf-8")
            if os.name != "nt":
                token_file.chmod(0o600)

        service = build("drive", "v3", credentials=credentials, cache_discovery=False)
        with path.open("rb") as video_file:
            media = MediaIoBaseUpload(
                video_file, mimetype="video/mp4", chunksize=8 * 1024 * 1024, resumable=True
            )
            uploaded = service.files().create(
                body={"name": path.name},
                media_body=media,
                fields="id,webViewLink",
            ).execute()
        file_id = uploaded.get("id")
        link = uploaded.get("webViewLink")
        if not file_id or not link:
            raise DeliveryError("Google Drive gaf geen bruikbare videolink terug.")

        service.permissions().create(
            fileId=file_id,
            body={"type": "user", "role": "reader", "emailAddress": recipient},
            sendNotificationEmail=False,
            fields="id",
        ).execute()
        return link
    except DeliveryConfigurationError:
        raise
    except (GoogleAuthError, HttpError, HttpLib2Error, OSError, ValueError) as exc:
        raise DeliveryError(f"Google Drive upload of delen mislukt: {exc}") from exc


def deliver_clip(path, recipient):
    recipient = _validate_recipient(recipient)
    path = Path(path)
    if not path.is_file() or path.suffix.lower() != ".mp4":
        raise DeliveryError("De MP4-video is niet gevonden.")

    settings = _smtp_settings()
    message = EmailMessage()
    message["From"] = settings[4]
    message["To"] = recipient
    message["Subject"] = f"Je ClipAPP-video: {path.name}"

    if path.stat().st_size <= MAX_ATTACHMENT_BYTES:
        message.set_content("Hier is je video, gemaakt met ClipAPP.")
        message.add_attachment(
            path.read_bytes(),
            maintype="video",
            subtype="mp4",
            filename=path.name,
        )
        _send_smtp(message, settings)
        return {"delivery": "attachment"}

    link = _drive_link(path, recipient)
    message.set_content(
        "Je video is te groot om als Gmail-bijlage te versturen. "
        "De video is privé gedeeld in Google Drive met dit e-mailadres:\n\n"
        f"{link}"
    )
    try:
        _send_smtp(message, settings)
    except DeliveryError as exc:
        raise DeliveryError(
            f"{exc} De video staat wel in Google Drive; gebruik deze link: {link}"
        ) from exc
    return {"delivery": "drive"}
