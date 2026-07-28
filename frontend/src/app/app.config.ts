import { ApplicationConfig, provideZonelessChangeDetection } from '@angular/core';
import { provideHttpClient } from '@angular/common/http';

// Zoneless: Angular 20 can run without zone.js, driven by signals.
// Lighter and a good talking point ("modern Angular") for the JiVS jury.
export const appConfig: ApplicationConfig = {
  providers: [
    provideZonelessChangeDetection(),
    provideHttpClient(),
  ],
};
