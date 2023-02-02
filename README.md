[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/sqrl-planner/gator-core/main.svg)](https://results.pre-commit.ci/latest/github/sqrl-planner/gator-core/main)

# gator-core
 A dataset aggregation framework for Sqrl Planner.

## Tools

#### Linting the codebase
For detecting code quality and style issues, run
```
flake8
```
For checking compliance with Python docstring conventions, run
```
pydocstyle
```

**NOTE**: these tools will not fix any issues, but they can help you identify potential problems.


#### Formatting the codebase
For automatically formatting the codebase, run
```
autopep8 --in-place --recursive .
```
For more information on this command, see the [autopep8](https://pypi.python.org/pypi/autopep8) documentation.

For automatically sorting imports, run
```
isort .
```
