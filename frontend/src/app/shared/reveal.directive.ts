import { AfterViewInit, Directive, ElementRef, OnDestroy, inject, input } from '@angular/core';

// Scroll reveal: elements marked with the .reveal class (and this directive)
// fade + rise into view once, when they first intersect the viewport.
// Respects prefers-reduced-motion by revealing immediately.
@Directive({
  selector: '[appReveal]',
  standalone: true,
})
export class RevealDirective implements AfterViewInit, OnDestroy {
  private readonly el = inject<ElementRef<HTMLElement>>(ElementRef);

  // Optional stagger delay in ms. Accepts both the bare form `appReveal`
  // (which passes an empty string -> 0) and `[appReveal]="80"`. The transform
  // coerces either to a number so the strict template compiler is satisfied.
  readonly appReveal = input(0, {
    transform: (value: number | string): number => {
      const n = typeof value === 'string' ? parseInt(value, 10) : value;
      return Number.isFinite(n) ? n : 0;
    },
  });

  private observer?: IntersectionObserver;

  ngAfterViewInit(): void {
    const node = this.el.nativeElement;
    node.classList.add('reveal');

    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
      node.classList.add('is-visible');
      return;
    }

    this.observer = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          if (entry.isIntersecting) {
            const delay = this.appReveal();
            if (delay) node.style.transitionDelay = `${delay}ms`;
            node.classList.add('is-visible');
            this.observer?.unobserve(node); // reveal once, then stop watching
          }
        }
      },
      { threshold: 0.15 },
    );
    this.observer.observe(node);
  }

  ngOnDestroy(): void {
    this.observer?.disconnect();
  }
}
