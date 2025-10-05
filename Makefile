.PHONY: help build run stop restart logs status clean shell

help: ## Show this help message
	@echo "Discord Voice Bot - Docker Commands"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

build: ## Build the Docker image
	docker-compose build

run: ## Start the bot
	docker-compose up -d

stop: ## Stop the bot
	docker-compose down

restart: ## Restart the bot
	docker-compose restart

logs: ## Show bot logs
	docker-compose logs -f

status: ## Show container status
	docker-compose ps

clean: ## Clean up containers and images
	docker-compose down --rmi all --volumes --remove-orphans

shell: ## Access bot container shell
	docker-compose exec discord-bot /bin/bash
