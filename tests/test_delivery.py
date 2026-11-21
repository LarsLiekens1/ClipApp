import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, Mock, patch

import delivery
import app as clipapp


class DeliveryTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.video = Path(self.temp_dir.name) / "clip_01.mp4"
        self.video.write_bytes(b"sample video")
        self.smtp_env = patch.dict(
            os.environ,
            {
                "SMTP_HOST": "smtp.example.com",
                "SMTP_PORT": "587",
                "SMTP_USER": "sender@example.com",
                "SMTP_PASSWORD": "test-password",
                "SMTP_FROM": "sender@example.com",
            },
            clear=True,
        )
        self.smtp_env.start()
        self.addCleanup(self.smtp_env.stop)

    def test_sends_small_video_as_attachment(self):
        with patch.object(delivery, "_send_smtp") as send_smtp:
            result = delivery.deliver_clip(self.video, "recipient@example.com")

        self.assertEqual(result, {"delivery": "attachment"})
        message = send_smtp.call_args.args[0]
        self.assertEqual(message["To"], "recipient@example.com")
        attachment = message.get_payload()[1]
        self.assertEqual(attachment.get_filename(), "clip_01.mp4")
        self.assertEqual(attachment.get_payload(decode=True), b"sample video")

    def test_sends_drive_link_for_video_over_attachment_limit(self):
        with self.video.open("wb") as file:
            file.truncate(delivery.MAX_ATTACHMENT_BYTES + 1)

        with (
            patch.object(delivery, "_drive_link", return_value="https://drive.example/video") as drive,
            patch.object(delivery, "_send_smtp") as send_smtp,
        ):
            result = delivery.deliver_clip(self.video, "recipient@example.com")

        self.assertEqual(result, {"delivery": "drive"})
        drive.assert_called_once_with(self.video, "recipient@example.com")
        self.assertIn("https://drive.example/video", send_smtp.call_args.args[0].get_content())

    def test_rejects_invalid_recipient(self):
        with patch.object(delivery, "_send_smtp") as send_smtp:
            with self.assertRaises(delivery.InvalidRecipient):
                delivery.deliver_clip(self.video, "not-an-email")

        send_smtp.assert_not_called()

    def test_smtp_uses_starttls_before_authentication(self):
        message = delivery.EmailMessage()
        connection = MagicMock()
        context = MagicMock()
        context.__enter__.return_value = connection

        with patch.object(delivery.smtplib, "SMTP", return_value=context):
            delivery._send_smtp(
                message,
                ("smtp.example.com", 587, "sender@example.com", "test-password",
                 "sender@example.com"),
            )

        connection.starttls.assert_called_once()
        connection.login.assert_called_once_with("sender@example.com", "test-password")
        connection.send_message.assert_called_once_with(message)

    def test_email_route_is_disabled_outside_desktop_mode(self):
        with patch.dict(os.environ, {"CLIPAPP_LOCAL_MODE": "0"}):
            response = clipapp.app.test_client().post(
                "/api/send-video",
                json={"job": "0123456789ab", "name": "clip_01.mp4",
                      "recipient": "recipient@example.com"},
                environ_base={"REMOTE_ADDR": "127.0.0.1"},
            )

        self.assertEqual(response.status_code, 403)

    def test_email_route_rejects_non_local_clients(self):
        with patch.dict(os.environ, {"CLIPAPP_LOCAL_MODE": "1"}):
            response = clipapp.app.test_client().post(
                "/api/send-video",
                json={"job": "0123456789ab", "name": "clip_01.mp4",
                      "recipient": "recipient@example.com"},
                environ_base={"REMOTE_ADDR": "192.0.2.1"},
            )

        self.assertEqual(response.status_code, 403)

    def test_email_route_sends_only_a_clip_from_the_requested_job(self):
        job = "0123456789ab"
        work = Path(self.temp_dir.name) / "work"
        job_dir = work / job
        job_dir.mkdir(parents=True)
        videos = [job_dir / name for name in ("clip_01.mp4", "bewerkt_123456.mp4")]
        for video in videos:
            video.write_bytes(b"sample video")

        with (
            patch.object(clipapp, "WORK", work),
            patch.object(clipapp, "deliver_clip", return_value={"delivery": "attachment"}) as send,
            patch.dict(os.environ, {"CLIPAPP_LOCAL_MODE": "1"}),
        ):
            for video in videos:
                response = clipapp.app.test_client().post(
                    "/api/send-video",
                    json={"job": job, "name": video.name, "recipient": "recipient@example.com"},
                    environ_base={"REMOTE_ADDR": "127.0.0.1"},
                )
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.json["delivery"], "attachment")

        self.assertEqual(send.call_count, 2)

    def test_drive_share_is_private_to_the_recipient(self):
        root = Path(self.temp_dir.name)
        config_dir = root / ".clipapp"
        config_dir.mkdir()
        (config_dir / "google_oauth_client.json").write_text("{}", encoding="utf-8")
        credentials = SimpleNamespace(valid=True, to_json=lambda: '{"token":"local"}')
        flow = SimpleNamespace(run_local_server=lambda **kwargs: credentials)
        service = Mock()
        service.files.return_value.create.return_value.execute.return_value = {
            "id": "drive-file",
            "webViewLink": "https://drive.example/video",
        }

        with (
            patch.object(Path, "home", return_value=root),
            patch.dict(os.environ, {}, clear=True),
            patch(
                "google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file",
                return_value=flow,
            ),
            patch("googleapiclient.discovery.build", return_value=service),
        ):
            link = delivery._drive_link(self.video, "recipient@example.com")

        self.assertEqual(link, "https://drive.example/video")
        service.permissions.return_value.create.assert_called_once_with(
            fileId="drive-file",
            body={
                "type": "user",
                "role": "reader",
                "emailAddress": "recipient@example.com",
            },
            sendNotificationEmail=False,
            fields="id",
        )


if __name__ == "__main__":
    unittest.main()
