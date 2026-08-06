import { Component } from '@angular/core';
import { RouterLink } from '@angular/router';
import { LineSidebarComponent } from '../../shared/line-sidebar.component';

// AEGIS landing page. Stage 14 lays out the six-section spine as anchored
// placeholders so the Line Sidebar and routing work end to end. Later stages
// fill each section with its real content, the network background, and motion.
@Component({
  selector: 'app-home',
  standalone: true,
  imports: [RouterLink, LineSidebarComponent],
  styleUrl: './home.page.scss',
  template: `
    <app-line-sidebar />

    <main>
      <!-- HERO -->
      <section id="hero" class="hero">
        <div class="container">
          <p class="eyebrow">Trusted Enterprise AI</p>
          <h1 class="hero-title">
            <span class="mark">AEGIS</span>
          </h1>
          <p class="lede">
            Ask your enterprise archive in plain language. Every answer cited,
            every access controlled, every threat filtered. Built for secure
            organizations.
          </p>
          <div class="actions">
            <a routerLink="/app" class="btn btn-primary">Open the console</a>
            <a href="#how" class="btn btn-ghost">See how it works</a>
          </div>
        </div>
      </section>

      <!-- PROBLEM -->
      <section id="problem" class="section">
        <div class="container">
          <p class="eyebrow">The problem</p>
          <h2>Your data is archived, but locked.</h2>
          <p class="prose">
            Companies archive legacy systems and switch them off. The data
            survives, but using it means knowing the right tables out of
            thousands and writing SQL. And you cannot safely point an AI at raw
            enterprise data — it holds personal information and invites misuse.
          </p>
        </div>
      </section>

      <!-- HOW IT WORKS -->
      <section id="how" class="section">
        <div class="container">
          <p class="eyebrow">How it works</p>
          <h2>Five layers of protection.</h2>
          <p class="prose">
            Input filter, pseudonymized data, a policy-bound agent, an output
            scan, and live metrics — the request passes through each in turn.
          </p>
          <!-- Stage 16: the animated five-layer diagram lands here. -->
        </div>
      </section>

      <!-- METRICS -->
      <section id="metrics" class="section">
        <div class="container">
          <p class="eyebrow">Results</p>
          <h2>Measured, not claimed.</h2>
          <p class="prose">
            Detection F1, injection catch rate, zero data leaks, cost per
            thousand records — all measured live.
          </p>
          <!-- Stage 17: count-up metric counters land here. -->
        </div>
      </section>

      <!-- TECH -->
      <section id="tech" class="section">
        <div class="container">
          <p class="eyebrow">Built with</p>
          <h2>A stack you can inspect.</h2>
          <p class="prose">
            FastAPI, Presidio NER, sqlglot policy enforcement, Angular, and the
            Claude API — every layer open to scrutiny.
          </p>
        </div>
      </section>

      <!-- CTA -->
      <section id="cta" class="section cta">
        <div class="container">
          <h2>See it answer — safely.</h2>
          <a routerLink="/app" class="btn btn-primary">Open the console</a>
        </div>
      </section>
    </main>
  `,
})
export class HomePage {}
