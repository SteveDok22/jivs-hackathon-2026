"""Deterministic pseudonymization — our headline differentiator.

Everyone at the hackathon will show "found and masked with ***".
We show "found and replaced with realistic fake data, consistently
across every table, joins intact, formats preserved". The data stays
usable for tests and migration — which is DMI's actual business.

How determinism works:
    HMAC-SHA256(secret_key, normalized_name) -> 64-bit seed -> Faker
Same person (any spelling, any table) -> same fake identity. Different
secret key -> completely different mapping, so the mapping itself is
protected by the key (store it in a KMS in production; .env here).

Format preservation: the replacement mirrors the original's shape —
"Jonas, Paul" -> "Weber, Marc", "P. Jonas" -> "M. Weber", upper stays upper.
"""

import hashlib
import hmac
import json
import random
from pathlib import Path

from faker import Faker

from app.pii.normalize import normalize


class Pseudonymizer:
    def __init__(self, secret_key: str, locale: str = "de_CH") -> None:
        self._key = secret_key.encode()
        self._locale = locale
        self._vault: dict[str, dict[str, str]] = {}  # canonical -> fake identity

    def identity_for(self, canonical_name: str) -> dict[str, str]:
        """Deterministic fake identity for one person (cached)."""
        canonical = normalize(canonical_name)
        if canonical in self._vault:
            return self._vault[canonical]

        digest = hmac.new(self._key, canonical.encode(), hashlib.sha256).digest()
        seed = int.from_bytes(digest[:8], "big")
        fake = Faker(self._locale)
        fake.seed_instance(seed)
        rng = random.Random(seed)

        first = fake.first_name()
        last = fake.last_name()
        identity = {
            "first": first,
            "last": last,
            "email": f"{first.lower()}.{last.lower()}{rng.randrange(10, 99)}@example.org",
        }
        self._vault[canonical] = identity
        return identity

    def replace_name(self, original_text: str, canonical_name: str) -> str:
        """Replace a name occurrence, mirroring the original's format."""
        identity = self.identity_for(canonical_name)
        first, last = identity["first"], identity["last"]

        stripped = original_text.strip()
        if "," in stripped:
            replacement = f"{last}, {first}"                    # "Jonas, Paul" form
        elif re_initial(stripped):
            replacement = f"{first[0]}. {last}"                 # "P. Jonas" form
        else:
            replacement = f"{first} {last}"
        if stripped.isupper():
            replacement = replacement.upper()
        return replacement

    def export_vault(self, path: str | Path) -> Path:
        """Persist the mapping (original -> fake) for governed re-identification."""
        target = Path(path)
        target.write_text(json.dumps(self._vault, indent=2, ensure_ascii=False, sort_keys=True))
        return target


def re_initial(text: str) -> bool:
    tokens = text.replace(".", " ").split()
    return any(len(token) == 1 for token in tokens)
