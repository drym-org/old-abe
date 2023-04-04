# Installing for development

You could do this in a virtual environment or at the system / user level if you prefer. I believe it only installs the package and dependencies locally at the current path, but I don't recall for sure.

```
$ make build
```

# Running Tests

```
$ make test
```

# Linting

Linter:

```
$ make lint
```

Run black on all source and test files:

```
$ make black
```

# More development workflows

Running ``make`` shows all the available options, including running specific tests, entering a debugger on a failing test, and more.

```
$ make
```
