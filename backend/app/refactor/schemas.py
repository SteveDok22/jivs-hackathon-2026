"""Data structures for legacy UI refactoring.

A UISpec is a framework-neutral description of a screen: its fields,
controls and layout. It is the pivot of the whole module — we extract
one from a screenshot, generate code from it, then re-extract one from
the generated code and compare. Comparing specs (not pixels) makes
fidelity measurable and testable offline.
"""

from pydantic import BaseModel, Field


class UIField(BaseModel):
    # A single interactive element on the screen.
    type: str = Field(description="input | select | checkbox | button | table | label | date")
    label: str = Field(description="visible text or field label")
    name: str = Field(description="machine name, snake_case, derived from the label")
    required: bool = False


class UISpec(BaseModel):
    title: str
    fields: list[UIField]
    layout: str = Field(default="form", description="form | table | dashboard | list")


class GeneratedComponent(BaseModel):
    framework: str = "angular"
    filename: str
    code: str
    notes: str = Field(default="", description="assumptions or stubbed service calls")


class FidelityReport(BaseModel):
    score: float                    # 0..1 — fraction of original fields reproduced
    matched: list[str]
    missing: list[str]              # fields in the original absent from the generated code
    extra: list[str]                # fields invented by the generator, not in the original
    iterations: int


class RefactorResult(BaseModel):
    spec: UISpec
    component: GeneratedComponent
    fidelity: FidelityReport
    cost_usd: float = 0.0
