import unittest

from services.downloader import normalize_video_url


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


if __name__ == "__main__":
    unittest.main()
