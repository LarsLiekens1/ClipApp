import base64
import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

import delivery
import app as clipapp


class DeliveryTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.video = Path(self.temp_dir.name) / "clip_01.mp4"
        self.video.write_bytes(b"sample video")
        self.gmail_env = patch.dict(
            os.environ, {"GMAIL_FROM": "sender@example.com"}
        )
        self.gmail_env.start()
        self.addCleanup(self.gmail_env.stop)

    def test_sends_small_video_as_gmail_attachment(self):
        with patch.object(delivery, "_gmail_send") as send_gmail:
            result = delivery.deliver_clip(self.video, "recipient@example.com")

        self.assertEqual(result, {"delivery": "attachment"})
        message = send_gmail.call_args.args[0]
        self.assertEqual(message["From"], "sender@example.com")
        self.assertEqual(message["To"], "recipient@example.com")
        attachment = message.get_payload()[1]
        self.assertEqual(attachment.get_filename(), "clip_01.mp4")
        self.assertEqual(attachment.get_payload(decode=True), b"sample video")

    def test_sends_drive_link_for_large_video_using_gmail(self):
        with self.video.open("wb") as file:
            file.truncate(delivery.MAX_ATTACHMENT_BYTES + 1)

        with (
            patch.object(delivery, "_drive_link", return_value="https://drive.example/video") as drive,
            patch.object(delivery, "_gmail_send") as send_gmail,
        ):
            result = delivery.deliver_clip(self.video, "recipient@example.com")

        self.assertEqual(result, {"delivery": "drive"})
        drive.assert_called_once_with(self.video, "recipient@example.com")
        self.assertIn("https://drive.example/video", send_gmail.call_args.args[0].get_content())

    def test_rejects_invalid_recipient(self):
        with patch.object(delivery, "_gmail_send") as send_gmail:
            with self.assertRaises(delivery.InvalidRecipient):
                delivery.deliver_clip(self.video, "not-an-email")

        send_gmail.assert_not_called()

    def test_requires_a_valid_gmail_sender(self):
        with (
            patch.dict(os.environ, {"GMAIL_FROM": "invalid"}, clear=False),
            patch.object(delivery, "_gmail_send") as send_gmail,
            self.assertRaises(delivery.DeliveryConfigurationError),
        ):
            delivery.deliver_clip(self.video, "recipient@example.com")

        send_gmail.assert_not_called()

    def test_gmail_api_sends_raw_message_as_authenticated_user(self):
        message = delivery.EmailMessage()
        message["To"] = "recipient@example.com"
        message["Subject"] = "ClipAPP test"
        message.set_content("Testbericht")
        credentials = object()
        service = Mock()
        service.users.return_value.messages.return_value.send.return_value.execute.return_value = {
            "id": "gmail-message"
        }

        with (
            patch.object(delivery, "_google_credentials", return_value=credentials) as get_credentials,
            patch("googleapiclient.discovery.build", return_value=service) as build,
        ):
            delivery._gmail_send(message)

        get_credentials.assert_called_once_with(
            [delivery.GMAIL_SEND_SCOPE], "google_gmail_token.json"
        )
        build.assert_called_once_with(
            "gmail", "v1", credentials=credentials, cache_discovery=False
        )
        call = service.users.return_value.messages.return_value.send
        call.assert_called_once()
        sent_message = base64.urlsafe_b64decode(call.call_args.kwargs["body"]["raw"])
        self.assertIn(b"To: recipient@example.com", sent_message)
        self.assertIn(b"Testbericht", sent_message)

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
        flow = SimpleNamespace(run_local_server=Mock(return_value=credentials))
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
        flow.run_local_server.assert_called_once_with(port=0, open_browser=True)
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
