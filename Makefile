MARKETPLACE := nobodyone
# every plugin in this marketplace, ours and the pinned third-party ones
PLUGINS     := $(shell python3 -c "import json;print(' '.join(p['name'] for p in json.load(open('.claude-plugin/marketplace.json'))['plugins']))")
OFFICIAL    := rust-analyzer-lsp@claude-plugins-official claude-code-setup@claude-plugins-official superpowers@claude-plugins-official security-guidance@claude-plugins-official github@claude-plugins-official feature-dev@claude-plugins-official

UNAME := $(shell uname -s)

.PHONY: setup plugins lsp browser doctor check

## setup: everything a fresh machine needs (plugins, language servers, browser)
setup: plugins lsp browser doctor

## plugins: add this repo as a marketplace and install every plugin in it
plugins:
	claude plugin marketplace add "$(CURDIR)"
	@for p in $(PLUGINS); do claude plugin install "$$p@$(MARKETPLACE)" || exit 1; done
	@for p in $(OFFICIAL); do claude plugin install "$$p" || exit 1; done

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
# Arch's rustup package ships no toolchain (component add fails until a default is set)
# and keeps the rust-analyzer proxy in /usr/lib/rustup/bin, off PATH: link it into ~/.local/bin
	@command -v rust-analyzer >/dev/null || { \
		{ rustup show active-toolchain >/dev/null 2>&1 || rustup default stable; } && \
		rustup component add rust-analyzer && \
		{ [ ! -x /usr/lib/rustup/bin/rust-analyzer ] || \
			ln -sf /usr/lib/rustup/bin/rust-analyzer "$(HOME)/.local/bin/rust-analyzer"; }; }

## browser: Chromium for the Playwright MCP server
browser:
	npx -y playwright@1.66.0-alpha-2026-11-09 install chromium  # same playwright the pinned MCP uses

## doctor: show which servers are missing and whether MCP servers connect
doctor:
	@for b in gopls pyright-langserver lua-language-server typescript-language-server bash-language-server yaml-language-server rust-analyzer; do \
		if command -v "$$b" >/dev/null; then echo "ok       $$b"; else echo "MISSING  $$b"; fi; done
	@claude mcp list

## check: validate the marketplace and every plugin
check:
	claude plugin validate .
	@for p in plugins/*/; do claude plugin validate "$$p" || exit 1; done
	sh plugins/workflow/hooks/test-guard.sh
	python3 -I plugins/workflow/skills/plugin-audit/audit.py --test
	python3 -I plugins/workflow/hooks/marketplace-branch.py --test
	python3 -I plugins/workflow/skills/codex/codex.py --test
