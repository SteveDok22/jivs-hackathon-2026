import { Routes } from '@angular/router';

// Two pages: the AEGIS landing (/) and the working product (/app).
// Lazy-loaded so the landing never ships the product's code and vice versa.
export const routes: Routes = [
  {
    path: '',
    loadComponent: () => import('./pages/home/home.page').then((m) => m.HomePage),
    title: 'AEGIS — Trusted Enterprise AI',
  },
  {
    path: 'app',
    loadComponent: () =>
      import('./pages/product/product.page').then((m) => m.ProductPage),
    title: 'AEGIS — Console',
  },
  { path: '**', redirectTo: '' },
];
