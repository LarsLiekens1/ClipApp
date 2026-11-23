import base64
import os
import re
from email.message import EmailMessage
from pathlib import Path

MAX_ATTACHMENT_BYTES = 17 * 1024 * 1024
GMAIL_SEND_SCOPE = "https://www.googleapis.com/auth/gmail.send"
DRIVE_SCOPE = "https://www.googleapis.com/auth/drive.file"
YOUTUBE_UPLOAD_SCOPE = "https://www.googleapis.com/auth/youtube.upload"
YOUTUBE_PRIVACY = ("private", "unlisted", "public")


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


def _google_credentials(scopes, token_name):
    try:
        from google.auth.exceptions import GoogleAuthError
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from oauthlib.oauth2.rfc6749.errors import OAuth2Error
        from requests.exceptions import RequestException
    except ImportError as exc:
        raise DeliveryConfigurationError(
            "Google OAuth-ondersteuning ontbreekt. Start ClipAPP opnieuw om dependencies te installeren."
        ) from exc

    config_dir = Path.home() / ".clipapp"
    client_file = Path(
        os.environ.get(
            "GOOGLE_OAUTH_CLIENT_FILE",
            str(config_dir / "google_oauth_client.json"),
        )
    ).expanduser()
    token_file = config_dir / token_name
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
                    str(token_file), scopes
                )
            except (OSError, ValueError) as exc:
                raise DeliveryConfigurationError(
                    f"Het lokale Google-tokenbestand is ongeldig: {token_file}"
                ) from exc

        if not credentials or not credentials.valid:
            if credentials and credentials.expired and credentials.refresh_token:
                credentials.refresh(Request())
            else:
                try:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        str(client_file), scopes
                    )
                except (OSError, ValueError) as exc:
                    raise DeliveryConfigurationError(
                        f"Het Google OAuth-clientbestand is ongeldig: {client_file}"
                    ) from exc
                credentials = flow.run_local_server(port=0, open_browser=True)

            try:
                token_file.write_text(credentials.to_json(), encoding="utf-8")
                if os.name != "nt":
                    token_file.chmod(0o600)
            except OSError as exc:
                raise DeliveryConfigurationError(
                    f"Het Google-tokenbestand kon niet worden opgeslagen: {token_file}"
                ) from exc

        return credentials
    except DeliveryConfigurationError:
        raise
    except (GoogleAuthError, OAuth2Error, RequestException, OSError, ValueError) as exc:
        raise DeliveryError(f"Google OAuth-aanmelding mislukt: {exc}") from exc


def _gmail_send(message):
    try:
        from httplib2 import HttpLib2Error
        from googleapiclient.discovery import build
        from googleapiclient.errors import HttpError
    except ImportError as exc:
        raise DeliveryConfigurationError(
            "Gmail API-ondersteuning ontbreekt. Start ClipAPP opnieuw om dependencies te installeren."
        ) from exc

    credentials = _google_credentials(
        [GMAIL_SEND_SCOPE], "google_gmail_token.json"
    )
    raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode("ascii")
    try:
        sent = (
            build("gmail", "v1", credentials=credentials, cache_discovery=False)
            .users()
            .messages()
            .send(userId="me", body={"raw": raw_message})
            .execute()
        )
        if not sent.get("id"):
            raise DeliveryError("Gmail heeft geen bevestiging van de verzending teruggegeven.")
    except DeliveryError:
        raise
    except (HttpError, HttpLib2Error, OSError, ValueError) as exc:
        raise DeliveryError(f"Gmail e-mail verzenden mislukt: {exc}") from exc


