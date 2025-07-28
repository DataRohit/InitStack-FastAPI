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
	@printf "${GREEN}Podman:${NC}\n"
	@echo "  podman-build    - Build All Services"
	@echo "  podman-up       - Build And Start All Services"
	@echo "  podman-restart  - Restart All Services"
	@echo "  podman-clean            - Clean Unused Podman Resources"
	@echo ""
	@printf "${GREEN}Docker:${NC}\n"
	@echo "  docker-build    - Build All Services"
	@echo "  docker-up       - Build And Start All Services"
	@echo "  docker-restart  - Restart All Services"
	@echo "  docker-clean            - Clean Unused Docker Resources"
	@echo ""
	@printf "${GREEN}Cleaning:${NC}\n"
	@echo "  clean-all      - Remove Python-related garbage files"
	@echo ""

# Execute SonarQube Code Analysis
sonar-scan:
	@echo ""
	@printf "${YELLOW}Starting Sonarscanner...${NC}\n"
	sonar-scanner \
		-D sonar.host.url=http://localhost:9000 \
		-D sonar.projectKey=InitStack \
		-D sonar.login=sqp_91d0028a2f5c1eb2bc80b0901ae524d01466505b
	@printf "${GREEN}SonarQube Scan Completed!${NC}\n"
	@echo ""

# Build All Services
podman-build:
	@echo ""
	@printf "${YELLOW}Building All Services...${NC}\n"
	podman compose build --detach
	@printf "${GREEN}Services Built Successfully!${NC}\n"
	@echo ""

# Build And Start All Services
podman-up:
	@echo ""
	@printf "${YELLOW}Building And Starting Services...${NC}\n"
	podman compose up -d --build --detach
	@printf "${GREEN}Services Built And Started Successfully!${NC}\n"
	@echo ""

# Restart All Services
podman-restart:
	@echo ""
	@printf "${YELLOW}Restarting Services...${NC}\n"
	podman compose restart
	@printf "${GREEN}Services Restarted Successfully!${NC}\n"
	@echo ""

# Clean Podman Resources
podman-clean:
	@echo ""
	@printf "${YELLOW}Cleaning Unused Podman Resources...${NC}\n"
	podman system prune -f --filter "until=24h"
	podman builder prune -f
	@printf "${GREEN}Podman Resources Cleaned Successfully!${NC}\n"
	@echo ""

# Docker Commands
docker-build:
	@echo ""
	@printf "${YELLOW}Building All Services With Docker...${NC}\n"
	docker compose build
	@printf "${GREEN}Services Built Successfully With Docker!${NC}\n"
	@echo ""

docker-up:
	@echo ""
	@printf "${YELLOW}Building And Starting Services With Docker...${NC}\n"
	docker compose up -d --build
	@printf "${GREEN}Services Built And Started Successfully With Docker!${NC}\n"
	@echo ""

docker-restart:
	@echo ""
	@printf "${YELLOW}Restarting Services With Docker...${NC}\n"
	docker compose restart
	@printf "${GREEN}Services Restarted Successfully With Docker!${NC}\n"
	@echo ""

docker-clean:
	@echo ""
	@printf "${YELLOW}Cleaning Unused Docker Resources...${NC}\n"
	docker system prune -f --filter "until=24h"
	docker builder prune -f
	@printf "${GREEN}Docker Resources Cleaned Successfully!${NC}\n"
	@echo ""

# Clean All Python Related Files
clean-all:
	@echo ""
	@printf "${YELLOW}Cleaning all Python-related files...${NC}\n"
	rm -rf .pytest_cache/ .coverage .scannerwork/ __pycache__/ build/ dist/ *.egg-info/ *.pyc *.pyo
	@printf "${GREEN}Python files cleaned successfully!${NC}\n"
	@echo ""

.PHONY: help sonar-scan clean-all \
	podman-build podman-up podman-restart podman-clean \
	docker-build docker-up docker-restart docker-clean
