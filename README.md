# semverkit

Parse, compare, sort, bump and range-check [Semantic Versions 2.0.0](https://semver.org). One file, Python standard library only.

## Use as a library

```python
from semverkit import Version, compare, sort_versions, satisfies

Version.parse("1.2.3-rc.1") < Version.parse("1.2.3")      # True
sort_versions(["1.10.0", "1.2.0", "1.2.0-rc.1"])          # ['1.2.0-rc.1', '1.2.0', '1.10.0']
Version.parse("1.2.3").bump("minor")                      # 1.3.0
satisfies("1.5.0", ">=1.2.0,<2.0.0")                      # True
satisfies("1.9.9", "^1.2.3")                              # True
```

## Use as a CLI

```
python semverkit.py compare 1.0.0-beta.2 1.0.0-beta.11    # -1
python semverkit.py sort 1.10.0 1.2.0 1.2.0-rc.1
python semverkit.py bump patch 1.2.3                      # 1.2.4
python semverkit.py satisfies 1.5.0 ">=1.2.0,<2.0.0"      # exit 0 if it matches, 1 if not
```

Invalid input exits with code 2.

## Details

- Precedence follows the spec: numeric identifiers compare as numbers, alphanumeric ones lexically, and a release outranks its prereleases. Build metadata is ignored.
- Constraints: `>= <= > < == != =`, `^` (caret) and `~` (tilde), joined by commas.
- A leading `v` is accepted when parsing.

## Tests

```
python -m unittest -v
```

## License

MIT
