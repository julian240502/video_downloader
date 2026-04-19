import unittest

from services.downloader import clean_error_message, normalize_video_url, subtitle_to_text


class NormalizeVideoUrlTests(unittest.TestCase):
    def test_removes_playlist_index_param(self):
        url = (
            "https://www.youtube.com/watch?v=ffCkmSqmykU"
            "&list=PLZCMx9H1iQsZOCN0dtpp238QoihLENrLD&index=2"
        )
        self.assertEqual(
            normalize_video_url(url),
            "https://www.youtube.com/watch?v=ffCkmSqmykU&list=PLZCMx9H1iQsZOCN0dtpp238QoihLENrLD",
        )

    def test_removes_tracking_params_and_keeps_core_params(self):
        url = (
            "https://www.youtube.com/watch?v=abc123&feature=share"
            "&pp=ygUNc29tZS1wYXJhbQ%3D%3D&start_radio=1&list=PL42&t=90"
        )
        self.assertEqual(
            normalize_video_url(url),
            "https://www.youtube.com/watch?v=abc123&list=PL42&t=90",
        )

    def test_supports_youtu_be_links(self):
        url = "https://youtu.be/abc123?feature=share&pp=abcd&t=45"
        self.assertEqual(normalize_video_url(url), "https://youtu.be/abc123?t=45")

    def test_non_youtube_urls_are_unchanged(self):
        url = "https://www.facebook.com/watch/?v=123456&index=2&feature=share"
        self.assertEqual(normalize_video_url(url), url)

    def test_noop_when_no_removable_params(self):
        url = "https://www.youtube.com/watch?v=abc123&list=PL42&t=12"
        self.assertEqual(normalize_video_url(url), url)

class SubtitleToTextTests(unittest.TestCase):
    def test_converts_vtt_to_plain_text(self):
        content = """WEBVTT

00:00:00.000 --> 00:00:01.000
Hello

00:00:01.000 --> 00:00:02.000
<c.colorE5E5E5>world</c>
"""
        self.assertEqual(subtitle_to_text(content), "Hello\nworld")

    def test_removes_duplicate_lines(self):
        content = """1
00:00:00,000 --> 00:00:01,000
Hi there

2
00:00:01,000 --> 00:00:02,000
Hi there
"""
        self.assertEqual(subtitle_to_text(content), "Hi there")

    def test_keeps_non_consecutive_repeated_lines(self):
        content = """1
00:00:00,000 --> 00:00:01,000
Hi there

2
00:00:01,000 --> 00:00:02,000
Welcome

3
00:00:02,000 --> 00:00:03,000
Hi there
"""
        self.assertEqual(subtitle_to_text(content), "Hi there\nWelcome\nHi there")


class ErrorCleanupTests(unittest.TestCase):
    def test_removes_ansi_escape_sequences(self):
        raw = "\x1b[0;31mERROR:\x1b[0m Unable to download subtitles"
        self.assertEqual(clean_error_message(raw), "ERROR: Unable to download subtitles")


if __name__ == "__main__":
    unittest.main()
