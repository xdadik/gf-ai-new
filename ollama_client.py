# pyre-ignore-all-errors
import json  # type: ignore  # pyre-ignore
from typing import AsyncGenerator, Iterable, List  # type: ignore  # pyre-ignore

import aiohttp  # type: ignore  # pyre-ignore


class OllamaClient:
    def __init__(self, *, base_url: str, model: str, session: aiohttp.ClientSession):
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._session = session
    async def stream_chat(self, *, messages: List[dict[str, str]]) -> AsyncGenerator[str, None]:  # type: ignore  # pyre-ignore
        url = f"{self._base_url}/api/chat"
        payload = {
            "model": self._model, 
            "messages": messages, 
            "stream": True,
            "options": {"num_ctx": 2048},
            "keep_alive": -1
        }

        async with self._session.post(url, json=payload) as resp:
            resp.raise_for_status()

            buffer = b""
            async for chunk in resp.content.iter_any():
                if not chunk:
                    continue
                buffer += chunk
                while b"\n" in buffer:
                    line, buffer = buffer.split(b"\n", 1)
                    line = line.strip()
                    if not line:
                        continue
                    data = json.loads(line.decode("utf-8", errors="replace"))
                    if data.get("error"):
                        raise RuntimeError(data["error"])
                    text = (data.get("message") or {}).get("content")
                    if text:
                        yield text
                    if data.get("done") is True:
                        return

            if buffer.strip():
                data = json.loads(buffer.decode("utf-8", errors="replace"))
                text = (data.get("message") or {}).get("content")
                if text:
                    yield text


