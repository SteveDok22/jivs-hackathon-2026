"""PII endpoints: scan a dataset directory, produce a pseudonymized copy."""

from fastapi import APIRouter
from pydantic import BaseModel

from app.pii.service import DEFAULT_THRESHOLD, pseudonymize_dataset, scan

router = APIRouter(prefix="/pii")


class ScanRequest(BaseModel):
    directory: str
    names: list[str]
    threshold: float = DEFAULT_THRESHOLD


class PseudonymizeRequest(ScanRequest):
    out_dir: str


@router.post("/scan")
def scan_endpoint(request: ScanRequest) -> dict:
    findings = scan(request.directory, request.names, threshold=request.threshold)
    return {"count": len(findings), "findings": [vars(f) for f in findings]}


@router.post("/pseudonymize")
def pseudonymize_endpoint(request: PseudonymizeRequest) -> dict:
    return pseudonymize_dataset(
        request.directory, request.out_dir, request.names, threshold=request.threshold
    )
