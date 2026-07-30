"""Legacy refactoring with a self-verification loop — our T3 differentiator.

Pipeline:
1. EXTRACT   screenshot -> UISpec (vision call, structured)
2. GENERATE  UISpec -> Angular component (structured)
3. VERIFY    re-extract a UISpec FROM the generated code, compare to the
             original spec -> fidelity score (fraction of fields reproduced)
4. REFINE    if fidelity < threshold, feed the missing fields back and
             regenerate; repeat up to max_iterations

Why this matters: in 2025 every team did one-shot generation with no check.
A closed loop that measures its own output and self-corrects is the move
none of them showed. The fidelity score is a real, testable number — it
goes on the eval panel next to the PII and guardrail metrics.

The comparison is structural (field type + fuzzy label match), so the whole
loop runs offline against FakeProvider in tests; only EXTRACT needs vision.
"""

from pathlib import Path

from rapidfuzz import fuzz

from app.llm.client import LLMClient, Tier
from app.llm.cost import get_meter
from app.pii.normalize import normalize
from app.refactor.schemas import (
    FidelityReport,
    GeneratedComponent,
    RefactorResult,
    UIField,
    UISpec,
)

DEFAULT_THRESHOLD = 0.9
DEFAULT_MAX_ITERATIONS = 3
_LABEL_MATCH = 82  # fuzzy score above which two field labels are "the same"

_EXTRACT_SYSTEM = """You convert legacy enterprise UI screens into a structured spec.
Identify every interactive element: inputs, selects, checkboxes, buttons, tables,
date pickers, and their visible labels. Derive a snake_case machine name for each
from its label. Be exhaustive — missing a field is worse than guessing its type."""

_GENERATE_SYSTEM = """You are a senior Angular engineer modernizing a legacy screen.
Produce ONE standalone Angular component (TypeScript, Angular 20, signals, reactive
forms). Reproduce every field in the spec with an appropriate control. Stub any
backend calls behind a service method with a clear TODO. Clean, typed, no TODOs left
except stubbed service calls."""

_RECOVER_SYSTEM = """You extract a structured UI spec from Angular component code.
List every field the component renders (form controls, buttons, table columns) with
its type, visible label, and machine name. This is used to verify the component
against a target spec, so be precise and exhaustive."""


class RefactorService:
    def __init__(self, llm: LLMClient | None = None) -> None:
        self._llm = llm or LLMClient()

    # ── Step 1: screenshot -> spec ───────────────────────────────────
    def extract_spec(self, image_b64: str) -> UISpec:
        return self._llm.structured(
            "Extract the UI spec from this legacy screen.",
            UISpec,
            tier=Tier.SMART,
            system=_EXTRACT_SYSTEM,
            image_b64=image_b64,
        )

    # ── Step 2: spec -> Angular code ─────────────────────────────────
    def generate(self, spec: UISpec, feedback: str = "") -> GeneratedComponent:
        prompt = f"Target spec:\n{spec.model_dump_json(indent=2)}\n"
        if feedback:
            prompt += f"\nThe previous attempt was incomplete. Fix these gaps:\n{feedback}\n"
        prompt += "\nGenerate the Angular component."
        return self._llm.structured(
            prompt, GeneratedComponent, tier=Tier.SMART, system=_GENERATE_SYSTEM
        )

    # ── Step 3: code -> spec (for verification) ──────────────────────
    def recover_spec(self, component: GeneratedComponent) -> UISpec:
        return self._llm.structured(
            f"Component code:\n{component.code}\n\nExtract the UI spec it implements.",
            UISpec,
            tier=Tier.SMART,
            system=_RECOVER_SYSTEM,
        )

    # ── Full loop ────────────────────────────────────────────────────
    def refactor(
        self,
        image_b64: str,
        *,
        threshold: float = DEFAULT_THRESHOLD,
        max_iterations: int = DEFAULT_MAX_ITERATIONS,
    ) -> RefactorResult:
        cost_before = get_meter().snapshot()["cost_usd"]

        target = self.extract_spec(image_b64)
        feedback = ""
        component = self.generate(target)
        report = self._verify(target, self.recover_spec(component), iterations=1)

        iteration = 1
        while report.score < threshold and iteration < max_iterations:
            iteration += 1
            feedback = "Missing fields: " + ", ".join(report.missing)
            component = self.generate(target, feedback=feedback)
            report = self._verify(target, self.recover_spec(component), iterations=iteration)

        return RefactorResult(
            spec=target,
            component=component,
            fidelity=report,
            cost_usd=round(get_meter().snapshot()["cost_usd"] - cost_before, 6),
        )

    # ── Structural spec comparison -> fidelity score ─────────────────
    def _verify(self, target: UISpec, produced: UISpec, *, iterations: int) -> FidelityReport:
        return compare_specs(target, produced, iterations=iterations)


def compare_specs(target: UISpec, produced: UISpec, *, iterations: int = 1) -> FidelityReport:
    """Fraction of the target's fields reproduced in `produced`.

    A field matches when its type is equal and its label fuzzily matches
    (order-independent). Pure function -> unit-testable without any LLM.
    """
    produced_remaining = list(produced.fields)
    matched: list[str] = []
    missing: list[str] = []

    for target_field in target.fields:
        hit = _find_match(target_field, produced_remaining)
        if hit is not None:
            matched.append(target_field.name)
            produced_remaining.remove(hit)
        else:
            missing.append(target_field.name)

    extra = [field.name for field in produced_remaining]
    score = len(matched) / len(target.fields) if target.fields else 1.0
    return FidelityReport(
        score=round(score, 4),
        matched=matched,
        missing=missing,
        extra=extra,
        iterations=iterations,
    )


def _find_match(target: UIField, candidates: list[UIField]) -> UIField | None:
    target_label = normalize(target.label)
    for candidate in candidates:
        if candidate.type != target.type:
            continue
        if fuzz.token_set_ratio(target_label, normalize(candidate.label)) >= _LABEL_MATCH:
            return candidate
    return None


def load_image_b64(path: str | Path) -> str:
    """Read an image file and return base64 — convenience for the CLI/demo."""
    import base64

    return base64.b64encode(Path(path).read_bytes()).decode()
