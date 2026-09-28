from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from threading import Lock
from collections import defaultdict


@dataclass(slots=True)
class Candidate:
    id: int
    name: str
    color: str
    score: int = 0


@dataclass(slots=True)
class Voter:
    id: int
    name: str
    has_voted: bool = False


class CandidateVoteGame:
    def __init__(self, candidates: list[Candidate], voters: list[Voter] | None = None) -> None:
        if not candidates:
            raise ValueError("Debe haber al menos un candidato.")
        self.candidates = candidates
        self.voters = voters or []
        self.votes: dict[int, int] = {}
        self.created_at = datetime.now().isoformat(timespec="seconds")
        self.updated_at = self.created_at
        self._lock = Lock()

    def add_vote(self, voter_id: int, candidate_id: int) -> bool:
        with self._lock:
            voter = next((v for v in self.voters if v.id == voter_id), None)
            if voter is None or voter.has_voted:
                return False
            for candidate in self.candidates:
                if candidate.id == candidate_id:
                    candidate.score += 1
                    voter.has_voted = True
                    self.votes[voter_id] = candidate_id
                    self.updated_at = datetime.now().isoformat(timespec="seconds")
                    return True
        return False

    def snapshot(self) -> list[Candidate]:
        with self._lock:
            return [Candidate(c.id, c.name, c.color, c.score) for c in self.candidates]

    def voters_snapshot(self) -> list[Voter]:
        with self._lock:
            return [Voter(v.id, v.name, v.has_voted) for v in self.voters]

    def vote_names_by_candidate(self) -> dict[int, list[str]]:
        with self._lock:
            voter_names = {v.id: v.name for v in self.voters}
            names: dict[int, list[str]] = defaultdict(list)
            for voter_id, candidate_id in self.votes.items():
                if voter_id in voter_names:
                    names[candidate_id].append(voter_names[voter_id])
            return dict(names)
