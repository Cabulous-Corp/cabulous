RUN_ARGS := $(wordlist 2,$(words $(MAKECMDGOALS)),$(MAKECMDGOALS))

$(eval $(RUN_ARGS):;@:)

.DEFAULT_GOAL := help

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

dev: ## Run development server
	@echo "Starting development server..."
	@bun run dev

build: ## Build the NextJS app
	@echo "Building app..."
	@bun run build

setup: ## Setup the project (copy .env, install deps)
	@echo "Checking for .env file..."
	@bun -e "const fs = require('fs'); if (!fs.existsSync('.env')) { fs.copyFileSync('.env.example', '.env'); console.log('Created .env from .env.example') } else { console.log('.env already exists, skipping copy.') }"
	@make install --no-print-directory
	@echo "Setup complete! Run 'make dev' to start."

install: ## Install dependencies
	@echo "Installing dependencies..."
	@bun install

lint: ## Run lint
	@echo "Running lint..."
	@bun run lint

lint-fix: ## Run lint and fix issues
	@echo "Running lint..."
	@bun run lint:fix

lint-fix-unsafe: ## Run lint and fix issues (unsafe)
	@echo "Running lint..."
	@bun run lint:fix-unsafe

generate-api-types: ## Generate API types
	@echo "Downloading API schema..."
	@curl http://localhost:8000/openapi.json > openapi.json
	@echo "Generating API types..."
	@bunx openapi-typescript openapi.json -o ./types/api.d.ts
	@rm openapi.json
	@echo "API types generated successfully!"
