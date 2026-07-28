// Dev: empty base -> requests go through Angular's proxy (proxy.conf.json)
// to the FastAPI server, which sidesteps CORS during development.
export const environment = {
  production: false,
  apiBase: '',
};
