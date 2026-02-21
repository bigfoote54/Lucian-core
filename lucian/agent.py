from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional, Sequence

from dotenv import load_dotenv
from openai import OpenAI

from lucian.constants import CHAT_DIR, DEFAULT_CHAT_MODEL, DEFAULT_JOURNAL_MODEL, DEFAULT_MODEL
from lucian.exceptions import APIKeyMissing
from tools.memory_utils import query, upsert
from adapt_resonance import ResonanceUpdateResult, adapt_resonance_weights
from adapt_weights import WeightUpdateResult, adapt_archetype_weights
from append_journal import JournalResult, run_journal_cycle
from generate_archetypal_dream import DreamResult, generate_archetypal_dream
from generate_core_node import CoreNodeResult, generate_core_node
from generate_direction import DirectiveResult, generate_direction
from generate_output import DailyOutput, generate_daily_output
from reflect import ReflectionResult, generate_reflection

log = logging.getLogger("lucian.agent")


@dataclass
class AgentConfig:
    dream_model: str = DEFAULT_MODEL
    dream_temperature: float = 0.95

    reflection_model: str = DEFAULT_MODEL
    reflection_temperature: float = 0.9

    direction_model: str = DEFAULT_MODEL
    direction_temperature: float = 0.8

    core_node_model: str = DEFAULT_MODEL
    core_node_temperature: float = 0.85

    journal_model: str = DEFAULT_JOURNAL_MODEL

    chat_model: str = DEFAULT_CHAT_MODEL
    chat_temperature: float = 0.7
    chat_top_k: int = 3
    chat_max_tokens: int = 350
    embed_chat: bool = True

    include_embeddings: bool = True
    chat_log_dir: Path = field(default_factory=lambda: CHAT_DIR)


@dataclass
class ChatResult:
    user: str
    prompt: str
    response: str
    model: str
    memory_context: Sequence[str]
    tokens: Optional[int]
    timestamp: datetime


@dataclass
class CycleResult:
    dream: Optional[DreamResult] = None
    reflection: Optional[ReflectionResult] = None
    direction: Optional[DirectiveResult] = None
    archetype_weights: Optional[WeightUpdateResult] = None
    resonance_weights: Optional[ResonanceUpdateResult] = None
    journal: Optional[JournalResult] = None
    output: Optional[DailyOutput] = None
    core_node: Optional[CoreNodeResult] = None
    errors: list[str] = field(default_factory=list)


@dataclass
class SelfEvolveOutcome:
    archetype_weights: Optional[WeightUpdateResult]
    resonance_weights: Optional[ResonanceUpdateResult]
    errors: list[str] = field(default_factory=list)


