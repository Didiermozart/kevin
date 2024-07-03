2# Variables
IMAGE_NAME = kevin_project
CONTAINER_NAME = kevin_container
HOST_PORT = 8000
CONTAINER_PORT = 8000
VOLUME_PATH = /path/to/local/directory
CONTAINER_VOLUME_PATH = /app/images
IP_ADDRESS = 172.20.0.2

# Construire l'image Docker
build:
	docker build -t $(IMAGE_NAME) .

# Exécuter le conteneur Docker avec un volume persistant et une IP définie
run:
	docker run -d \
		--name $(CONTAINER_NAME) \
		-p $(HOST_PORT):$(CONTAINER_PORT) \
		-v $(VOLUME_PATH):$(CONTAINER_VOLUME_PATH) \
		--ip $(IP_ADDRESS) \
		$(IMAGE_NAME)

# Arrêter et supprimer le conteneur Docker
clean:
	docker stop $(CONTAINER_NAME)
	docker rm $(CONTAINER_NAME)

# Supprimer l'image Docker
prune:
	docker image rm $(IMAGE_NAME)
