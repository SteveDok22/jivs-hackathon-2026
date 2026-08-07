import { Component } from '@angular/core';
import { RouterLink } from '@angular/router';
import { NetworkBackgroundComponent } from '../../shared/network-background.component';
import { ChatComponent } from '../../features/chat/chat.component';
import { MetricsComponent } from '../../features/metrics/metrics.component';

// The AEGIS console — the working product. Hosts the chat agent and the live
// metrics panel. Stage 18 adds the network background here.
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
      <div class="stack">
        <app-chat />
        <app-metrics />
      </div>
    </main>
  `,
})
export class ProductPage {}
