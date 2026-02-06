# Digital Aqua Development Environment Utilities (DADevEnv)

This repo contains common utilities for working with development environments.
It aims to reduce the amount of boilerplate in repos.

## Tools

### Environment Manager `env.sh`

This script manages the environment for a project, principally via `micromamba`.

For convenience, you can symlink this script and its common dependency to your project's root directory, e.g.:
```bash
ln -s ../External/DADevEnv/Scripts/common.sh Scripts/common.sh
ln -s External/DADevEnv/Scripts/env.sh env.sh
```

Prepend the script to commands to run them in the environment, e.g.:
```bash
./env.sh python --version
```

For more advanced usage, run
```bash
./env.sh --help
```
