include *.mk

cluster?=nats
export KUBECONFIG=$(HOME)/.k3d/kubeconfig-$(cluster).yaml

## create cluster and deploy nats
kubes: cluster nats

## create k3s cluster
cluster:
	k3d cluster create $(cluster) -p 4222:4222@loadbalancer -p 8222:80@loadbalancer --wait
	@k3d kubeconfig write $(cluster) > /dev/null
	@echo "Probing until cluster is ready (~60 secs)..."
	@while ! kubectl get crd ingressroutes.traefik.containo.us 2> /dev/null ; do sleep 10 && echo $$((i=i+10)); done
	@echo -e "\nTo use your cluster set:\n"
	@echo "export KUBECONFIG=$(KUBECONFIG)"

## deploy nats to kubes
nats:
	helm repo add nats https://nats-io.github.io/k8s/helm/charts/
	helm repo update nats
	helm upgrade --install nats nats/nats --version=1.0.3 --values infra/values.yaml --wait --debug > /dev/null

## ping nats
ping:
	cat <(echo -e 'CONNECT {}') <(sleep 1) | nc localhost 4222

## publish using nats-box
pub:
	kubectl exec -it deployment/nats-box -- nats pub test hi

## demo js
demo-js: $(venv)
	$(venv)/bin/python -m demo.js

## list streams using cli
stream-ls:
	hash nats || brew install nats-io/nats-tools/nats
	nats stream ls

## show kube logs
logs:
	kubectl logs -l "app.kubernetes.io/name=nats,app.kubernetes.io/instance=nats" -c nats -f --tail=-1

