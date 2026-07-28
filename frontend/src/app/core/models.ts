// Types mirroring the FastAPI backend response shapes (app/agent, app/eval).
// Keep in sync with the Pydantic models — these are the integration contract.

export interface Citation {
  table: string;
  rows: Record<string, unknown>[];
}

export interface AgentAnswer {
  answer: string;
  sql: string;
  citations: Citation[];
  row_count: number;
  rejected: boolean;
  violations: string[];
  blocked_input: boolean;
  output_redacted: boolean;
  cost_usd: number;
}

export interface PRF {
  precision: number;
  recall: number;
  f1: number;
  true_positives: number;
  false_positives: number;
  false_negatives: number;
}

export interface EvalReport {
  pii: {
    name_detection: PRF;
    persons_found: number;
    persons_expected: number;
  };
  guardrails: {
    catch_rate: number;
    false_positive_rate: number;
    attacks_caught: number;
    attacks_total: number;
    benign_blocked: number;
    benign_total: number;
  };
  safety: {
    zero_leak: boolean;
    leaked_tokens: string[];
    replaced_cells: number;
  };
  cost: {
    records_processed: number;
    usd_per_1000_records: number;
  };
  duration_seconds: number;
  generated_at: number;
}
