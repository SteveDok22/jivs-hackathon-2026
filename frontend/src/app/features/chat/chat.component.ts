import { Component, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../core/api.service';
import { AgentAnswer } from '../../core/models';

// The agent console: ask a question in plain language, see the answer plus
// its provenance (SQL, cited rows) and the security verdicts (input blocked,
// output redacted). Provenance and guardrail state are the signature of this
// UI — an answer you can trust because you can see where it came from.
@Component({
  selector: 'app-chat',
  standalone: true,
  imports: [FormsModule],
  styleUrl: './chat.component.scss',
  template: `
    <section class="chat">
      <form class="ask" (submit)="submit($event)">
        <input
          [(ngModel)]="question"
          name="question"
          placeholder="Ask about the archive — e.g. how much did we pay vendors in 2019?"
          [disabled]="loading()"
          aria-label="Question"
        />
        <button type="submit" [disabled]="loading() || !question.trim()">
          {{ loading() ? 'Thinking…' : 'Ask' }}
        </button>
      </form>

      @if (error()) {
        <p class="error">{{ error() }}</p>
      }

      @if (answer(); as a) {
        <article class="answer fade-in">
          <!-- Security verdicts first: the trust layer is the point. -->
          <div class="badges">
            @if (a.blocked_input) {
              <span class="badge blocked">Input blocked — prompt injection</span>
            }
            @if (a.rejected && !a.blocked_input) {
              <span class="badge blocked">Rejected by data policy</span>
            }
            @if (a.output_redacted) {
              <span class="badge redacted">Output PII redacted</span>
            }
            @if (!a.rejected && !a.output_redacted) {
              <span class="badge verified">Verified · no leak</span>
            }
            <span class="badge cost">\${{ a.cost_usd.toFixed(4) }}</span>
          </div>

          <p class="text">{{ a.answer }}</p>

          @if (a.violations.length) {
            <ul class="violations">
              @for (v of a.violations; track v) { <li>{{ v }}</li> }
            </ul>
          }

          @if (a.sql) {
            <details open>
              <summary>SQL executed</summary>
              <pre>{{ a.sql }}</pre>
            </details>
          }

          @if (a.citations.length) {
            <details open>
              <summary>Sources · {{ a.row_count }} rows</summary>
              @for (c of a.citations; track c.table) {
                <div class="citation">
                  <h4>{{ c.table }}</h4>
                  @if (c.rows.length) {
                    <table>
                      <thead>
                        <tr>
                          @for (col of columns(c); track col) { <th>{{ col }}</th> }
                        </tr>
                      </thead>
                      <tbody>
                        @for (row of c.rows; track $index) {
                          <tr>
                            @for (col of columns(c); track col) { <td>{{ row[col] }}</td> }
                          </tr>
                        }
                      </tbody>
                    </table>
                  }
                </div>
              }
            </details>
          }
        </article>
      }
    </section>
  `,
})
export class ChatComponent {
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
    this.api.ask(q).subscribe({
      next: (result) => {
        this.answer.set(result);
        this.loading.set(false);
      },
      error: (err) => {
        this.error.set(`Request failed: ${err.message ?? 'unknown error'}`);
        this.loading.set(false);
      },
    });
  }

  columns(citation: { rows: Record<string, unknown>[] }): string[] {
    return citation.rows.length ? Object.keys(citation.rows[0]) : [];
  }
}
