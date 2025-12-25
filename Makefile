.PHONY: help migration-create migration-apply migration-rollback migration-history migration-current migration-heads migration-stamp migration-sql migration-merge

SHELL := /bin/bash

help:
	@echo "Alembic Migration Commands:"
	@echo ""
	@echo "  make migration-create MSG='description'  - Generate new migration with auto-detect"
	@echo "  make migration-apply                     - Apply all pending migrations"
	@echo "  make migration-rollback [STEPS=1]        - Rollback migrations (default: 1 step)"
	@echo "  make migration-history                   - Show migration history"
	@echo "  make migration-current                   - Show current database revision"
	@echo "  make migration-heads                     - Show pending migrations"
	@echo "  make migration-stamp                     - Mark database as up-to-date"
	@echo "  make migration-sql                       - Show SQL without executing"
	@echo "  make migration-merge MSG='msg' R1=rev1 R2=rev2 - Merge migration branches"
	@echo ""
	@echo "Examples:"
	@echo "  make migration-create MSG='create users table'"
	@echo "  make migration-apply"
	@echo "  make migration-rollback STEPS=2"

migration-create:
ifndef MSG
	@echo "Error: MSG is required. Usage: make migration-create MSG='description'"
	@exit 1
endif
	alembic revision --autogenerate -m "$(MSG)"

migration-apply:
	alembic upgrade head

migration-rollback:
	alembic downgrade -$(or $(STEPS),1)

migration-history:
	alembic history

migration-current:
	alembic current

migration-heads:
	alembic heads

migration-stamp:
	alembic stamp head

migration-sql:
	alembic upgrade head --sql

migration-merge:
ifndef MSG
	@echo "Error: MSG is required. Usage: make migration-merge MSG='merge msg' R1=rev1 R2=rev2"
	@exit 1
endif
ifndef R1
	@echo "Error: R1 (first revision) is required"
	@exit 1
endif
ifndef R2
	@echo "Error: R2 (second revision) is required"
	@exit 1
endif
	alembic merge -m "$(MSG)" $(R1) $(R2)
