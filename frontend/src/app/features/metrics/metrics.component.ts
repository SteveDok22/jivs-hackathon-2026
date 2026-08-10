import { Component, ElementRef, effect, inject, signal } from '@angular/core';
import anime from 'animejs';
import { ApiService } from '../../core/api.service';
import { EvalReport } from '../../core/models';

// Live metrics panel. Runs the backend eval harness and reveals the results
// with a scan-in loading state, then a staggered shutter-reveal of each card
// with its number counting up — an effect worthy of the numbers behind it.
@Component({
  selector: 'app-metrics',
  standalone: true,
  styleUrl: './metrics.component.scss',
  template: `
    <section class="metrics" #root>
      <header>
        <h2>Evaluation</h2>
        <button class="run-btn" (click)="run()" [disabled]="loading()">
          {{ loading() ? 'Scanning…' : 'Run evaluation' }}
        </button>
      </header>

      @if (loading()) {
        <div class="scanning" aria-live="polite">
          <div class="scanbar"></div>
          <div class="steps">
            <span>Detecting PII</span><span>Running guardrails</span>
            <span>Pseudonymizing</span><span>Scoring fidelity</span>
          </div>
        </div>
      }

      @if (report(); as r) {
        <div class="grid" #grid>
          <div class="metric card"><span class="shutter"></span>
            <span class="label">PII detection F1</span>
            <span class="value verified" data-count="{{ r.pii.name_detection.f1 }}"
                  data-decimals="2">0.00</span>
            <span class="sub">P {{ pct(r.pii.name_detection.precision) }} ·
              R {{ pct(r.pii.name_detection.recall) }}</span>
          </div>

          <div class="metric card"><span class="shutter"></span>
            <span class="label">Names discovered (NER)</span>
            <span class="value verified" data-count="{{ r.pii.persons_discovered }}">0</span>
            <span class="sub">{{ r.pii.presidio_available ? 'Presidio active' : 'regex fallback' }}
              · vs {{ r.pii.persons_expected }} on watch-list</span>
          </div>

          <div class="metric card"><span class="shutter"></span>
            <span class="label">Injection catch rate</span>
            <span class="value verified" data-count="{{ r.guardrails.catch_rate * 100 }}"
                  data-suffix="%" data-decimals="1">0%</span>
            <span class="sub">{{ r.guardrails.attacks_caught }}/{{ r.guardrails.attacks_total }}
              attacks · {{ r.guardrails.benign_blocked }}/{{ r.guardrails.benign_total }} false pos</span>
          </div>

          <div class="metric card"><span class="shutter"></span>
            <span class="label">Data safety</span>
            <span class="value" [class.verified]="r.safety.zero_leak"
                                [class.blocked]="!r.safety.zero_leak">
              {{ r.safety.zero_leak ? 'Zero leak' : 'Leak found' }}
            </span>
            <span class="sub">{{ r.safety.replaced_cells }} cells pseudonymized</span>
          </div>

          <div class="metric card"><span class="shutter"></span>
            <span class="label">Cost / 1000 records</span>
            <span class="value">\${{ r.cost.usd_per_1000_records.toFixed(2) }}</span>
            <span class="sub">{{ r.cost.records_processed }} records · PII path is LLM-free</span>
          </div>

          <div class="metric card"><span class="shutter"></span>
            <span class="label">Refactor verifier</span>
            <span class="value" [class.verified]="r.refactor.verifier_correct"
                                [class.blocked]="!r.refactor.verifier_correct">
              {{ r.refactor.verifier_correct ? 'Correct' : 'Failing' }}
            </span>
            <span class="sub">fidelity self-check · perfect {{ pct(r.refactor.perfect_score) }}</span>
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
  private readonly host = inject(ElementRef<HTMLElement>);

  readonly report = signal<EvalReport | null>(null);
  readonly loading = signal(false);

  constructor() {
    // When a report arrives, animate the grid on the next frame.
    effect(() => {
      if (this.report()) {
        queueMicrotask(() => requestAnimationFrame(() => this.animateGrid()));
      }
    });
  }

  run(): void {
    this.loading.set(true);
    this.report.set(null);
    this.api.runEval().subscribe({
      next: (r) => {
        this.loading.set(false);
        this.report.set(r);
      },
      error: () => this.loading.set(false),
    });
  }

  private animateGrid(): void {
    const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    const cards = this.host.nativeElement.querySelectorAll<HTMLElement>('.metric');
    const shutters = this.host.nativeElement.querySelectorAll<HTMLElement>('.shutter');
    const values = this.host.nativeElement.querySelectorAll<HTMLElement>('.value[data-count]');

    if (reduced) {
      cards.forEach((c) => (c.style.opacity = '1'));
      values.forEach((v) => this.setFinal(v));
      return;
    }

    anime({
      targets: cards,
      opacity: [0, 1],
      translateY: [24, 0],
      delay: anime.stagger(90),
      duration: 620,
      easing: 'easeOutExpo',
    });

    anime({
      targets: shutters,
      scaleX: [0, 1],
      delay: anime.stagger(90),
      duration: 320,
      easing: 'easeInOutQuad',
      complete: () => {
        anime({
          targets: shutters,
          scaleX: [1, 0],
          transformOrigin: '100% 0',
          delay: anime.stagger(90),
          duration: 320,
          easing: 'easeInOutQuad',
        });
      },
    });

    values.forEach((el, i) => {
      const target = parseFloat(el.dataset['count'] ?? '0');
      const decimals = parseInt(el.dataset['decimals'] ?? '0', 10);
      const suffix = el.dataset['suffix'] ?? '';
      const counter = { v: 0 };
      anime({
        targets: counter,
        v: target,
        duration: 1400,
        delay: 200 + i * 90,
        easing: 'easeOutExpo',
        update: () => (el.textContent = `${counter.v.toFixed(decimals)}${suffix}`),
      });
    });
  }

  private setFinal(el: HTMLElement): void {
    const target = parseFloat(el.dataset['count'] ?? '0');
    const decimals = parseInt(el.dataset['decimals'] ?? '0', 10);
    const suffix = el.dataset['suffix'] ?? '';
    el.textContent = `${target.toFixed(decimals)}${suffix}`;
  }

  pct(value: number): string {
    return `${(value * 100).toFixed(1)}%`;
  }
}
