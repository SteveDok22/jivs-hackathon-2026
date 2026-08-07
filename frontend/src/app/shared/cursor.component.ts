import { AfterViewInit, Component, ElementRef, OnDestroy, inject } from '@angular/core';

// Custom cursor: a small ring that trails the real pointer with a soft lag and
// grows / brightens over interactive elements. Restrained and enterprise —
// not a toy. Hidden entirely on touch devices and under reduced-motion, where
// the native cursor is left alone.
@Component({
  selector: 'app-cursor',
  standalone: true,
  template: `
    <div class="ring" #ring aria-hidden="true"></div>
    <div class="dot" #dot aria-hidden="true"></div>
  `,
  styles: [`
    :host { position: fixed; inset: 0; pointer-events: none; z-index: 9999; }
    .ring, .dot {
      position: fixed;
      top: 0; left: 0;
      border-radius: 50%;
      transform: translate(-50%, -50%);
      will-change: transform;
    }
    .ring {
      width: 32px; height: 32px;
      border: 1.5px solid rgba(229, 50, 45, 0.7);
      transition: width var(--dur) var(--ease), height var(--dur) var(--ease),
        border-color var(--dur) var(--ease), background var(--dur) var(--ease);
    }
    .dot {
      width: 5px; height: 5px;
      background: var(--red-glow);
    }
    :host(.hovering) .ring {
      width: 52px; height: 52px;
      border-color: var(--white);
      background: rgba(255, 255, 255, 0.06);
      box-shadow: var(--glow-white);
    }
    :host(.pressed) .ring { width: 26px; height: 26px; }
  `],
})
export class CursorComponent implements AfterViewInit, OnDestroy {
  private readonly host = inject(ElementRef<HTMLElement>);

  private ring!: HTMLElement;
  private dot!: HTMLElement;

  // Target (real pointer) and current (eased) positions.
  private tx = 0;
  private ty = 0;
  private rx = 0;
  private ry = 0;
  private frame = 0;
  private enabled = false;

  private onMove = (e: PointerEvent) => {
    this.tx = e.clientX;
    this.ty = e.clientY;
    // The dot tracks 1:1 (no lag); the ring eases in the loop.
    this.dot.style.transform = `translate(${this.tx}px, ${this.ty}px) translate(-50%, -50%)`;
  };
  private onOver = (e: Event) => {
    const target = e.target as HTMLElement;
    if (target.closest('a, button, input, [role="button"]')) {
      this.host.nativeElement.classList.add('hovering');
    }
  };
  private onOut = (e: Event) => {
    const target = e.target as HTMLElement;
    if (target.closest('a, button, input, [role="button"]')) {
      this.host.nativeElement.classList.remove('hovering');
    }
  };
  private onDown = () => this.host.nativeElement.classList.add('pressed');
  private onUp = () => this.host.nativeElement.classList.remove('pressed');

  ngAfterViewInit(): void {
    // Only enable on devices with a fine pointer and no reduced-motion pref.
    const finePointer = window.matchMedia('(pointer: fine)').matches;
    const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (!finePointer || reduced) {
      this.host.nativeElement.style.display = 'none';
      return;
    }

    this.enabled = true;
    this.ring = this.host.nativeElement.querySelector('.ring')!;
    this.dot = this.host.nativeElement.querySelector('.dot')!;
    document.body.style.cursor = 'none'; // hide native cursor site-wide

    window.addEventListener('pointermove', this.onMove, { passive: true });
    window.addEventListener('pointerover', this.onOver, { passive: true });
    window.addEventListener('pointerout', this.onOut, { passive: true });
    window.addEventListener('pointerdown', this.onDown, { passive: true });
    window.addEventListener('pointerup', this.onUp, { passive: true });

    this.loop();
  }

  private loop = (): void => {
    if (!this.enabled) return;
    // Ease the ring toward the pointer for a soft magnetic trail.
    this.rx += (this.tx - this.rx) * 0.18;
    this.ry += (this.ty - this.ry) * 0.18;
    this.ring.style.transform = `translate(${this.rx}px, ${this.ry}px) translate(-50%, -50%)`;
    this.frame = requestAnimationFrame(this.loop);
  };

  ngOnDestroy(): void {
    this.enabled = false;
    cancelAnimationFrame(this.frame);
    document.body.style.cursor = '';
    window.removeEventListener('pointermove', this.onMove);
    window.removeEventListener('pointerover', this.onOver);
    window.removeEventListener('pointerout', this.onOut);
    window.removeEventListener('pointerdown', this.onDown);
    window.removeEventListener('pointerup', this.onUp);
  }
}
