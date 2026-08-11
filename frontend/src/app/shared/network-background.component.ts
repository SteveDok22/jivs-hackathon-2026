import {
  AfterViewInit,
  Component,
  ElementRef,
  OnDestroy,
  ViewChild,
  inject,
} from '@angular/core';

// AEGIS signature background: a red "plexus" data-network. Nodes drift, links
// draw between nearby nodes and fade with distance, the cursor repels nearby
// nodes, and a periodic scan pulse sweeps across brightening the nodes it
// passes — tying the motion to the product's meaning (scanning data).
//
// Engineering choice: canvas 2D, not WebGL/Three.js. The effect is inherently
// 2D; canvas is lighter, works without a WebGL context (so it never fails on
// low-end GPUs), and looks identical. It honours the "balance, don't overload"
// requirement from DESIGN.md.
//
// Performance guards: node count scales with screen area and is capped; the
// loop pauses when the tab is hidden or the canvas scrolls out of view
// (IntersectionObserver); prefers-reduced-motion renders a single static frame.

interface Node {
  x: number;
  y: number;
  vx: number;
  vy: number;
  radius: number;
  white: boolean; // a few white nodes for contrast, per the reference
  glow: number;   // 0..1, lifted by the scan pulse, decays back down
}

@Component({
  selector: 'app-network-bg',
  standalone: true,
  template: `<canvas #canvas aria-hidden="true"></canvas>`,
  styles: [`
    :host {
      position: absolute;
      inset: 0;
      overflow: hidden;
      pointer-events: none; /* never blocks clicks on content above */
      z-index: 0;
    }
    canvas { display: block; width: 100%; height: 100%; }
  `],
})
export class NetworkBackgroundComponent implements AfterViewInit, OnDestroy {
  @ViewChild('canvas', { static: true })
  private canvasRef!: ElementRef<HTMLCanvasElement>;

  private readonly host = inject<ElementRef<HTMLElement>>(ElementRef);

  private ctx!: CanvasRenderingContext2D;
  private nodes: Node[] = [];
  private width = 0;
  private height = 0;
  private dpr = 1;

  private frameId = 0;
  private running = false;
  private lastTime = 0;
  private onScreen = true;

  // Cursor position in CSS pixels; -1 means "off canvas".
  private pointerX = -1;
  private pointerY = -1;

  // Scan pulse: a vertical wavefront sweeping left->right on a period.
  private scanX = 0;
  private scanPeriodMs = 6000;
  private scanElapsed = 0;

  // Tunables
  private readonly linkDistance = 130; // px within which nodes connect
  private readonly repelRadius = 120;  // px cursor influence
  private reducedMotion = false;

  private observer?: IntersectionObserver;
  private onResize = () => this.resize();
  private onVisibility = () => this.syncRunning();
  private onPointerMove = (e: PointerEvent) => {
    const rect = this.canvasRef.nativeElement.getBoundingClientRect();
    this.pointerX = e.clientX - rect.left;
    this.pointerY = e.clientY - rect.top;
  };
  private onPointerLeave = () => {
    this.pointerX = -1;
    this.pointerY = -1;
  };

  ngAfterViewInit(): void {
    this.reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    const context = this.canvasRef.nativeElement.getContext('2d');
    if (!context) return;
    this.ctx = context;

    this.resize();

    window.addEventListener('resize', this.onResize, { passive: true });
    document.addEventListener('visibilitychange', this.onVisibility);
    window.addEventListener('pointermove', this.onPointerMove, { passive: true });
    window.addEventListener('pointerleave', this.onPointerLeave, { passive: true });

    // Pause the loop when the canvas is scrolled out of view.
    this.observer = new IntersectionObserver(
      (entries) => {
        this.onScreen = entries[0]?.isIntersecting ?? true;
        this.syncRunning();
      },
      { threshold: 0 },
    );
    this.observer.observe(this.host.nativeElement);

    if (this.reducedMotion) {
      this.drawStaticFrame();
    } else {
      this.syncRunning();
    }
  }

  ngOnDestroy(): void {
    this.stop();
    window.removeEventListener('resize', this.onResize);
    document.removeEventListener('visibilitychange', this.onVisibility);
    window.removeEventListener('pointermove', this.onPointerMove);
    window.removeEventListener('pointerleave', this.onPointerLeave);
    this.observer?.disconnect();
  }

  // ── Sizing & node seeding ──────────────────────────────────────────
  private resize(): void {
    const rect = this.host.nativeElement.getBoundingClientRect();
    this.dpr = Math.min(window.devicePixelRatio || 1, 2); // cap DPR for perf
    this.width = rect.width;
    this.height = rect.height;

    const canvas = this.canvasRef.nativeElement;
    canvas.width = Math.floor(this.width * this.dpr);
    canvas.height = Math.floor(this.height * this.dpr);
    this.ctx.setTransform(this.dpr, 0, 0, this.dpr, 0, 0);

    this.seedNodes();
    if (this.reducedMotion) this.drawStaticFrame();
  }

