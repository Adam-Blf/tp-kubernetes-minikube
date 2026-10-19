#!/usr/bin/env bash
# Rejoue le TP Kubernetes du paragraphe 3 au paragraphe 10 et capture chaque sortie.
set -u
# Sous Windows, ajouter le dossier de minikube.exe au PATH si besoin.
export PATH="/c/Program Files/Kubernetes/Minikube:$PATH"
R="${1:-$(cd "$(dirname "$0")/.." && pwd)}"; O="$R/preuves-new"
rm -rf "$O"; mkdir -p "$O"; cd "$R"
F=""
sec() { F="$O/$1.txt"; : > "$F"; }
run() { printf '$ %s\n' "$*" >> "$F"; bash -c "$*" >> "$F" 2>&1; echo >> "$F"; }
note() { printf '# %s\n\n' "$*" >> "$F"; }

sec 01-cluster
run docker version
run kubectl version --client
run minikube version
run minikube start --driver=docker
run minikube status
run "docker ps --format 'table {{.Names}}\t{{.Image}}\t{{.Status}}'"
run kubectl cluster-info
run kubectl get nodes -o wide
run kubectl get pods -A

sec 06-pod-autonome
run kubectl create namespace demo
run kubectl config set-context --current --namespace=demo
run kubectl apply -f manifests/pod.yaml
run kubectl wait --for=condition=Ready pod/whoami-pod --timeout=180s
run kubectl get pods -o wide
run "kubectl describe pod whoami-pod | head -n 30"
run kubectl logs whoami-pod
run kubectl exec whoami-pod -- sh -c hostname
note "traefik/whoami ne contient ni shell ni binaire hostname : on attache un conteneur de débogage busybox qui partage l'espace de noms du Pod."
run kubectl debug whoami-pod -q --image=busybox:1.36 --target=whoami --attach=true -- hostname
run kubectl delete pod whoami-pod
run kubectl get pods
note "Le Pod autonome ne revient pas : aucun contrôleur ne le surveille."

sec 02-deployment
run kubectl apply -f manifests/deployment.yaml
run kubectl rollout status deployment/whoami --timeout=180s
run kubectl get deployment,replicaset,pods
run kubectl get pods --show-labels
run "kubectl describe deployment whoami | head -n 30"

sec 03-autoreparation
run kubectl get pods
VICTIME=$(kubectl get pods -l app=whoami -o jsonpath='{.items[0].metadata.name}')
kubectl get pods -w --output-watch-events > "$O/watch.log" 2>&1 & WP=$!
sleep 2
run kubectl delete pod "$VICTIME" --wait=false
run kubectl get pods
note "Ci-dessus : le Pod supprimé est en Terminating à côté de son remplaçant créé par le ReplicaSet."
sleep 12
kill $WP 2>/dev/null
printf '$ kubectl get pods -w --output-watch-events   (second terminal, Ctrl+C apres 12 s)\n' >> "$F"
cat "$O/watch.log" >> "$F"; echo >> "$F"; rm -f "$O/watch.log"
run kubectl get pods

sec 03b-mise-a-l-echelle
run kubectl scale deployment whoami --replicas=5
run kubectl rollout status deployment/whoami --timeout=120s
run kubectl get pods
run kubectl scale deployment whoami --replicas=0
run kubectl get pods
sleep 8
run kubectl get pods
run kubectl scale deployment whoami --replicas=3
run kubectl rollout status deployment/whoami --timeout=120s
run kubectl get pods

sec 04-service-http
run kubectl apply -f manifests/service.yaml
run kubectl get services
run kubectl get endpoints whoami-service
run kubectl get pods -o wide
kubectl port-forward service/whoami-service 8080:80 > /dev/null 2>&1 & PF=$!
sleep 4
run curl -s http://localhost:8080
kill $PF 2>/dev/null

sec 05-image-personnalisee
run "docker build -t monapp:1.0 ./monapp 2>&1 | tail -n 12"
run minikube image load monapp:1.0
run "minikube image ls | grep monapp"
run kubectl apply -f monapp-deployment.yaml
run kubectl rollout status deployment/monapp --timeout=120s
run kubectl get pods -l app=monapp
kubectl port-forward deployment/monapp 8081:80 > /dev/null 2>&1 & PF=$!
sleep 4
run curl -s http://localhost:8081
kill $PF 2>/dev/null

sec 10-nettoyage
run kubectl delete -f manifests/service.yaml --ignore-not-found
run kubectl delete -f manifests/deployment.yaml --ignore-not-found
run kubectl delete -f manifests/pod.yaml --ignore-not-found
run kubectl delete -f monapp-deployment.yaml --ignore-not-found
run kubectl delete namespace demo
run kubectl config set-context --current --namespace=default
run minikube stop
echo FIN
