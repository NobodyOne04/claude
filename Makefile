MARKETPLACE := nobodyone
PLUGINS     := $(notdir $(wildcard plugins/*))
OFFICIAL    := rust-analyzer-lsp@claude-plugins-official claude-code-setup@claude-plugins-official superpowers@claude-plugins-official security-guidance@claude-plugins-official github@claude-plugins-official feature-dev@claude-plugins-official
# third-party plugins as <plugin>=<github owner/repo of its marketplace>
EXTERNAL    := ponytail=DietrichGebert/ponytail diagram-design=cathrynlavery/diagram-design

UNAME := $(shell uname -s)

.PHONY: setup plugins lsp browser doctor check

## setup: everything a fresh machine needs (plugins, language servers, browser)
setup: plugins lsp browser doctor

## plugins: add this repo as a marketplace and install every plugin in it
plugins:
	claude plugin marketplace add "$(CURDIR)"
	@for p in $(PLUGINS); do claude plugin install "$$p@$(MARKETPLACE)" || exit 1; done
	@for p in $(OFFICIAL); do claude plugin install "$$p" || exit 1; done
	@for e in $(EXTERNAL); do claude plugin install "$${e%%=*}" --marketplace "$${e#*=}" || exit 1; done

## lsp: install the language servers the dev plugin (and rust-analyzer-lsp) use
lsp:
ifeq ($(UNAME),Darwin)
	@command -v gopls >/dev/null || go install golang.org/x/tools/gopls@latest
	@command -v pyright-langserver >/dev/null || brew install pyright
	@for b in lua-language-server typescript-language-server bash-language-server yaml-language-server; do \
		command -v "$$b" >/dev/null || brew install "$$b" || exit 1; done
else
	sudo pacman -S --needed gopls pyright lua-language-server typescript-language-server bash-language-server yaml-language-server
endif
	@command -v rust-analyzer >/dev/null || rustup component add rust-analyzer

## browser: Chromium for the Playwright MCP server
browser:
	npx -y playwright install chromium

## doctor: show which servers are missing and whether MCP servers connect
doctor:
	@for b in gopls pyright-langserver lua-language-server typescript-language-server bash-language-server yaml-language-server rust-analyzer; do \
		if command -v "$$b" >/dev/null; then echo "ok       $$b"; else echo "MISSING  $$b"; fi; done
	@claude mcp list

## check: validate the marketplace and every plugin
check:
	claude plugin validate .
	@for p in plugins/*/; do claude plugin validate "$$p" || exit 1; done
