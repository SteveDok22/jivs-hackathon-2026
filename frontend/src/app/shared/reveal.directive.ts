import { AfterViewInit, Directive, ElementRef, OnDestroy, inject, input } from '@angular/core';

// Scroll reveal: elements marked with the .reveal class (and this directive)
// fade + rise into view once, when they first intersect the viewport.
// Respects prefers-reduced-motion by revealing immediately.
@Directive({
  selector: '[appReveal]',
  standalone: true,
})
export class RevealDirective implements AfterViewInit, OnDestroy {
  private readonly el = inject(ElementRef<HTMLElement>);

  // Optional stagger delay in ms, for sequencing siblings.
  readonly appReveal = input<number>(0);

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
