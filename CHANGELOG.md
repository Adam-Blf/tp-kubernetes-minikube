# Changelog

Format inspiré de Keep a Changelog, versions en semver.

## [1.0.0] - 2026-10-19

### Ajouté

- Manifestes du TP : Pod autonome, Deployment `whoami` à 3 réplicas, Service ClusterIP, Deployment `monapp`.
- Image personnalisée `monapp:1.0` (nginx 1.27, page en français) chargée dans Minikube.
- Preuves rejouées de bout en bout le 19/10/2026 : 10 captures légendées (dont 2 vues navigateur) et leurs sorties brutes, dont le Pod en `Terminating` à côté de son remplaçant et la mise à l'échelle à 5 Pods.
- Lecture du `hostname` du Pod autonome par `kubectl debug`, l'image n'ayant pas de shell.
- Habillage aux couleurs EFREI (captures, rapport PDF, page monapp, diagramme), police Gilroy si installée.
- Rapport complet `docs/RAPPORT.md` et sa version PDF, mini doc `docs/pod-autonome.md` reprise du travail d'Emilien Morice.
- Scripts `rejouer_tp.sh` et `render_preuves.py`.
- CI : kubeconform, hadolint, contrôle des livrables, déploiement e2e sur kind. Release : archive de rendu et image GHCR.
