# Security Policy

## Scope

- the static viewer deployed at https://aliakseych.github.io/3d-landmarks/;
- the GitHub Actions workflows in `.github/workflows/`;
- the local pipeline scripts in `.omp/skills/`.

The project has no backend, accounts or user data.

Privacy issues are in scope too. Examples: a committed file that leaks location, device or personal metadata (EXIF GPS in a photo), or a raw capture that was pushed by mistake.

## Reporting

Use GitHub's private reporting: **Security → Report a vulnerability** on this repository. Do not open a public issue for security or privacy problems.

You can expect an acknowledgement within 7 days. Fixes are made on `main`; the site is redeployed from the latest commit, so there are no versioned releases to patch.
