from src.services.jokes import JokeService, JokeItem


def test_get_joke_from_feed_and_bind_vote():
    service = JokeService()

    def fake_fetch():
        return [
            JokeItem(title="Анекдот 1", text="Текст 1"),
            JokeItem(title="Анекдот 2", text="Текст 2"),
        ]

    service._fetch_feed = fake_fetch  # type: ignore[attr-defined]

    joke = service.get_joke()
    assert joke is not None

    service.bind_sent_message(101, joke)
    assert service.vote(101, liked=False) is True


def test_disliked_joke_gets_filtered_out():
    service = JokeService(min_rating_to_serve=-1)
    bad = JokeItem(title="Плохой", text="Шутка")
    good = JokeItem(title="Норм", text="Шутка")

    service._pool = [bad, good]
    service.bind_sent_message(1, bad)
    assert service.vote(1, liked=False) is True
    assert service.vote(1, liked=False) is True  # рейтинг <= -2

    picked = service.get_joke()
    assert picked is not None
    assert picked.title == "Норм"


def test_vote_unknown_message_returns_false():
    service = JokeService()
    assert service.vote(9999, liked=True) is False
