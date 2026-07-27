"""CLI: python -m app.eval  ->  pretty-print the evaluation report."""

import json

from app.eval.harness import run_evaluation

if __name__ == "__main__":
    report = run_evaluation()
    print(json.dumps(report.to_dict(), indent=2, ensure_ascii=False))
