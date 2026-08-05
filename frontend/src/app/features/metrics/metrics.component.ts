import { Component, inject, signal } from '@angular/core';
import { ApiService } from '../../core/api.service';
import { EvalReport } from '../../core/models';

// Live metrics panel. Runs the backend eval harness and shows the numbers
// that map to the jury sheet: detection accuracy, guardrail catch rate,
// zero-leak safety, cost. This is the "numbers, not just a demo" surface.
@Component({
  selector: 'app-metrics',
  standalone: true,
  styleUrl: './metrics.component.scss',
  template: `
    <section class="metrics">
      <header>
        <h2>Evaluation</h2>
        <button (click)="run()" [disabled]="loading()">
          {{ loading() ? 'Running…' : 'Run evaluation' }}
        </button>
      </header>

      @if (report(); as r) {
        <div class="grid fade-in">
          <div class="metric">
            <span class="label">PII detection F1</span>
            <span class="value verified">{{ pct(r.pii.name_detection.f1) }}</span>
            <span class="sub">
              P {{ pct(r.pii.name_detection.precision) }} ·
              R {{ pct(r.pii.name_detection.recall) }}
            </span>
          </div>

          <div class="metric">
            <span class="label">Names discovered (NER)</span>
            <span class="value verified">{{ r.pii.persons_discovered }}</span>
            <span class="sub">
              {{ r.pii.presidio_available ? 'Presidio active' : 'regex fallback' }} ·
              vs {{ r.pii.persons_expected }} on watch-list
            </span>
          </div>

          <div class="metric">
            <span class="label">Injection catch rate</span>
            <span class="value verified">{{ pct(r.guardrails.catch_rate) }}</span>
            <span class="sub">
              {{ r.guardrails.attacks_caught }}/{{ r.guardrails.attacks_total }} attacks ·
              {{ r.guardrails.benign_blocked }}/{{ r.guardrails.benign_total }} false pos
            </span>
          </div>

          <div class="metric">
            <span class="label">Data safety</span>
            <span class="value" [class.verified]="r.safety.zero_leak"
                                [class.blocked]="!r.safety.zero_leak">
              {{ r.safety.zero_leak ? 'Zero leak' : 'Leak found' }}
            </span>
            <span class="sub">{{ r.safety.replaced_cells }} cells pseudonymized</span>
          </div>

          <div class="metric">
            <span class="label">Cost / 1000 records</span>
            <span class="value">\${{ r.cost.usd_per_1000_records.toFixed(2) }}</span>
            <span class="sub">{{ r.cost.records_processed }} records · PII path is LLM-free</span>
          </div>

          <div class="metric">
            <span class="label">Refactor verifier</span>
            <span class="value" [class.verified]="r.refactor.verifier_correct"
                                [class.blocked]="!r.refactor.verifier_correct">
              {{ r.refactor.verifier_correct ? 'Correct' : 'Failing' }}
            </span>
            <span class="sub">
              fidelity self-check · perfect {{ pct(r.refactor.perfect_score) }}
            </span>
          </div>
        </div>
        <p class="footnote">Run completed in {{ r.duration_seconds }}s</p>
      } @else if (!loading()) {
        <p class="empty">Run the evaluation to see live metrics.</p>
      }
    </section>
  `,
})
export class MetricsComponent {
  private readonly api = inject(ApiService);

  readonly report = signal<EvalReport | null>(null);
  readonly loading = signal(false);

  run(): void {
    this.loading.set(true);
    this.api.runEval().subscribe({
      next: (r) => {
        this.report.set(r);
        this.loading.set(false);
      },
      error: () => this.loading.set(false),
    });
  }

  pct(value: number): string {
    return `${(value * 100).toFixed(1)}%`;
  }
}