def _drive_link(path, recipient):
    try:
        from google.auth.exceptions import GoogleAuthError
        from httplib2 import HttpLib2Error
        from googleapiclient.discovery import build
        from googleapiclient.errors import HttpError
        from googleapiclient.http import MediaIoBaseUpload
    except ImportError as exc:
        raise DeliveryConfigurationError(
            "Google Drive-ondersteuning ontbreekt. Start ClipAPP opnieuw om dependencies te installeren."
        ) from exc

    credentials = _google_credentials([DRIVE_SCOPE], "google_drive_token.json")
    try:
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

    sender = os.environ.get("GMAIL_FROM", "").strip()
    if not re.fullmatch(r"[^@\s<>]+@[^@\s<>]+\.[^@\s<>]+", sender):
        raise DeliveryConfigurationError(
            "Stel GMAIL_FROM in op het e-mailadres van het Google-account waarmee je inlogt."
        )

    message = EmailMessage()
    message["From"] = sender
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
        _gmail_send(message)
        return {"delivery": "attachment"}

    link = _drive_link(path, recipient)
    message.set_content(
        "Je video is te groot om als Gmail-bijlage te versturen. "
        "De video is privé gedeeld in Google Drive met dit e-mailadres:\n\n"
        f"{link}"
    )
    try:
        _gmail_send(message)
    except DeliveryError as exc:
        raise DeliveryError(
            f"{exc} De video staat wel in Google Drive; gebruik deze link: {link}"
        ) from exc
    return {"delivery": "drive"}


def upload_youtube_short(path, title, description="", privacy="private"):
    """Upload een clip naar je eigen YouTube-kanaal (gratis via de YouTube Data API).
    Standaard privé. Verticale video's tot 3 minuten worden door YouTube als Short getoond."""
    path = Path(path)
    if not path.is_file() or path.suffix.lower() != ".mp4":
        raise DeliveryError("De MP4-video is niet gevonden.")
    if privacy not in YOUTUBE_PRIVACY:
        raise DeliveryError("Kies privé, niet vermeld of openbaar.")
    title = " ".join(str(title or "").split()) or path.stem
    if "#shorts" not in title.lower():
        title = f"{title[:91].rstrip()} #Shorts"
    title = title[:100]
    description = str(description or "")[:4900]
    try:
        from google.auth.exceptions import GoogleAuthError
        from httplib2 import HttpLib2Error
        from googleapiclient.discovery import build
        from googleapiclient.errors import HttpError
        from googleapiclient.http import MediaIoBaseUpload
    except ImportError as exc:
        raise DeliveryConfigurationError(
            "YouTube API-ondersteuning ontbreekt. Start ClipAPP opnieuw om dependencies te installeren."
        ) from exc

    credentials = _google_credentials([YOUTUBE_UPLOAD_SCOPE], "google_youtube_token.json")
    try:
        service = build("youtube", "v3", credentials=credentials, cache_discovery=False)
        with path.open("rb") as video_file:           # bestand netjes sluiten (Windows)
            request = service.videos().insert(
                part="snippet,status",
                body={
                    "snippet": {"title": title, "description": description, "categoryId": "22"},
                    "status": {"privacyStatus": privacy, "selfDeclaredMadeForKids": False},
                },
                media_body=MediaIoBaseUpload(video_file, mimetype="video/mp4",
                                             chunksize=8 * 1024 * 1024, resumable=True),
            )
            response = None
            while response is None:
                _, response = request.next_chunk()
        video_id = response.get("id")
        if not video_id:
            raise DeliveryError("YouTube gaf geen video-id terug.")
        return {"id": video_id, "url": f"https://youtube.com/shorts/{video_id}",
                "privacy": response.get("status", {}).get("privacyStatus", privacy)}
    except DeliveryError:
        raise
    except HttpError as exc:
        if "quota" in str(exc).lower():
            raise DeliveryError(
                "Het gratis dagquotum van de YouTube API is op. "
                "Probeer het morgen opnieuw."
            ) from exc
        raise DeliveryError(f"Uploaden naar YouTube mislukt: {exc}") from exc
    except (GoogleAuthError, HttpLib2Error, OSError, ValueError) as exc:
        raise DeliveryError(f"Uploaden naar YouTube mislukt: {exc}") from exc
