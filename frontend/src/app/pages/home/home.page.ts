import { AfterViewInit, Component, ElementRef, inject } from '@angular/core';
import { RouterLink } from '@angular/router';
import anime from 'animejs';
import { LineSidebarComponent } from '../../shared/line-sidebar.component';
import { NetworkBackgroundComponent } from '../../shared/network-background.component';
import { FiveLayersComponent } from '../../shared/five-layers.component';
import { HeroDemoComponent } from '../../shared/hero-demo.component';
import { GridScanComponent } from '../../shared/grid-scan.component';
import { RevealDirective } from '../../shared/reveal.directive';
import { CountUpDirective } from '../../shared/count-up.directive';

// AEGIS landing page. Stage 14 lays out the six-section spine as anchored
// placeholders so the Line Sidebar and routing work end to end. Later stages
// fill each section with its real content, the network background, and motion.
@Component({
  selector: 'app-home',
  standalone: true,
  imports: [
    RouterLink,
    LineSidebarComponent,
    NetworkBackgroundComponent,
    FiveLayersComponent,
    HeroDemoComponent,
    GridScanComponent,
    RevealDirective,
    CountUpDirective,
  ],
  styleUrl: './home.page.scss',
  template: `
    <app-line-sidebar />

    <main>
      <!-- HERO -->
      <section id="hero" class="hero">
        <app-network-bg />
        <div class="container hero-content">
          <p class="eyebrow anim-in">Trusted Enterprise AI</p>
          <h1 class="hero-title anim-in">
            <span class="mark">AEGIS</span>
          </h1>
          <p class="lede anim-in">
            Ask your enterprise archive in plain language. Every answer cited,
            every access controlled, every threat filtered. Built for secure
            organizations.
          </p>

          <div class="hero-demo-wrap anim-in">
            <app-hero-demo />
          </div>

          <div class="hero-flow anim-in">
            <app-five-layers />
          </div>

          <div class="actions anim-in">
            <a routerLink="/app" class="btn btn-primary">Open the console</a>
            <a href="#how" class="btn btn-ghost">See how it works</a>
          </div>
        </div>
      </section>

      <!-- PROBLEM -->
      <section id="problem" class="section">
        <div class="container">
          <p class="eyebrow" appReveal>The problem</p>
          <h2 [appReveal]="80">Your data is archived, but locked.</h2>
          <p class="prose" [appReveal]="160">
            Companies archive legacy systems and switch them off. The data
            survives, but using it means knowing the right tables out of
            thousands and writing SQL. And you cannot safely point an AI at raw
            enterprise data: it holds personal information and invites misuse.
          </p>
          <div class="problem-grid">
            <div class="card pad" [appReveal]="80">
              <span class="big mono">1000s</span>
              <span class="cap">of tables to know before you can ask one question</span>
            </div>
            <div class="card pad" [appReveal]="160">
              <span class="big mono">20 yrs</span>
              <span class="cap">of one person's data scattered across systems, misspelled</span>
            </div>
            <div class="card pad" [appReveal]="240">
              <span class="big mono">4%</span>
              <span class="cap">of global revenue — the GDPR fine for getting PII wrong</span>
            </div>
          </div>
        </div>
      </section>

      <!-- HOW IT WORKS -->
      <section id="how" class="section how">
        <app-grid-scan />
        <div class="container how-content">
          <p class="eyebrow" appReveal>How it works</p>
          <h2 [appReveal]="80">Five layers of protection.</h2>
          <p class="prose" [appReveal]="160">
            Every request passes through each layer in turn. Break one and the
            next still holds — defense in depth, not a single gate.
          </p>
          <div class="layer-cards">
            @for (layer of howLayers; track layer.n) {
              <div class="card pad layer-card" [appReveal]="layer.n * 70">
                <span class="num mono">0{{ layer.n }}</span>
                <h3>{{ layer.title }}</h3>
                <p>{{ layer.body }}</p>
              </div>
            }
          </div>
        </div>
      </section>

      <!-- METRICS -->
      <section id="metrics" class="section">
        <div class="container">
          <p class="eyebrow" appReveal>Results</p>
          <h2 [appReveal]="80">Measured, not claimed.</h2>
          <p class="prose" [appReveal]="160">
            Every number below comes from the project's own evaluation harness,
            run against a synthetic enterprise dataset with a known answer key.
          </p>
          <div class="metrics-grid">
            <div class="metric card pad" [appReveal]="60">
              <span class="value mono" [appCountUp]="169">0</span>
              <span class="mlabel">names discovered by NER</span>
              <span class="mnote">beyond the 3-name watch-list</span>
            </div>
            <div class="metric card pad" [appReveal]="130">
              <span class="value mono" [appCountUp]="100" suffix="%">0</span>
              <span class="mlabel">prompt-injection catch rate</span>
              <span class="mnote">0% false positives on benign input</span>
            </div>
            <div class="metric card pad" [appReveal]="200">
              <span class="value mono" [appCountUp]="1" [decimals]="2">0</span>
              <span class="mlabel">PII detection F1</span>
              <span class="mnote">precision 1.00 · recall 1.00</span>
            </div>
            <div class="metric card pad" [appReveal]="270">
              <span class="value mono" [appCountUp]="0">0</span>
              <span class="mlabel">data leaks after pseudonymization</span>
              <span class="mnote">joins stay intact, data still usable</span>
            </div>
          </div>
        </div>
      </section>

      <!-- TECH -->
      <section id="tech" class="section">
        <div class="container">
          <p class="eyebrow" appReveal>Built with</p>
          <h2 [appReveal]="80">A stack you can inspect.</h2>
          <p class="prose" [appReveal]="160">
            No black boxes. Every layer is open to scrutiny — the security
            argument depends on it.
          </p>
          <div class="tech-row" [appReveal]="200">
            @for (tech of techStack; track tech) {
              <span class="chip mono">{{ tech }}</span>
            }
          </div>
        </div>
      </section>

      <!-- CTA -->
      <section id="cta" class="section cta">
        <div class="container">
          <h2 appReveal>See it answer — safely.</h2>
          <p class="prose center" [appReveal]="80">
            Ask a question, watch it get filtered, checked, and cited in real time.
          </p>
          <a routerLink="/app" class="btn btn-primary" [appReveal]="160">Open the console</a>
        </div>
      </section>

      <footer class="footer">
        <div class="container foot">
          <span class="brand-mark">AEGIS</span>
          <span class="foot-note">Trusted Enterprise AI · a portfolio project</span>
        </div>
      </footer>

    </main>
  `,
})
export class HomePage implements AfterViewInit {
  private readonly host = inject<ElementRef<HTMLElement>>(ElementRef);

