import { Component } from '@angular/core';
import { ChatComponent } from './features/chat/chat.component';
import { MetricsComponent } from './features/metrics/metrics.component';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [ChatComponent, MetricsComponent],
  styles: [`
    .shell { max-width: 920px; margin: 0 auto; padding: 2rem 1.5rem 4rem; }
    header.brand { margin-bottom: 2rem; }
    .brand h1 {
      margin: 0;
      font-size: 1.5rem;
      letter-spacing: -0.01em;
    }
    .brand .mark { color: var(--gold); }
    .brand p { margin: 0.25rem 0 0; color: var(--text-dim); font-size: 0.9rem; }
    .stack { display: flex; flex-direction: column; gap: 2rem; }
  `],
  template: `
    <div class="shell">
      <header class="brand">
        <h1><span class="mark">Trusted</span> Enterprise Agent</h1>
        <p>Ask your archive in plain language — every answer cited, every access checked.</p>
      </header>
      <div class="stack">
        <app-chat />
        <app-metrics />
      </div>
    </div>
  `,
})
export class AppComponent {}