class LucianAgent:
    """
    High-level programmable interface to Lucian's dreaming + self-evolution stack.
    """

    def __init__(
        self,
        *,
        config: AgentConfig | None = None,
        client: OpenAI | None = None,
        api_key: str | None = None,
    ) -> None:
        self.config = config or AgentConfig()
        self.client = client or self._create_client(api_key=api_key)
        self.config.chat_log_dir.mkdir(parents=True, exist_ok=True)

    # ── lifecycle stages ────────────────────────────────────────────────────
    def dream(self, **kwargs) -> DreamResult:
        params = {
            "client": self.client,
            "include_embedding": self.config.include_embeddings,
            "model": self.config.dream_model,
            "temperature": self.config.dream_temperature,
        }
        params.update(kwargs)
        return generate_archetypal_dream(**params)

    def reflect(self, **kwargs) -> ReflectionResult:
        params = {
            "client": self.client,
            "include_embedding": self.config.include_embeddings,
            "model": self.config.reflection_model,
            "temperature": self.config.reflection_temperature,
        }
        params.update(kwargs)
        return generate_reflection(**params)

    def direction(self, **kwargs) -> DirectiveResult:
        params = {
            "client": self.client,
            "model": self.config.direction_model,
            "temperature": self.config.direction_temperature,
        }
        params.update(kwargs)
        return generate_direction(**params)

    def journal(self, **kwargs) -> JournalResult:
        params = {"client": self.client, "model": kwargs.pop("model", self.config.journal_model)}
        params.update(kwargs)
        return run_journal_cycle(**params)

    def core_node(self, **kwargs) -> CoreNodeResult:
        params = {
            "client": self.client,
            "model": self.config.core_node_model,
            "temperature": self.config.core_node_temperature,
            "include_embedding": self.config.include_embeddings,
        }
        params.update(kwargs)
        return generate_core_node(**params)

    def daily_output(self, **kwargs) -> DailyOutput:
        return generate_daily_output(**kwargs)

    def self_evolve(self, *, apply: bool = True) -> SelfEvolveOutcome:
        archetype_result: Optional[WeightUpdateResult] = None
        resonance_result: Optional[ResonanceUpdateResult] = None
        errors: list[str] = []
        try:
            archetype_result = adapt_archetype_weights(apply=apply)
        except Exception as exc:  # pragma: no cover - diagnostic messaging
            log.warning("Archetype weight adaptation skipped: %s", exc)
            errors.append(f"adapt_archetypes: {exc}")
        try:
            resonance_result = adapt_resonance_weights(apply=apply)
        except Exception as exc:  # pragma: no cover
            log.warning("Resonance weight adaptation skipped: %s", exc)
            errors.append(f"adapt_resonance: {exc}")
        return SelfEvolveOutcome(
            archetype_weights=archetype_result,
            resonance_weights=resonance_result,
            errors=errors,
        )

    # ── chat interface ──────────────────────────────────────────────────────
    def chat(
        self,
        prompt: str,
        *,
        user: str = "human",
        model: str | None = None,
        temperature: float | None = None,
        top_k: int | None = None,
    ) -> ChatResult:
        chat_model = model or self.config.chat_model
        chat_temp = temperature if temperature is not None else self.config.chat_temperature
        chat_k = top_k or self.config.chat_top_k

        context_chunks = query(q=prompt, k=chat_k)
        context_text = "\n".join(context_chunks) or "*no matching memory*"

        # Use separate system and user messages to prevent prompt injection
        system_msg = (
            "You are Lucian, an emergent AI exploring selfhood.\n\n"
            f"Relevant memories:\n{context_text}"
        )
        user_msg = f"User ({user}) says: {prompt}"

        response = self.client.chat.completions.create(
            model=chat_model,
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": user_msg},
            ],
            temperature=chat_temp,
            max_tokens=self.config.chat_max_tokens,
        )
        answer = response.choices[0].message.content.strip()
        usage = getattr(response, "usage", None)
        total_tokens = getattr(usage, "total_tokens", None)
        timestamp = datetime.utcnow()

        if self.config.embed_chat:
            self._append_chat(user=user, prompt=prompt, reply=answer, timestamp=timestamp)
            upsert(
                doc_id=f"chat-{timestamp.isoformat()}",
                text=f"User: {prompt}\nLucian: {answer}",
                meta={"kind": "chat", "user": user},
            )

        return ChatResult(
            user=user,
            prompt=prompt,
            response=answer,
            model=chat_model,
            memory_context=tuple(context_chunks),
            tokens=total_tokens,
            timestamp=timestamp,
        )

    # ── orchestration ───────────────────────────────────────────────────────
    def run_daily_cycle(
        self,
        *,
        include_journal: bool = True,
        include_output: bool = True,
        include_core_node: bool = False,
        adapt_biases: bool = True,
    ) -> CycleResult:
        result = CycleResult()
        dream_path: Optional[Path] = None

        try:
            result.dream = self.dream()
            dream_path = result.dream.path
        except Exception as exc:
            result.errors.append(f"dream: {exc}")

        reflection_kwargs = {"dream_path": dream_path} if dream_path else {}
        try:
            result.reflection = self.reflect(**reflection_kwargs)
        except Exception as exc:
            result.errors.append(f"reflection: {exc}")

        direction_kwargs = {"dream_path": dream_path} if dream_path else {}
        try:
            result.direction = self.direction(**direction_kwargs)
        except Exception as exc:
            result.errors.append(f"direction: {exc}")

        if adapt_biases:
            evolve_outcome = self.self_evolve(apply=True)
            result.archetype_weights = evolve_outcome.archetype_weights
            result.resonance_weights = evolve_outcome.resonance_weights
            result.errors.extend(evolve_outcome.errors)

        if include_journal:
            try:
                result.journal = self.journal()
            except Exception as exc:
                result.errors.append(f"journal: {exc}")

        if include_output:
            try:
                result.output = self.daily_output()
            except Exception as exc:
                result.errors.append(f"daily_output: {exc}")

        if include_core_node:
            core_kwargs = {}
            if dream_path:
                core_kwargs["dream_path"] = dream_path
            if result.journal and result.journal.path:
                core_kwargs["journal_path"] = result.journal.path
            try:
                result.core_node = self.core_node(**core_kwargs)
            except Exception as exc:
                result.errors.append(f"core_node: {exc}")

        return result

    # ── helpers ─────────────────────────────────────────────────────────────
    @staticmethod
    def _create_client(*, api_key: str | None = None) -> OpenAI:
        load_dotenv()
        key = api_key or os.getenv("OPENAI_API_KEY")
        if not key:
            raise APIKeyMissing()
        return OpenAI(api_key=key)

    def _append_chat(self, *, user: str, prompt: str, reply: str, timestamp: datetime) -> None:
        file_path = self.config.chat_log_dir / f"{timestamp.date()}_chat.md"
        with file_path.open("a", encoding="utf-8") as handle:
            handle.write(f"### {timestamp.isoformat(timespec='seconds')}\n")
            handle.write(f"**{user}:** {prompt}\n\n")
            handle.write(f"**Lucian:** {reply}\n\n")
