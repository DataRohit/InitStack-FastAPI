# Cross-Platform Color Definitions
ifeq ($(OS),Windows_NT)
    # Git Bash Support Only
    ifeq ($(shell echo $$BASH_VERSION 2>/dev/null),)
        $(error This Makefile only supports Git Bash on Windows)
    endif
    GREEN=\033[0;32m
    BLUE=\033[0;34m
    YELLOW=\033[1;33m
    RED=\033[0;31m
    NC=\033[0m
else
    # Unix Systems Have Full ANSI Color Support
    GREEN=\033[0;32m
    BLUE=\033[0;34m
    YELLOW=\033[1;33m
    RED=\033[0;31m
    NC=\033[0m
endif

ECHO_CMD=echo
GREEN_START=${GREEN}
BLUE_START=${BLUE}
YELLOW_START=${YELLOW}
RED_START=${RED}
COLOR_END=${NC}

# Display Available Makefile Commands
help:
	@echo ""
	@printf "${BLUE}InitStack Makefile Commands${NC}\n"
	@echo ""
	@printf "${GREEN}General:${NC}\n"
	@echo "  help        - Show This Help Message"
	@echo ""
	@printf "${GREEN}Code Analysis:${NC}\n"
	@echo "  sonar-scan  - Run SonarQube Analysis For The Project"
	@echo ""
	@printf "${GREEN}Docker:${NC}\n"
	@echo "  docker-up      - Build and start all Docker containers"
	@echo "  docker-restart - Restart all containers and nginx-service"
	@echo ""

# Execute SonarQube Code Analysis
sonar-scan:
	@echo ""
	@printf "${YELLOW}Starting SonarScanner...${NC}\n"
	sonar-scanner \
		-Dsonar.host.url=http://localhost:9000 \
		-Dsonar.projectKey=InitStack \
		-Dsonar.login=sqp_a046f1a745639c2e11ac52953bc478ef8afc7bc2
	@printf "${GREEN}SonarQube scan completed!${NC}\n"
	@echo ""

# Docker Commands
docker-up:
	@echo ""
	@printf "${YELLOW}Building and starting Docker containers...${NC}\n"
	docker compose build && docker compose up -d --remove-orphans
	@printf "${GREEN}Docker containers started successfully!${NC}\n"
	@echo ""

docker-restart:
	@echo ""
	@printf "${YELLOW}Restarting Docker containers...${NC}\n"
	docker compose restart && docker compose restart nginx-service
	@printf "${GREEN}Docker containers restarted successfully!${NC}\n"
	@echo ""

.PHONY: help sonar-scan docker-up docker-restart
