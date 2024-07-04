# Variables
IMAGE_NAME = kevin_project
CONTAINER_NAME = kevin_container
HOST_PORT = 8000
CONTAINER_PORT = 8000
VOLUME_PATH = /path/to/local/directory
CONTAINER_VOLUME_PATH = /app/images
NETWORK_NAME = kevin_network
IP_ADDRESS = 172.20.0.2
SUBNET = 172.20.0.0/16

# Construire l'image Docker
build:
	docker build -t $(IMAGE_NAME) .

# Créer le réseau Docker
network:
	docker network create --subnet=$(SUBNET) $(NETWORK_NAME) || true


clean-container:
	docker stop $(CONTAINER_NAME) || true
	docker rm $(CONTAINER_NAME) || true

# Exécuter le conteneur Docker avec un volume persistant, un réseau et une IP définis
run: network clean-container
	docker run -d \
		--name $(CONTAINER_NAME) \
		-p $(HOST_PORT):$(CONTAINER_PORT) \
		-v $(VOLUME_PATH):$(CONTAINER_VOLUME_PATH) \
		--network $(NETWORK_NAME) \
		--ip $(IP_ADDRESS) \
		$(IMAGE_NAME)


# Arrêter et supprimer le conteneur Docker
clean:
	docker stop $(CONTAINER_NAME)
	docker rm $(CONTAINER_NAME)

# Supprimer l'image Docker
prune: clean
	docker image rm $(IMAGE_NAME)

# Supprimer le réseau Docker
network-clean:
	docker network rm $(NETWORK_NAME)

# View the logs of the running container
logs:
	docker logs -f $(CONTAINER_NAME)

export:
	docker save -o $(CONTAINER_NAME).tar $(CONTAINER_NAME)