  readonly howLayers = [
    { n: 1, title: 'Input filter', body: 'Prompt-injection attempts are caught before the agent runs — layered heuristics plus an optional classifier.' },
    { n: 2, title: 'Pseudonymized data', body: 'The model only ever sees masked data: names replaced consistently across tables, so joins and statistics survive.' },
    { n: 3, title: 'Policy-bound agent', body: 'Generated SQL is parsed and checked against an explicit policy before it touches the database. The model has no direct access.' },
    { n: 4, title: 'Output scan', body: 'The answer is scanned on the way out; any restricted PII is redacted even if an earlier layer let it through.' },
    { n: 5, title: 'Cited answer', body: 'Every answer carries its sources — the exact tables and rows it came from — so it can be trusted and verified.' },
  ];

  readonly techStack = [
    'FastAPI', 'Python 3.12', 'Presidio NER', 'sqlglot', 'DuckDB',
    'Claude API', 'Angular 20', 'Anime.js', 'Docker', 'pytest',
  ];

  ngAfterViewInit(): void {
    const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    const targets = this.host.nativeElement.querySelectorAll('.hero .anim-in');

    if (reduced) {
      targets.forEach((el: Element) => ((el as HTMLElement).style.opacity = '1'));
      return;
    }

    // Staggered entrance: each hero element fades and rises in sequence.
    anime({
      targets: targets,
      opacity: [0, 1],
      translateY: [20, 0],
      delay: anime.stagger(120, { start: 150 }),
      duration: 700,
      easing: 'easeOutExpo',
    });
  }
}
