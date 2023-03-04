# Install for Development

```
make build
```

# Running Tests

Refer to the Makefile for all things related to the development workflow. E.g.

```
make test
```

# Drafting a Release

```
# increment the version
bump2version [major|minor|patch]
# push new release tag upstream
git push --follow-tags
```
