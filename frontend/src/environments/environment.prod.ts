// Prod (Vercel): no backend is deployed, so demo mode serves captured real
// responses and the console shows a "run locally" note. This keeps the public
// site live and free while the full agent runs locally from the repo.
export const environment = {
  production: true,
  demoMode: true,
  apiBase: '',
  repoUrl: 'https://github.com/SteveDok22/jivs-hackathon-2026',
};
