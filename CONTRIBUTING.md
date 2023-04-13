# Installing for development

You could do this in a virtual environment or at the system / user level if you prefer. I believe it only installs the package and dependencies locally at the current path, but I don't recall for sure.

```
$ make build
```

# Running Tests

```
$ make test
```

## Debugging

To debug a test execution using a step debugger, put this in the body of the test you'd like to debug:

```
import pudb; pudb.set_trace()
```

Now, when you run `make test` (for example), it will put you in the debugger, allowing you to step through the execution of the code. Here are some things you can do:

* `n` - next
* `s` - step into
* `u` - up to higher level in the call stack
* `d` - down to lower level in the call stack
* `H` - return "home" to the current step in the execution
* `c` - continue (resume execution until another breakpoint is hit)
* `C-x` - REPL to evaluate expressions to see their value (`C-x` again returns)

There's more handy stuff that you can do like setting breakpoints and visiting other modules. Press `?` to see all the options.

*Note*: the official docs for `pudb` say that we could also use `pu.db()` instead of `pudb.set_trace()`, but this doesn't seem to work.

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
