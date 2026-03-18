SUBTARGETS := $(wordlist 2,$(words $(MAKECMDGOALS)),$(MAKECMDGOALS))
ROOT_TARGETS := help service app
FORWARD_TARGETS := $(filter-out $(ROOT_TARGETS),$(SUBTARGETS))

.PHONY: help repo-help service app

ifeq (service,$(firstword $(MAKECMDGOALS)))
  ifneq ($(SUBTARGETS),)
    $(foreach arg,$(SUBTARGETS),$(eval $(arg):;@:))
  endif
endif

ifeq (app,$(firstword $(MAKECMDGOALS)))
  ifneq ($(SUBTARGETS),)
    $(foreach arg,$(SUBTARGETS),$(eval $(arg):;@:))
  endif
endif

ifneq ($(filter $(firstword $(MAKECMDGOALS)),service app),$(firstword $(MAKECMDGOALS)))
help:
	@echo "Uso: make <contexto> <target>"
	@echo ""
	@echo "Contextos disponiveis:"
	@echo "  make service <target> - encaminha para o Makefile de service"
	@echo "  make app <target>     - encaminha para o Makefile de app"
	@echo ""
	@echo "Exemplos:"
	@echo "  make service up-dev"
	@echo "  make service test"
	@echo "  make app help"
endif

repo-help: help

service:
	@$(MAKE) -C service $(SUBTARGETS)

app:
	@$(MAKE) -C app $(SUBTARGETS)
