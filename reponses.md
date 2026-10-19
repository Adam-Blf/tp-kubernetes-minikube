# Réponses aux questions du TP Kubernetes

## Question de la partie 3 : nœud et composants système

Le cluster ne compte qu'un seul nœud, `minikube`, de rôle `control-plane`, au statut `Ready` (Kubernetes v1.37.0, IP interne 192.168.49.2, runtime `containerd://2.3.4`, Debian 12). Il porte à la fois le plan de contrôle et les charges applicatives.

Trois composants système observés dans `kubectl get pods -A` (namespace `kube-system`) :

- `kube-apiserver-minikube` : point d'entrée de l'API Kubernetes, par lequel passent kubectl et tous les autres composants.
- `etcd-minikube` : base clé-valeur qui stocke l'état du cluster.
- `coredns-559f6c778d-wmzmz` : service DNS interne qui résout les noms de Services.

On aurait pu citer aussi `kube-scheduler`, `kube-controller-manager`, `kube-proxy` ou `kindnet` (réseau).

## Pod autonome vs Pod géré par un Deployment

Démarche du test (rédigée par Emilien Morice, vérifiée sur notre cluster) : on applique `pod.yaml`, Kubernetes crée `whoami-pod` ; on vérifie qu'il tourne avec `kubectl get pods` ; on le supprime avec `kubectl delete pod whoami-pod` ; un nouveau `kubectl get pods` montre qu'il ne revient pas. Le but est de montrer la limite d'un Pod seul, que rien ne supervise.

Un Pod autonome est créé directement : si on le supprime (`kubectl delete pod whoami-pod`), il disparaît définitivement, comme on l'a constaté avec `kubectl get pods` qui ne renvoie plus rien. Rien ne surveille son état et il ne peut pas être mis à l'échelle ni mis à jour progressivement.

Un Pod géré par un Deployment appartient à un ReplicaSet qui maintient le nombre de réplicas voulu. En supprimant le Pod `whoami-c6f799d48-9qwp6`, un nouveau Pod (`whoami-c6f799d48-n6kgw`) est apparu en quelques secondes et on est resté à 3 Pods. Le Deployment apporte aussi `scale` et les mises à jour progressives avec retour arrière.

## Rôle du ReplicaSet dans l'auto-réparation

Le Deployment crée et pilote un ReplicaSet (ici `whoami-c6f799d48`). Le ReplicaSet compare en continu le nombre de Pods qui correspondent à son sélecteur (`app: whoami`) avec le nombre désiré (`replicas`). Quand un Pod disparaît, l'écart est détecté et le ReplicaSet en crée un nouveau pour revenir à l'état désiré. C'est une boucle de réconciliation : le même mécanisme joue pour le `scale` à 5 (deux Pods créés), puis à 0 (tous supprimés), puis à 3.

## Rôle du Service et vérification de son ciblage

Les Pods sont éphémères et leurs adresses IP changent à chaque recréation. Le Service `whoami-service` (type ClusterIP) offre une adresse IP virtuelle et un nom DNS stables dans le cluster, et répartit le trafic vers les Pods dont les labels correspondent à son `selector` (`app: whoami`). Le champ `targetPort: http` désigne le port nommé `http` des conteneurs (80).

Pour vérifier qu'il cible les bons Pods :

- `kubectl get endpoints whoami-service` (ou `kubectl get endpointslices`) : les adresses listées (10.244.0.15, 10.244.0.16 et 10.244.0.17, port 80) doivent être celles des Pods affichés par `kubectl get pods -o wide`.
- `kubectl get pods --show-labels` : les Pods doivent porter `app=whoami`.
- `kubectl describe service whoami-service` : affiche le Selector et les Endpoints.
- Un `curl` via `port-forward` renvoie le `Hostname` d'un Pod du Deployment.

Si le sélecteur ne correspond à aucun label, la liste des endpoints est vide et le Service ne répond pas.

## Pourquoi charger l'image dans Minikube et `imagePullPolicy: Never`

Le nœud Minikube est un conteneur avec son propre runtime (containerd) et son propre stock d'images, distinct de celui du Docker de l'hôte. L'image `monapp:1.0`, construite localement, n'existe donc pas dans le nœud et n'est publiée sur aucun registre. `minikube image load monapp:1.0` la copie dans le stock du nœud. Avec `imagePullPolicy: Never`, kubelet utilise uniquement l'image déjà présente et ne tente jamais de la télécharger : sans cela, il chercherait `monapp:1.0` sur Docker Hub et le Pod finirait en `ErrImagePull` ou `ImagePullBackOff`. Si l'image n'a pas été chargée, le Pod échoue avec `ErrImageNeverPull`.
