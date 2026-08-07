import { AfterViewInit, Directive, ElementRef, OnDestroy, inject, input } from '@angular/core';
import anime from 'animejs';

// Count-up: animates the element's text from 0 to `appCountUp` when it first
// scrolls into view. Supports decimals and a suffix (e.g. "%"). The numbers we
// pass are the real validated figures from the eval harness.
@Directive({
  selector: '[appCountUp]',
  standalone: true,
})
export class CountUpDirective implements AfterViewInit, OnDestroy {
  private readonly el = inject(ElementRef<HTMLElement>);

  readonly appCountUp = input.required<number>();
  readonly decimals = input<number>(0);
  readonly suffix = input<string>('');
  readonly duration = input<number>(1600);

  private observer?: IntersectionObserver;
  private done = false;

  ngAfterViewInit(): void {
    const node = this.el.nativeElement;
    const target = this.appCountUp();
    const decimals = this.decimals();
    const suffix = this.suffix();

    node.textContent = `0${decimals ? '.' + '0'.repeat(decimals) : ''}${suffix}`;

    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
      node.textContent = `${target.toFixed(decimals)}${suffix}`;
      return;
    }

    this.observer = new IntersectionObserver(
      (entries) => {
        if (entries[0]?.isIntersecting && !this.done) {
          this.done = true;
          this.observer?.disconnect();
          const counter = { value: 0 };
          anime({
            targets: counter,
            value: target,
            duration: this.duration(),
            easing: 'easeOutExpo',
            update: () => {
              node.textContent = `${counter.value.toFixed(decimals)}${suffix}`;
            },
          });
        }
      },
      { threshold: 0.4 },
    );
    this.observer.observe(node);
  }

  ngOnDestroy(): void {
    this.observer?.disconnect();
  }
}
