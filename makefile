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
	@echo "  docker-build      - Build And Start All Docker Containers"
	@echo "  docker-up         - Start All Containers And Nginx-Service"
	@echo "  docker-restart    - Restart All Containers And Nginx-Service"
	@echo ""
	@printf "${GREEN}Cleaning:${NC}\n"
	@echo "  clean-all      - Remove Python-related garbage files"
	@echo ""

# Execute SonarQube Code Analysis
sonar-scan:
	@echo ""
	@printf "${YELLOW}Starting Sonarscanner...${NC}\n"
	sonar-scanner \
		-Dsonar.host.url=http://localhost:9000 \
		-Dsonar.projectKey=InitStack \
		-Dsonar.login=sqp_3ec9155b26578025ba805b2107edbcdafadc6976
	@printf "${GREEN}SonarQube Scan Completed!${NC}\n"
	@echo ""

# Docker Commands
docker-build:
	@echo ""
	@printf "${YELLOW}Building And Starting Docker Containers...${NC}\n"
	docker compose build && docker compose up -d --remove-orphans
	@printf "${GREEN}Docker Containers Started Successfully!${NC}\n"
	@echo ""

docker-up:
	@echo ""
	@printf "${YELLOW}Starting Docker Containers...${NC}\n"
	docker compose up -d --remove-orphans
	@printf "${GREEN}Docker Containers Started Successfully!${NC}\n"
	@echo ""

docker-restart:
	@echo ""
	@printf "${YELLOW}Restarting Docker Containers...${NC}\n"
	docker compose restart && docker compose restart nginx-service
	@printf "${GREEN}Docker Containers Restarted Successfully!${NC}\n"
	@echo ""


# Clean All Python Related Files
clean-all:
	@echo ""
	@printf "${YELLOW}Cleaning all Python-related files...${NC}\n"
	rm -rf .pytest_cache/ .coverage .scannerwork/ __pycache__/ build/ dist/ *.egg-info/ *.pyc *.pyo
	@printf "${GREEN}Python files cleaned successfully!${NC}\n"
	@echo ""

.PHONY: help sonar-scan docker-build docker-up docker-restart clean-all
