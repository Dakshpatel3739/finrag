"""Locust load driver for the FinRAG Phase 5 burst.

WHAT: sends realistic query traffic to the chain-server /query endpoint by
default, or directly to an LLM NIM chat-completions endpoint when configured.
WHY: HPA proof needs sustained GPU work so replicas climb under load.
"""

from __future__ import annotations

import os
import random
from typing import Any

from locust import HttpUser, between, task

QUESTIONS = [
    "Summarize the main revenue risks in the latest uploaded 10-K.",
    "Which business segment had the strongest margin improvement?",
    "List debt maturities mentioned in the filing with citations.",
    "Compare cash flow from operations against net income.",
    "What did management say about supply chain exposure?",
    "Find acquisition-related risks and cite the source pages.",
    "Explain the largest year-over-year expense changes.",
    "Which disclosed controls affect financial reporting?",
]


class FinRAGUser(HttpUser):
    """A Locust user that generates RAG-style query pressure."""

    # WHY: short think time creates steady load without unrealistic request spam.
    wait_time = between(1, 4)

    def on_start(self) -> None:
        """Acquire a bearer token unless one was supplied.

        Environment:
        - FINRAG_TARGET_MODE=chain|nim
        - FINRAG_BEARER_TOKEN=<already-issued-token>
        - FINRAG_USERNAME and FINRAG_PASSWORD for /auth/login
        """

        self.target_mode = os.getenv("FINRAG_TARGET_MODE", "chain").strip().lower()
        self.bearer_token = os.getenv("FINRAG_BEARER_TOKEN", "").strip()
        self.nim_model = os.getenv("FINRAG_NIM_MODEL", "meta/llama-3.1-8b-instruct")

        if self.target_mode == "nim":
            # Direct NIM mode usually relies on internal networking or an auth
            # sidecar. The bearer token is optional here.
            return

        if self.bearer_token:
            return

        username = os.getenv("FINRAG_USERNAME", "owner@example.com")
        password = os.getenv("FINRAG_PASSWORD", "change-me")
        with self.client.post(
            "/auth/login",
            json={"email": username, "password": password},
            name="/auth/login",
            catch_response=True,
        ) as response:
            if response.status_code != 200:
                response.failure(f"login failed: {response.status_code} {response.text[:120]}")
                return
            payload: dict[str, Any] = response.json()
            self.bearer_token = str(payload.get("access_token", ""))
            if not self.bearer_token:
                response.failure("login response did not include access_token")

    @task(5)
    def query_chain_server(self) -> None:
        """Drive the FinRAG API path used by users."""

        if self.target_mode == "nim":
            self.query_nim_direct()
            return

        headers = {"Authorization": f"Bearer {self.bearer_token}"} if self.bearer_token else {}
        question = random.choice(QUESTIONS)
        with self.client.post(
            "/query",
            json={"question": question},
            headers=headers,
            name="/query",
            catch_response=True,
        ) as response:
            if response.status_code >= 500:
                response.failure(f"server error: {response.status_code} {response.text[:120]}")
            elif response.status_code in {401, 403}:
                response.failure("auth failed; set FINRAG_BEARER_TOKEN or login env vars")

    def query_nim_direct(self) -> None:
        """Optionally bypass the API and hit an LLM NIM directly.

        WHY: direct mode isolates GPU/HPA behavior if chain-server auth or Milvus
        wiring is not ready during the burst.
        """

        headers = {"Content-Type": "application/json"}
        if self.bearer_token:
            headers["Authorization"] = f"Bearer {self.bearer_token}"

        prompt = random.choice(QUESTIONS)
        self.client.post(
            "/v1/chat/completions",
            json={
                "model": self.nim_model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 256,
                "temperature": 0.2,
                "stream": False,
            },
            headers=headers,
            name="/v1/chat/completions",
        )
