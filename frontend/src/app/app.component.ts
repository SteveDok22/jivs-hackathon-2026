import { Component } from '@angular/core';
import { RouterOutlet } from '@angular/router';

// Root shell. Pages own their own layout; the shell only hosts the outlet.
@Component({
  selector: 'app-root',
  standalone: true,
  imports: [RouterOutlet],
  template: `<router-outlet />`,
})
export class AppComponent {}
