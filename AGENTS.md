# Repository Agent Instructions

- Communicate in Chinese when working in this repository.
- Keep files UTF-8 encoded without BOM.
- Do not leak secrets, tokens, credentials, or internal-only links.
- Avoid destructive commands unless the user explicitly requests them.

## Release And Docker Build

- The Docker release workflow is triggered only by pushing a version tag matching `v*.*.*`.
- Every repository push that is intended to trigger a build must include a version bump and matching tag.
- Increment the patch version from the current version by default. Example: `0.2.13` -> `0.2.14`.
- Keep these version declarations in sync:
  - `pyproject.toml` project `version`
  - `module/__init__.py` `__version__`
- After committing the version bump, create and push the matching annotated tag:

```bash
git tag -a vX.Y.Z -m "Release X.Y.Z"
git push origin main
git push origin vX.Y.Z
```

- If `main` was already pushed but the Docker build did not start, check whether the matching tag was pushed. Push the missing tag instead of making an empty commit.
- Before finalizing a release-triggering change, report the commit hash and tag name to the user.

## Testing

- For code changes, run the focused relevant tests first, then broader tests when the blast radius is shared behavior.
- For a version-only bump, a lightweight syntax check is enough unless code also changed.
