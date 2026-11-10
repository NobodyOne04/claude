.PHONY: check
check:
	claude plugin validate .
	@for p in plugins/*/; do claude plugin validate "$$p" || exit 1; done
