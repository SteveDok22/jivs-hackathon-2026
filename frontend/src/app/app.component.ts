import { Component } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { CursorComponent } from './shared/cursor.component';

// Root shell: hosts the router outlet and the site-wide custom cursor.
// Pages own their own layout.
@Component({
  selector: 'app-root',
  standalone: true,
  imports: [RouterOutlet, CursorComponent],
  template: `
    <app-cursor />
    <router-outlet />
  `,
})
export class AppComponent {}