  private seedNodes(): void {
    // Node count scales with area but is capped for performance, and reduced
    // further on small screens.
    const area = this.width * this.height;
    const base = Math.round(area / 12000);
    const count = Math.max(24, Math.min(base, this.width < 700 ? 45 : 90));

    this.nodes = Array.from({ length: count }, () => ({
      x: Math.random() * this.width,
      y: Math.random() * this.height,
      vx: (Math.random() - 0.5) * 0.25,
      vy: (Math.random() - 0.5) * 0.25,
      radius: Math.random() * 1.6 + 1,
      white: Math.random() < 0.12, // ~12% white nodes for contrast
      glow: 0,
    }));
  }

  // ── Run control ────────────────────────────────────────────────────
  private syncRunning(): void {
    const shouldRun = this.onScreen && !document.hidden && !this.reducedMotion;
    if (shouldRun) this.start();
    else this.stop();
  }

  private start(): void {
    if (this.running) return;
    this.running = true;
    this.lastTime = performance.now();
    this.frameId = requestAnimationFrame(this.tick);
  }

  private stop(): void {
    this.running = false;
    cancelAnimationFrame(this.frameId);
  }

  // ── Frame loop ─────────────────────────────────────────────────────
  private tick = (now: number): void => {
    if (!this.running) return;
    const dt = Math.min(now - this.lastTime, 50); // clamp to avoid jumps
    this.lastTime = now;

    this.update(dt);
    this.draw();

    this.frameId = requestAnimationFrame(this.tick);
  };

  private update(dt: number): void {
    const step = dt / 16.67; // normalise to ~60fps units

    // Advance the scan pulse.
    this.scanElapsed = (this.scanElapsed + dt) % this.scanPeriodMs;
    this.scanX = (this.scanElapsed / this.scanPeriodMs) * (this.width + 200) - 100;

    for (const node of this.nodes) {
      node.x += node.vx * step;
      node.y += node.vy * step;

      // Wrap around edges for a continuous field.
      if (node.x < 0) node.x += this.width;
      if (node.x > this.width) node.x -= this.width;
      if (node.y < 0) node.y += this.height;
      if (node.y > this.height) node.y -= this.height;

      // Cursor repulsion.
      if (this.pointerX >= 0) {
        const dx = node.x - this.pointerX;
        const dy = node.y - this.pointerY;
        const dist = Math.hypot(dx, dy);
        if (dist < this.repelRadius && dist > 0.01) {
          const force = (1 - dist / this.repelRadius) * 0.6;
          node.x += (dx / dist) * force * step;
          node.y += (dy / dist) * force * step;
        }
      }

      // Scan pulse brightens nodes near the wavefront, then decays.
      const scanDist = Math.abs(node.x - this.scanX);
      if (scanDist < 40) node.glow = Math.max(node.glow, 1 - scanDist / 40);
      node.glow *= 0.94;
    }
  }

  // ── Drawing ────────────────────────────────────────────────────────
  private draw(): void {
    const ctx = this.ctx;
    ctx.clearRect(0, 0, this.width, this.height);

    // Links first, so nodes sit on top.
    for (let i = 0; i < this.nodes.length; i++) {
      const a = this.nodes[i];
      for (let j = i + 1; j < this.nodes.length; j++) {
        const b = this.nodes[j];
        const dx = a.x - b.x;
        const dy = a.y - b.y;
        const dist = Math.hypot(dx, dy);
        if (dist > this.linkDistance) continue;

        const strength = 1 - dist / this.linkDistance;
        const glow = Math.max(a.glow, b.glow);
        // Base link is red; the scan pulse tints links toward white as it passes.
        const alpha = strength * 0.5 + glow * 0.4;
        ctx.strokeStyle = glow > 0.15
          ? `rgba(255, ${Math.round(120 + glow * 135)}, ${Math.round(120 + glow * 135)}, ${alpha})`
          : `rgba(229, 50, 45, ${alpha})`;
        ctx.lineWidth = 0.6 + strength * 0.5;
        ctx.beginPath();
        ctx.moveTo(a.x, a.y);
        ctx.lineTo(b.x, b.y);
        ctx.stroke();
      }
    }

    // Nodes.
    for (const node of this.nodes) {
      const r = node.radius + node.glow * 1.5;
      if (node.white || node.glow > 0.4) {
        ctx.fillStyle = `rgba(255, 255, 255, ${0.7 + node.glow * 0.3})`;
        ctx.shadowColor = 'rgba(255, 255, 255, 0.6)';
      } else {
        ctx.fillStyle = `rgba(229, 50, 45, ${0.75 + node.glow * 0.25})`;
        ctx.shadowColor = 'rgba(255, 77, 77, 0.7)';
      }
      ctx.shadowBlur = 6 + node.glow * 10;
      ctx.beginPath();
      ctx.arc(node.x, node.y, r, 0, Math.PI * 2);
      ctx.fill();
    }
    ctx.shadowBlur = 0;
  }

  // Static single frame for reduced-motion users.
  private drawStaticFrame(): void {
    if (!this.ctx) return;
    this.update(0);
    this.draw();
  }
}
