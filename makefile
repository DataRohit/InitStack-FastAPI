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

# Execute SonarQube Code Analysis
sonar-scan:
	@echo ""
	@printf "${YELLOW}Starting SonarScanner...${NC}\n"
	sonar-scanner \
		-Dsonar.host.url=http://localhost:9000 \
		-Dsonar.projectKey=InitStack \
		-Dsonar.login=sqp_576f052d2afb2ee6832d6d42b0524b755b8f75c1
	@printf "${GREEN}SonarQube scan completed!${NC}\n"
	@echo ""

.PHONY: help sonar-scan
