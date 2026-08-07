import { Component } from '@angular/core';

// Grid Scan: a faint grid overlay with a red scan line sweeping across it,
// echoing the "scanning data" motif. CSS-only (transform + gradient), so it is
// cheap and pauses cleanly under prefers-reduced-motion. Sits behind content.
@Component({
  selector: 'app-grid-scan',
  standalone: true,
  template: `<div class="grid" aria-hidden="true"></div><div class="scan" aria-hidden="true"></div>`,
  styles: [`
    :host {
      position: absolute;
      inset: 0;
      overflow: hidden;
      pointer-events: none;
      z-index: 0;
    }
    .grid {
      position: absolute;
      inset: 0;
      background-image:
        linear-gradient(to right, rgba(229, 50, 45, 0.06) 1px, transparent 1px),
        linear-gradient(to bottom, rgba(229, 50, 45, 0.06) 1px, transparent 1px);
      background-size: 48px 48px;
      mask-image: radial-gradient(ellipse at center, black 40%, transparent 80%);
    }
    .scan {
      position: absolute;
      left: 0;
      right: 0;
      height: 180px;
      background: linear-gradient(to bottom,
        transparent,
        rgba(229, 50, 45, 0.10) 45%,
        rgba(255, 77, 77, 0.18) 50%,
        rgba(229, 50, 45, 0.10) 55%,
        transparent);
      animation: sweep 7s linear infinite;
    }
    @keyframes sweep {
      0%   { top: -180px; }
      100% { top: 100%; }
    }
    @media (prefers-reduced-motion: reduce) {
      .scan { display: none; }
    }
  `],
})
export class GridScanComponent {}
