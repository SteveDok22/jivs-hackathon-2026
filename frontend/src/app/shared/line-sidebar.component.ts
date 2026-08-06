import { Component, ElementRef, OnDestroy, OnInit, inject, signal } from '@angular/core';

interface NavSection {
  id: string;
  label: string;
}

// Line Sidebar: a fixed vertical rail (enterprise, solid — not playful).
// A white indicator line slides to the section currently in view, tracked
// with IntersectionObserver. Clicking a label smooth-scrolls to its section.
// Recreated natively in Angular from the ReactBits "Line Sidebar" idea.
@Component({
  selector: 'app-line-sidebar',
  standalone: true,
  styleUrl: './line-sidebar.component.scss',
  template: `
    <nav class="rail" aria-label="Section navigation">
      <ul>
        @for (section of sections; track section.id) {
          <li>
            <button
              [class.active]="active() === section.id"
              (click)="jump(section.id)"
              [attr.aria-current]="active() === section.id ? 'true' : null"
            >
              <span class="tick"></span>
              <span class="label">{{ section.label }}</span>
            </button>
          </li>
        }
      </ul>
    </nav>
  `,
})
export class LineSidebarComponent implements OnInit, OnDestroy {
  private readonly host = inject(ElementRef<HTMLElement>);

  // Sections of the homepage, in order. Kept here so the rail is the single
  // place that defines the page's narrative spine.
  readonly sections: NavSection[] = [
    { id: 'hero', label: 'AEGIS' },
    { id: 'problem', label: 'Problem' },
    { id: 'how', label: 'How it works' },
    { id: 'metrics', label: 'Results' },
    { id: 'tech', label: 'Tech' },
    { id: 'cta', label: 'Try it' },
  ];

  readonly active = signal<string>('hero');
  private observer?: IntersectionObserver;

  ngOnInit(): void {
    // Observe every section; the one most in view becomes active.
    this.observer = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          if (entry.isIntersecting) {
            this.active.set(entry.target.id);
          }
        }
      },
      { rootMargin: '-45% 0px -45% 0px', threshold: 0 },
    );

    // Defer until the page's sections exist in the DOM.
    queueMicrotask(() => {
      for (const section of this.sections) {
        const el = document.getElementById(section.id);
        if (el) this.observer!.observe(el);
      }
    });
  }

  ngOnDestroy(): void {
    this.observer?.disconnect();
  }

  jump(id: string): void {
    document.getElementById(id)?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }
}
