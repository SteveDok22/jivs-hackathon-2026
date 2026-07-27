"""Eval endpoints: trigger a run, fetch the latest report.

The report JSON is the data source for the Stage 7 metrics dashboard.
A run is offline and takes ~1s, so /eval/run is safe to call live on stage.
"""

from fastapi import APIRouter

from app.eval.harness import EvalReport, run_evaluation

router = APIRouter(prefix="/eval")

_latest: EvalReport | None = None


@router.post("/run")
def run() -> dict:
    global _latest
    _latest = run_evaluation()
    return _latest.to_dict()


@router.get("/report")
def report() -> dict:
    if _latest is None:
        return {"status": "no run yet — POST /eval/run first"}
    return _latest.to_dict()
