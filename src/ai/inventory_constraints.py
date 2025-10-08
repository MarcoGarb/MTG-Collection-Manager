 # src/ai/inventory_constraints.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, Iterable, Optional, Sequence, Set, Tuple
import unicodedata
import re


def normalize_name(name: str) -> str:
    """
    Normalize card names to a consistent key:
    - strip accents
    - lowercase
    - keep alphanumerics and spaces
    - collapse multiple spaces
    """
    if not isinstance(name, str):
        name = str(name)
    # strip accents
    name_nfkd = unicodedata.normalize("NFKD", name)
    ascii_only = "".join(ch for ch in name_nfkd if not unicodedata.combining(ch))
    # lowercase, keep alnum + space
    cleaned = re.sub(r"[^a-z0-9\s]", " ", ascii_only.lower())
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


# Normalized names
BASIC_LANDS: Set[str] = {
    normalize_name("Plains"),
    normalize_name("Island"),
    normalize_name("Swamp"),
    normalize_name("Mountain"),
    normalize_name("Forest"),
    normalize_name("Wastes"),
}


@dataclass(frozen=True)
class QuantityViolation:
    name: str
    need: int
    have: int


class InventoryView:
    """
    In-memory inventory with normalization and optional unlimited basics.
    """
    def __init__(
        self,
        counts_by_name: Dict[str, int],
        allow_unlimited_basics: bool = True,
        basics: Optional[Set[str]] = None,
        normalizer: Callable[[str], str] = normalize_name,
    ):
        self._normalize = normalizer
        self._allow_unlimited_basics = bool(allow_unlimited_basics)
        self._basics = set(basics) if basics is not None else set(BASIC_LANDS)

        # store normalized counts
        self._counts: Dict[str, int] = {}
        for k, v in (counts_by_name or {}).items():
            key = self._normalize(k)
            self._counts[key] = self._counts.get(key, 0) + int(v or 0)

    @classmethod
    def from_counts(
        cls,
        counts_by_name: Dict[str, int],
        allow_unlimited_basics: bool = True,
        basics: Optional[Set[str]] = None,
        normalizer: Callable[[str], str] = normalize_name,
    ) -> "InventoryView":
        return cls(
            counts_by_name=counts_by_name or {},
            allow_unlimited_basics=allow_unlimited_basics,
            basics=basics,
            normalizer=normalizer,
        )

    def _key(self, name: str) -> str:
        return self._normalize(name)

    def remaining(self, name: str) -> int:
        key = self._key(name)
        if self._allow_unlimited_basics and key in self._basics:
            # effectively unlimited
            return 10**9
        return max(0, int(self._counts.get(key, 0)))

    def can_take(self, name: str, n: int = 1) -> bool:
        return self.remaining(name) >= int(n)

    def take(self, name: str, n: int = 1) -> None:
        n = int(n)
        if n <= 0:
            return
        key = self._key(name)
        if self._allow_unlimited_basics and key in self._basics:
            # no decrement
            return
        cur = int(self._counts.get(key, 0))
        if cur < n:
            # do not go negative; caller should check can_take first
            raise ValueError(f"Inventory exhausted for '{name}': need {n}, have {cur}")
        self._counts[key] = cur - n

    def as_dict(self) -> Dict[str, int]:
        return dict(self._counts)


def validate_owned_quantities_from_counts(
    deck_counts_by_name: Dict[str, int],
    inventory: InventoryView,
) -> Sequence[QuantityViolation]:
    violations: list[QuantityViolation] = []
    for raw_name, need in (deck_counts_by_name or {}).items():
        need = int(need or 0)
        if need <= 0:
            continue
        rem = inventory.remaining(raw_name)
        if rem < need:
            violations.append(
                QuantityViolation(
                    name=raw_name,
                    need=need,
                    have=rem,
                )
            )
    return violations