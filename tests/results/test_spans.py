from indico_toolkit.results import Span


class TestV1Span:
    @staticmethod
    def test_pre_review() -> None:
        span = Span._from_v1_result(
            {
                "start": 33,
                "end": 62,
                "page_num": 1,
            },
        )

        assert span.start == 33
        assert span.end == 62
        assert span.page == 1

    @staticmethod
    def test_post_review() -> None:
        span = Span._from_v1_result(
            {
                "start": 33,
                "end": 62,
                "pageNum": 1,
            },
        )

        assert span.start == 33
        assert span.end == 62
        assert span.page == 1

    @staticmethod
    def test_post_review_manually_entered() -> None:
        span = Span._from_v1_result(
            {
                "pageNum": 1,
            },
        )

        assert span.start is None
        assert span.end is None
        assert span.page == 1
