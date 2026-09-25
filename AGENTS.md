# Agent Guidelines

These instructions apply to the entire repository.

## Branches and Scope

- Never edit files or commit on `main` or `dev`, including documentation changes.
  Read-only inspection is fine.
- `dev` is the default integration branch. Start focused branches from updated
  `dev` and target their PRs to `dev`. Release through a `dev` to `main` PR;
  `main` is the production branch.
- Before editing, check the current branch and working tree. Create or switch
  to an appropriate branch; do not repurpose a branch for an unrelated task.
- Use descriptive branch names such as `feat/42-blog-tag-filtering`,
  `fix/login-redirect`, or `docs/agent-guidelines`.
- Keep each branch and PR focused on one issue or cohesive change. Reference
  the issue when one exists, and suggest unrelated improvements separately.
- Release PRs from `dev` to `main` may collect multiple reviewed changes;
  summarize the included changes and deployment considerations.

## Branch Synchronization

- Fetch `origin` at the start of each session, before resuming work on a branch,
  and before pushing. Check the working tree and compare the branch with its
  remote counterpart before making changes.
- Fast-forward local branches to their remote counterparts where possible,
  including updating local `dev` from `origin/dev` before creating a branch.
  Preserve local changes and commits; if histories diverge, stop and ask how
  to reconcile them rather than resetting, rebasing, or force-pushing.
- Commit task-related feature-branch changes at meaningful checkpoints and
  before handoff, then push to `origin` so work can be resumed from another
  machine. Set upstream tracking on the first push and use non-force pushes.
  Keep commits focused and follow the verification and safety rules below.
- Before handoff, verify the branch is synchronized with its upstream and
  report any uncommitted or unpushed work. If fetching or pushing fails, report
  the blocker; never imply local-only work is available on another machine.

## Simplicity and Maintainability

- Optimize for code a human can understand, debug, and maintain without AI.
- Prefer the smallest clear solution that fully addresses the task. Do not
  sacrifice readability just to reduce line count.
- Follow existing conventions by default. If a simpler approach would improve
  maintainability, explain the tradeoff and propose broader changes before
  implementing them.
- Avoid speculative abstractions, unnecessary dependencies, configuration
  layers, and backward compatibility without a concrete requirement.
- Preserve the existing Flask structure and declared Python compatibility
  unless changing them is part of the approved task.
- Document non-obvious decisions and constraints, not what the code already
  says. Update relevant documentation when behavior or setup changes.

## Atomic Commits

- Each commit should express one cohesive idea and be easy to review.
- Implementation, tests, and documentation may be separate commits when that
  makes the changes clearer. They do not need to be bundled into one commit.
- The PR as a whole must include the implementation, tests, and documentation
  appropriate to the change.
- Do not mix unrelated changes in a commit or include unrelated work in a PR.
- Prefer commits that leave the project buildable and existing tests passing.
  The completed PR must pass all required checks.
- Review the staged diff before committing and stage only intended changes.
- Use concise commit messages that explain the purpose of the change and
  follow the repository's existing style.

## Verification

- Add or update tests for behavior changes and bug fixes.
- Use `uv` for local setup and verification, with the Python version declared
  in `pyproject.toml`. Run
  `uv run --locked --extra dev pytest --cov-report=xml` to install the required
  dependencies and execute the test suite in the project environment.
- Do not update dependencies or regenerate `uv.lock` merely to run tests.
  Report setup or lockfile problems rather than silently changing them.
- For UI changes, check desktop and mobile behavior when possible and
  preserve the site's established visual language.
- For documentation-only changes, check accuracy and the diff; application
  tests are not required locally unless the changes affect executable examples
  or setup. Documentation-only PRs must still pass required GitHub checks.
- Report what was verified and the actual results. If checks fail or cannot
  run, explain why; never imply they passed.
- All PRs must pass required GitHub checks. Never bypass or weaken branch
  protection to merge a change.

## Safety and Authorization

- Preserve existing user changes. Never discard, overwrite, or stage unrelated
  work. Ask before proceeding if it directly conflicts with the task.
- Standing authorization covers routine commits and non-force pushes of
  task-related changes on focused feature branches (including `fix/` and
  `docs/` branches), plus fetching and fast-forwarding local tracking branches.
- Require explicit authorization for other commits and pushes, PR creation,
  non-fast-forward merges, deployments, history rewriting, and destructive Git
  operations. Merging PRs always requires explicit authorization.
- Never commit secrets, credentials, sensitive instance configuration, or
  database dumps. Do not expose secrets in logs or responses.
- Do not access or modify the VPS or production database without explicit
  authorization.
- Merging into `main` triggers production deployment. Obtain explicit
  release/deployment authorization before merging.
- Do not weaken authentication or other security controls to simplify
  development or testing.

## Pull Requests and AI Disclosure

- Every AI-assisted PR must have the GitHub label `ai-assisted`, including PRs
  with AI-assisted documentation or tests.
- Include a brief AI disclosure in the PR description explaining what AI
  helped with and how the changes were verified.
- If the label is unavailable or cannot be applied, explicitly report that
  limitation so it can be resolved; do not silently omit it.
- PR descriptions should reference the issue when applicable, summarize the
  change, list verification results, and disclose known limitations or
  deployment considerations.
