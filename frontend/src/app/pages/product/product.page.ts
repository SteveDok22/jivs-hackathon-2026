import { Component, inject } from '@angular/core';
import { RouterLink } from '@angular/router';
import { ApiService } from '../../core/api.service';
import { NetworkBackgroundComponent } from '../../shared/network-background.component';
import { ChatComponent } from '../../features/chat/chat.component';
import { MetricsComponent } from '../../features/metrics/metrics.component';

// The AEGIS console — the working product. Hosts the chat agent and the live
// metrics panel. In demo mode (public site) a banner explains that saved
// examples are shown and links to the repo for the full local experience.
@Component({
  selector: 'app-product',
  standalone: true,
  imports: [RouterLink, NetworkBackgroundComponent, ChatComponent, MetricsComponent],
  styleUrl: './product.page.scss',
  template: `
    <header class="topbar">
      <div class="container bar">
        <a routerLink="/" class="brand">
          <span class="mark">AEGIS</span>
          <span class="sub">Console</span>
        </a>
        <a routerLink="/" class="back">← Back to overview</a>
      </div>
    </header>

    <div class="bg-layer"><app-network-bg /></div>
    <main class="container">
      @if (demoMode) {
        <div class="demo-banner">
          <span class="badge badge-red">Live preview</span>
          <p>
            This hosted console runs a few saved real examples so it stays live
            and free. The full agent — your own questions, live evaluation —
            runs locally.
            <a [href]="repoUrl" target="_blank" rel="noopener">Clone the repo →</a>
          </p>
        </div>
      }
      <div class="stack">
        <app-chat />
        <app-metrics />
      </div>
    </main>
  `,
})
export class ProductPage {
  private readonly api = inject(ApiService);
  readonly demoMode = this.api.demoMode;
  readonly repoUrl = this.api.repoUrl;
}
