// Adresse publique du relais PRIM (Cloudflare Worker du dossier metro-proxy/), sans barre finale.
// Renseignée automatiquement par le workflow « Relais PRIM » après le déploiement, par exemple :
//   proxy: 'https://metro-prim.mon-compte.workers.dev'
// Sans relais, l'appli propose de saisir une clé PRIM personnelle (gardée sur le téléphone).
window.METRO_CONFIG = {
  proxy: '',
};
