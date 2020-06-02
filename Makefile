ROOT_DIR := $(abspath $(patsubst %/,%,$(dir $(abspath $(lastword $(MAKEFILE_LIST))))))
.DEFAULT_GOAL := help

DOCKERFILE := Dockerfile
PACKAGE_PATH ?= aws_aware
PACKAGE_EXE ?= aws-aware

# Deployment configuration settings
# You can change the default deploy config like:
#  make dpl="deploy_special.env" app/config/init
dpl ?= ./config/default.env
-include $(dpl)
export $(shell sed 's/=.*//' $(dpl))

define BROWSER_PYSCRIPT
import os, webbrowser, sys
try:
	from urllib import pathname2url
except:
	from urllib.request import pathname2url
webbrowser.open("file://" + pathname2url(os.path.abspath(sys.argv[1])))
endef

export BROWSER_PYSCRIPT
BROWSER := python -c "$$BROWSER_PYSCRIPT"

.PHONY: help
help: ## Help
	@grep --no-filename -E '^[a-zA-Z_%/-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

.PHONY: clean
clean: .clean/build .clean/pyc .clean/test ## remove all build, test, coverage and Python artifacts

.PHONY: .clean/build
.clean/build: ## remove build artifacts
	rm -fr build/
	rm -fr dist/
	#rm -f $(PACKAGE_PATH)/config/config.yml
	rm -f temp_config.yml
	rm -fr $(PACKAGE_PATH)/logs/*.log
	rm -fr .eggs/
	find . \( -path ./env -o -path ./venv -o -path ./.env -o -path ./.venv \) -prune -o -name '*.egg-info' -exec rm -fr {} +
	find . \( -path ./env -o -path ./venv -o -path ./.env -o -path ./.venv \) -prune -o -name '*.egg' -exec rm -f {} +

.PHONY: .clean/pyc
.clean/pyc: ## remove Python file artifacts
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -fr {} +

.PHONY: .clean/test
.clean/test: ## remove test and coverage artifacts
	rm -fr .tox/
	rm -f .coverage
	rm -fr htmlcov/
	rm -fr .pytest_cache

.PHONY: .clean/docs
.clean/docs: ## remove generated docs
	rm -rf docs

.PHONY: lint
lint: ## check style with flake8
	flake8 $(PACKAGE_PATH) tests

.PHONY: .lint/autoflake
.lint/autoflake: ## Use autoflake to fix issues
	@echo "Autoflake: remove unused imports"
	find ./$(PACKAGE_PATH) -name '*.py'|grep -v scriptconfig.py|xargs autoflake --in-place --remove-all-unused-imports
	## @echo "Autoflake: remove unused vars"
	##	find ./$(PACKAGE_PATH) -name '*.py'|grep -v scriptconfig.py|xargs autoflake --in-place --remove-unused-variables

.PHONY: .lint/autopep8
.lint/autopep8: ## Use autopep8 to fix issues
	autopep8 --in-place --recursive --max-line-length=79 --exclude="*/scriptconfig.py/*" --select="W291,W293,E101,E121,E20,W391,E301,E265,E26,E51" ./$(PACKAGE_PATH)

.PHONY: test
test: ## run tests quickly with Python
	python setup.py test

.PHONY: .test/tox
.test/tox: ## run tests on every Python version with tox
	tox

.PHONY: coverage
coverage: ## check code coverage quickly with the default Python
	coverage run --source $(PACKAGE_PATH) setup.py test
	coverage report -m
	coverage html
	$(BROWSER) htmlcov/index.html

.PHONY: docs
docs: .clean/docs ## generate Sphinx HTML documentation, including API docs
	sphinx-apidoc -f -F -o docs/ $(PACKAGE_PATH)
	$(MAKE) -C docs html
	pandoc --from=markdown --to=rst --output=README.rst README.MD
	$(BROWSER) docs/_build/html/index.html

.PHONY: servedocs
servedocs: docs ## compile the docs watching for changes
	watchmedo shell-command -p '*.rst' -c '$(MAKE) -C docs' -R -D .

.PHONY: release
release: dist ## package and upload a release
	twine upload -r artifactorypypi dist/$(PACKAGE_PATH)*.whl

.PHONY: exe
exe: ## Create local executable
	pyinstaller --name $(PACKAGE_EXE) $(PACKAGE_PATH)/cli.py

.PHONY: dist
dist: clean ## builds source and wheel package
	python setup.py sdist
	python setup.py bdist_wheel

.PHONY: install
install: clean ## install the package to the active Python's site-packages
	pip install -e . --no-cache-dir --no-deps
	#	pipenv install -e .

.PHONY: deps
deps: ## Install pip dependencies
	pip install -r requirements.txt

.PHONY: deps/dev
deps/dev: ## Install pip dependencies for development
	pip install -r requirements-dev.txt

.PHONY: .install/from/pypi
.install/from/pypi: ## Install from artifactory
	pip install $(PACKAGE_EXE) -U --no-deps

.PHONY: .deploy/cron/task
.deploy/cron/task: .create/wrapper/script ## Installs cron job to run every 4 hours
	crontab -l > .mycron 2>/dev/null || true
	echo '0 0-23/4 * * * $(APP_AUTO_SCRIPTPATH)/$(APP_AUTO_SCRIPTNAME)' >> .mycron
	crontab .mycron
	rm -rf .mycron
	@echo 'Configured cron as user to run every 4 hours the following command:'
	@echo '  $(APP_AUTO_SCRIPTPATH)/$(APP_AUTO_SCRIPTNAME)'
	@echo 'You would be wise to review this script to ensure its what ya want!'

.PHONY: .create/wrapper/script
.create/wrapper/script: ## Creates a wrapper script for cron or whatever to use
	@rm -rf $(APP_AUTO_SCRIPTPATH)/$(APP_AUTO_SCRIPTNAME)
	echo $(APP_AUTO_SCRIPT) > $(APP_AUTO_SCRIPTPATH)/$(APP_AUTO_SCRIPTNAME)
	chmod +x $(APP_AUTO_SCRIPTPATH)/$(APP_AUTO_SCRIPTNAME)
	@echo "Created $(APP_AUTO_SCRIPTPATH)/$(APP_AUTO_SCRIPTNAME)"

.PHONY: .sso/login
.sso/login: ## Perform SSO Login using mycompany-aws-sso
	@$(MAKE) -s -C ./mycompany-aws-sso .sso/login

.PHONY: app/config/init
app/config/init: ## Creates a new app config file
	rm -rf $(APP_CONFIG_PATH)
	$(PACKAGE_EXE) config new -filename $(APP_CONFIG_PATH)
	$(PACKAGE_EXE) -configfile $(APP_CONFIG_PATH) config change emailrecipients $(EMAIL_RECIPIENTS)
	$(PACKAGE_EXE) -configfile $(APP_CONFIG_PATH) config change environment ''
	$(PACKAGE_EXE) -configfile $(APP_CONFIG_PATH) config change costcenter ''
	$(PACKAGE_EXE) -configfile $(APP_CONFIG_PATH) config change appname ''
	$(PACKAGE_EXE) -configfile $(APP_CONFIG_PATH) config change awsprofile $(AWS_PROFILE)
	#$(PACKAGE_EXE) -configfile $(APP_CONFIG_PATH) config change slack_webhooks '$(APP_SLACK_URI)'
	#$(PACKAGE_EXE) -configfile $(APP_CONFIG_PATH) config change slack_notifications $(APP_SLACK_ENABLED)
	$(PACKAGE_EXE) -configfile $(APP_CONFIG_PATH) config change monitorconfig $(MONITOR_CONFIG_PATH)
	$(PACKAGE_EXE) -configfile $(APP_CONFIG_PATH) config change datapath /tmp/instance_data.yml
	@echo ''
	@echo 'Config File Deployed: $(APP_CONFIG_PATH)'

.PHONY: app/config/smtp
app/config/smtp: ## Updates smtp config (example task)
	$(PACKAGE_EXE) -configfile $(APP_CONFIG_PATH) config change emailsmtpserver localhost
	$(PACKAGE_EXE) -configfile $(APP_CONFIG_PATH) config change emailsmtpserverport 2525

.PHONY: app/run
app/run: ## Run $(PACKAGE_EXE) and send any notifications
	$(PACKAGE_EXE) -configfile "$(APP_CONFIG_PATH)" run -sendalerts -sendwarnings -force monitors

.PHONY: app/run/export
app/run/export: ## Run $(PACKAGE_EXE) instance export for debugging
	$(PACKAGE_EXE) -configfile $(APP_CONFIG_PATH) run -sendalerts -sendwarnings -force export_data

.PHONY: app/run/report
app/run/report: ## Run $(PACKAGE_EXE) instance export for debugging
	$(PACKAGE_EXE) -configfile $(APP_CONFIG_PATH) run report -filteredinstances

.PHONY: app/show/config
app/show/config: ## Show current app configuration file
	$(PACKAGE_EXE) -configfile $(APP_CONFIG_PATH) config show

.PHONY: docker/image
docker/image: ## build docker image
	docker build -f $(DOCKERFILE) -t $(PACKAGE_EXE) .

.PHONY: docker/run
docker/run: ## Run the $(PACKAGE_EXE):latest container
	docker run -it --rm \
	-v ~/.aws:/app/.aws:ro \
	$(PACKAGE_EXE):latest

.PHONY: docker/shell
docker/shell: ## shell into $(PACKAGE_EXE):latest
	docker run -it --rm \
	-v ~/.aws:/app/.aws:ro \
	$(PACKAGE_EXE):latest \
	/bin/bash