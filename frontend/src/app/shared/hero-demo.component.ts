import { Component, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../core/api.service';
import { AgentAnswer } from '../core/models';

// A compact, self-contained live demo embedded in the hero: type a question,
// it calls the real agent and shows the answer with its security verdicts.
// The full console lives at /app; this is the "try it in one line" taste.
@Component({
  selector: 'app-hero-demo',
  standalone: true,
  imports: [FormsModule],
  styleUrl: './hero-demo.component.scss',
  template: `
    <div class="demo">
      <form class="row" (submit)="submit($event)">
        <input
          [(ngModel)]="question"
          name="q"
          [disabled]="loading()"
          placeholder="How many customers are there in total?"
          aria-label="Ask the agent"
        />
        <button type="submit" class="btn btn-primary" [disabled]="loading() || !question.trim()">
          {{ loading() ? 'Scanning…' : 'Ask' }}
        </button>
      </form>

      @if (loading()) {
        <div class="processing" aria-live="polite">
          <span class="pulse"></span><span class="pulse"></span><span class="pulse"></span>
          <span class="txt">Filtering · retrieving · checking policy</span>
        </div>
      }

      @if (answer(); as a) {
        <div class="result">
          <div class="badges">
            @if (a.blocked_input) { <span class="badge badge-red">Injection blocked</span> }
            @else if (a.rejected) { <span class="badge badge-red">Policy refused</span> }
            @else if (a.output_redacted) { <span class="badge badge-amber">PII redacted</span> }
            @else { <span class="badge badge-verified">Verified · no leak</span> }
            @if (a.row_count > 0) { <span class="badge badge-red">{{ a.row_count }} rows cited</span> }
          </div>
          <p class="answer">{{ a.answer }}</p>
        </div>
      }

      @if (error()) { <p class="err">{{ error() }}</p> }
    </div>
  `,
})
export class HeroDemoComponent {
  private readonly api = inject(ApiService);

  question = '';
  readonly answer = signal<AgentAnswer | null>(null);
  readonly loading = signal(false);
  readonly error = signal<string | null>(null);

  submit(event: Event): void {
    event.preventDefault();
    const q = this.question.trim();
    if (!q || this.loading()) return;

    this.loading.set(true);
    this.error.set(null);
    this.answer.set(null);
    this.api.ask(q).subscribe({
      next: (result) => {
        this.answer.set(result);
        this.loading.set(false);
      },
      error: (err) => {
        this.error.set(
          err?.status === 0
            ? 'Backend not reachable — start the API on :8000.'
            : `Request failed (${err?.status ?? 'error'}).`,
        );
        this.loading.set(false);
      },
    });
  }
}
