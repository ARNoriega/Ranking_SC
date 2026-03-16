"""Modelos de dominio definidos por el diagrama de clases."""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel, ConfigDict, model_validator


class Player(BaseModel):
    gamer_tag: str
    model_config = ConfigDict(extra="forbid")


class SetResult(BaseModel):
    winner_id: int
    loser_id: int
    score: str


class TorneoNormalizado(BaseModel):
    fecha: date
    nombre: str
    entrants: list[Player]
    sets: list[SetResult]
    placements: dict[int, int]


class RankingEntry(BaseModel):
    player: Player
    score_total_raw: float
    score_total_normalized: float | None = None
    score_results_raw: float | None = None
    score_results_normalized: float | None = None
    score_h2h_raw: float | None = None
    score_h2h_normalized: float | None = None


class RankingTable(BaseModel):
    entries: list[RankingEntry]

    @model_validator(mode="after")
    def sort_entries(self) -> "RankingTable":
        self.entries = sorted(
            self.entries,
            key=lambda entry: entry.score_total_raw,
            reverse=True,
        )
        return self