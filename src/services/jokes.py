import logging
import random
import re
from dataclasses import dataclass
from html import unescape
from typing import List, Optional
import xml.etree.ElementTree as ET

import requests


@dataclass
class JokeItem:
    title: str
    text: str


class JokeService:
    """Сервис получения анекдотов с anekdot.ru + простая адаптация по фидбеку."""

    def __init__(
        self,
        feed_url: str = "https://www.anekdot.ru/rss/export_j.xml",
        timeout: int = 10,
        min_rating_to_serve: int = -2,
    ):
        self.feed_url = feed_url
        self.timeout = timeout
        self.min_rating_to_serve = min_rating_to_serve
        self._session = requests.Session()
        self._pool: List[JokeItem] = []
        self._ratings: dict[str, int] = {}
        self._served_by_message_id: dict[int, JokeItem] = {}

    def _normalize_text(self, text: str) -> str:
        text = unescape(text or "")
        text = re.sub(r"<[^>]+>", "", text)
        text = text.replace("\xa0", " ")
        text = re.sub(r"\s+", " ", text).strip()
        return text

    def _build_key(self, joke: JokeItem) -> str:
        return f"{joke.title}::{joke.text}".strip().lower()

    def _is_allowed(self, joke: JokeItem) -> bool:
        key = self._build_key(joke)
        return self._ratings.get(key, 0) > self.min_rating_to_serve

    def _fetch_feed(self) -> List[JokeItem]:
        response = self._session.get(self.feed_url, timeout=self.timeout)
        response.raise_for_status()

        root = ET.fromstring(response.text)
        items = root.findall(".//item")
        jokes: List[JokeItem] = []

        for item in items:
            title = self._normalize_text(item.findtext("title", default="Анекдот"))
            text = self._normalize_text(item.findtext("description", default=""))
            if text:
                jokes.append(JokeItem(title=title or "Анекдот", text=text))

        return jokes

    def _refill_pool(self) -> None:
        jokes = self._fetch_feed()
        random.shuffle(jokes)
        self._pool = jokes

    def get_joke(self) -> Optional[JokeItem]:
        attempts = 0
        while attempts < 2:
            if not self._pool:
                self._refill_pool()

            while self._pool:
                joke = self._pool.pop()
                if self._is_allowed(joke):
                    return joke

            attempts += 1
            self._pool = []

        logging.warning("JokeService: Не удалось подобрать подходящий анекдот (все зафлажены фидбеком?)")
        return None

    def bind_sent_message(self, message_id: int, joke: JokeItem) -> None:
        self._served_by_message_id[message_id] = joke

    def vote(self, message_id: int, liked: bool) -> bool:
        joke = self._served_by_message_id.get(message_id)
        if not joke:
            return False

        key = self._build_key(joke)
        delta = 1 if liked else -1
        self._ratings[key] = self._ratings.get(key, 0) + delta
        return True
