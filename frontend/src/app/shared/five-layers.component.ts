import { AfterViewInit, Component, ElementRef, OnDestroy, inject } from '@angular/core';
import anime from 'animejs';

// The five-layer story, animated. A request dot travels left to right through
// each protection layer; each layer pulses as the dot passes; at the end a
// cited answer appears. This is the ASCII architecture diagram from the README,
// brought to life — the core "how it works" visual.
//
// Anime.js drives a looping timeline. Respects prefers-reduced-motion by
// showing the layers statically (no dot, no loop).

interface Layer {
  id: string;
  label: string;
  hint: string;
  icon: string; // inline SVG path data
}

@Component({
  selector: 'app-five-layers',
  standalone: true,
  styleUrl: './five-layers.component.scss',
  template: `
    <div class="flow" #flow>
      <div class="track">
        <div class="line"></div>
        <div class="dot" #dot></div>
      </div>
      <div class="layers">
        @for (layer of layers; track layer.id) {
          <div class="layer" [attr.data-id]="layer.id">
            <div class="node">
              <svg viewBox="0 0 24 24" width="22" height="22" aria-hidden="true">
                <path [attr.d]="layer.icon" fill="none" stroke="currentColor" stroke-width="1.7"
                      stroke-linecap="round" stroke-linejoin="round" />
              </svg>
            </div>
            <div class="meta">
              <span class="name">{{ layer.label }}</span>
              <span class="hint">{{ layer.hint }}</span>
            </div>
          </div>
        }
      </div>
    </div>
  `,
})
export class FiveLayersComponent implements AfterViewInit, OnDestroy {
  private readonly host = inject<ElementRef<HTMLElement>>(ElementRef);
  private timeline?: anime.AnimeTimelineInstance;

  readonly layers: Layer[] = [
    {
      id: 'input',
      label: 'Input filter',
      hint: 'blocks prompt injection',
      icon: 'M12 3l7 3v5c0 4-3 7-7 8-4-1-7-4-7-8V6z',
    },
    {
      id: 'data',
      label: 'Pseudonymized data',
      hint: 'names replaced, joins intact',
      icon: 'M4 7h16M4 12h16M4 17h10',
    },
    {
      id: 'agent',
      label: 'Policy-bound agent',
      hint: 'SQL checked before it runs',
      icon: 'M9 3v4M15 3v4M5 7h14v12H5zM9 11h6M9 15h4',
    },
    {
      id: 'output',
      label: 'Output scan',
      hint: 'no PII leaves the system',
      icon: 'M2 12s3-7 10-7 10 7 10 7-3 7-10 7S2 12 2 12z M12 9a3 3 0 100 6 3 3 0 000-6z',
    },
    {
      id: 'answer',
      label: 'Cited answer',
      hint: 'every claim sourced',
      icon: 'M20 6L9 17l-5-5',
    },
  ];

  ngAfterViewInit(): void {
    const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    const nodes = this.host.nativeElement.querySelectorAll<HTMLElement>('.layer');

    if (reduced) {
      // Static: reveal all layers, no travelling dot.
      nodes.forEach((n) => n.classList.add('lit'));
      const dot = this.host.nativeElement.querySelector<HTMLElement>('.dot');
      if (dot) dot.style.display = 'none';
      return;
    }

    const dot = this.host.nativeElement.querySelector<HTMLElement>('.dot');
    const count = this.layers.length;

    // One loop: the dot crosses the track while each layer lights up in turn.
    this.timeline = anime.timeline({
      loop: true,
      easing: 'easeInOutQuad',
    });

    this.timeline.add({
      targets: dot,
      left: ['0%', '100%'],
      duration: 4200,
      easing: 'easeInOutSine',
      begin: () => nodes.forEach((n) => n.classList.remove('lit')),
      update: (anim: anime.AnimeInstance) => {
        // Light each layer as the dot reaches its position.
        const progress = anim.progress / 100;
        const activeIndex = Math.min(count - 1, Math.floor(progress * count));
        nodes.forEach((n, i) => n.classList.toggle('lit', i <= activeIndex));
      },
    });

    // Brief hold at the end so the "cited answer" state reads before looping.
    this.timeline.add({ targets: dot, opacity: [1, 0.3], duration: 700 });
    this.timeline.add({ targets: dot, opacity: [0.3, 1], duration: 400 });
  }

  ngOnDestroy(): void {
    this.timeline?.pause();
  }
}
