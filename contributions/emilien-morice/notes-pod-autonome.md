# Pod autonome vs Deployment

## Ce qu'on fait ici

On crée un **Pod autonome** : un seul conteneur `traefik/whoami` qui tourne directement dans Kubernetes, sans aucune supervision.

## Pourquoi ce test ?

Pour comprendre la limite d'un Pod seul. Kubernetes ne surveille pas les Pods autonomes.

## Ce qu'on observe

1. On applique `pod.yaml` → Kubernetes crée le pod `whoami-pod`
2. On vérifie qu'il tourne (`kubectl get pods`)
3. On entre dedans (`kubectl exec`) → le hostname retourné est `whoami-pod`
4. On le supprime (`kubectl delete pod whoami-pod`)
5. On vérifie (`kubectl get pods`) → **il ne revient pas**

## Conclusion

Un Pod autonome = aucune résilience. Si le pod plante ou est supprimé, c'est terminé.
C'est pour ça qu'on utilise un **Deployment** en pratique : il garantit qu'un nombre
défini de réplicas tourne en permanence et recrée automatiquement tout pod disparu.
