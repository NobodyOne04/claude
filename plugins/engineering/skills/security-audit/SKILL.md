---
name: security-audit
description: On-demand security audit of a project (application code, dependencies, infrastructure, CI/CD, data) that keeps a versioned Security Report as the baseline. Use ONLY when I explicitly ask, e.g. "run a security audit", "check project security", "audit dependencies", "review API security", "verify previous security findings", or to fix findings from that report. Never run it on your own; you may suggest it after security-relevant changes.
---

# Security audit

A user-controlled tool. It never runs automatically: not during normal development, code
review, builds or deploys.

## Suggesting an audit
After relevant changes (new dependencies, auth/authz, new endpoints or integrations, secrets
handling, infrastructure or deploy config, permissions or privileges) you may suggest one in
a line. A suggestion is not authorization: wait for my yes. Don't nag.

## Hard limits
- Only this project's assets. Prefer static analysis and safe local testing.
- No destructive tests on production, no denial-of-service, no changes to production
  infrastructure, no testing external systems without my explicit authorization.
- DAST, active API testing or pentesting only when I ask and the target and allowed
  techniques are confirmed first.
- Never extract real user data. Never write secrets, tokens, passwords or personal data
  into the report, logs or chat: name the location, redact the value.

## The Security Report
- Default `docs/security/SECURITY_REPORT.md`, unless the project already keeps security docs
  elsewhere. Record its path in the project's `CLAUDE.md` so later sessions find it.
- It is versioned: commit it the repo's usual way (a branch and PR, see `github-flow`).
- Never overwrite it with only the latest results. Update in place, keep history.
- If `CLAUDE.md` points to a report that's missing, find out why before assuming no past
  audits.
- Structure:
  ```markdown
  # Security Report
  ## Latest audit        <date, scope, overall assessment, methodology and tools, limitations>
  ## Findings           <one block per finding, current state>
  ## Audit history      <one entry per audit: date, scope, new/resolved/reopened ids>
  ```
- Finding block: ID (`SEC-001`, stable, never reused) · title · severity · confidence ·
  status · first detected · last verified · component · evidence and location · attack
  scenario · impact · remediation · references (CWE, CVE, OWASP).
- Statuses: `Open`, `In Progress`, `Resolved` (fix verified), `Accepted Risk` (only when I
  explicitly accept it; never set it yourself), `False Positive` (verified), `Reopened`.
  Resolved findings stay in the report.

## Workflow
1. **Prepare**: read the Security Report and previous findings; map the project (languages,
   frameworks, services, infra, docs, config); what changed since the last audit
   (`git log` since its date); the scope I asked for. Don't trust old results unverified.
2. **Attack surface**: public/internal APIs, auth boundaries, external integrations, data
   stores, brokers and workers, exposed network services, file/process execution,
   dependencies and build, CI/CD and deploy, secrets and sensitive data. Only what exists.
3. **Select checks** by technology, deployment model, scope, past findings and recent changes.
   Focused request → targeted checks; full audit → broad coverage. Categories:
   - **Application**: injection, authn/authz, broken access control, input validation,
     XSS/SSRF/path traversal, insecure deserialization, race conditions, crypto misuse,
     information disclosure.
   - **Dependencies**: known CVEs (direct and transitive), unmaintained packages, untrusted
     sources, dependency confusion, lockfile integrity, needless dependencies.
   - **Infrastructure**: Linux permissions and privileges, containers, Kubernetes, network
     exposure, TLS, database access, service-to-service auth, infra secrets, isolation.
   - **CI/CD and supply chain**: workflow permissions, exposed credentials, unpinned or unsafe
     third-party actions, untrusted PR execution, artifact and image integrity, deploy creds.
   - **Data**: sensitive storage, encryption at rest/in transit, password hashing, key
     management, PII exposure, sensitive logging, backups, retention and deletion.
   No findings for technology the project doesn't use.
4. **Run** what's available: SAST (e.g. `semgrep`), SCA (`osv-scanner`, `npm audit`,
   `pip-audit`, `govulncheck`, `cargo audit`), secret scanning (`gitleaks`), container/IaC
   scanning (`trivy`), language analyzers, and manual code reading. Check a tool exists before
   relying on it; record the ones that couldn't run. Don't install tools without asking.
   Every audit also gets Codex's independent read-only audit of the same scope (`codex`
   skill); its findings go through step 5 like any other. Put the Hard limits above and the
   techniques I authorized in its prompt. Keep secret files (`.env*`, keys, credential
   stores, data dumps) and raw scanner output out of its scope, and tell it to name the
   location of a secret, never print the value: whatever it reads lands in its own logs
   and goes to OpenAI.
5. **Validate** every finding: read the code or config, exploitable vs theoretical,
   prerequisites, false positives, duplicates of existing findings; record confidence and
   evidence. Scanner output alone is not a confirmed vulnerability.
6. **Report**: mark confirmed Codex findings `found by: Codex`, list its dismissed ones with
   the reason; classify each finding as new, recurring, resolved, reopened or unchanged;
   update the Security Report; present prioritized findings to me.

References: OWASP Top 10 and ASVS, CWE, CVE/CVSS, NIST, OSV and vendor advisories,
language-specific guidance, chosen by project type.

## Severity
- **Critical**: RCE, major credential compromise, significant data exposure.
- **High**: serious weakness, meaningful exploitation potential.
- **Medium**: exploitable with limited impact or extra prerequisites.
- **Low**: little practical impact.
- **Informational**: hardening advice, no confirmed vulnerability.
Weigh real exploitability, exposure, prerequisites and business impact; CVSS when useful.

## Remediation: a separate step
Explain fixes and their side effects, group related ones, and get my approval before
changing anything. Fixes needing architectural change go through `architecture-review`.
After a fix, verify it, then set `Resolved` with the verification date. Statuses change only
on evidence.

## Output
Full audit: executive summary, scope, overall assessment, methodology and tools, new
findings, known findings with current status, resolved and reopened, prioritized
remediation, limitations and unverified areas, report path.
Focused audit: only the relevant findings, and the report updated.
Never claim the project is fully secure.
