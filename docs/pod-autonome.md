# Mini doc : Pod autonome vs Deployment

Première version rédigée par Emilien Morice (original conservé dans
`contributions/emilien-morice/`), mise à jour après exécution sur notre cluster.

## Ce qu'on fait ici

On crée un **Pod autonome** : un seul conteneur `traefik/whoami:v1.10.3` qui tourne
directement dans Kubernetes, sans contrôleur pour le surveiller. Manifeste :
`manifests/pod.yaml`.

## Pourquoi ce test

Pour voir la limite d'un Pod seul : Kubernetes ne recrée pas un Pod qu'aucun
contrôleur (ReplicaSet, Deployment, StatefulSet...) ne possède.

## Déroulé observé

1. `kubectl apply -f manifests/pod.yaml` : Kubernetes crée `whoami-pod`.
2. `kubectl get pods -o wide` : le Pod est `Running`.
3. `kubectl exec -it whoami-pod -- sh` **échoue** : l'image `traefik/whoami` ne
   contient ni shell ni binaire `hostname`. On lit donc le nom d'hôte avec un
   conteneur de débogage éphémère qui partage l'espace de noms du Pod :
   `kubectl debug whoami-pod -q --image=busybox:1.36 --target=whoami --attach=true -- hostname`
   renvoie `whoami-pod`. Le nom d'hôte apparaît aussi dans la réponse HTTP (`Hostname:`).
4. `kubectl delete pod whoami-pod`.
5. `kubectl get pods` : **il ne revient pas**.

Preuve : `preuves/06-pod-autonome.png`.

## Deux choix dans le manifeste

- **Label `app: whoami-pod`**, et non `app: whoami`. Le Service `whoami-service`
  sélectionne `app: whoami` : avec le même label, le Pod autonome recevrait aussi
  du trafic du Service tant qu'il coexiste avec les Pods du Deployment.
- **Port nommé `http`**, pour rester cohérent avec `targetPort: http` du Service.

## Conclusion

Un Pod autonome n'a aucune résilience : supprimé ou planté, il est perdu. En
pratique on passe par un **Deployment**, qui crée un ReplicaSet chargé de maintenir
le nombre de réplicas voulu et de recréer tout Pod disparu (`preuves/03-autoreparation.png`).
