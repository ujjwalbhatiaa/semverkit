"""semverkit: parse, compare, sort and bump Semantic Versions (semver.org 2.0.0). Stdlib only."""
import argparse
import functools
import re
import sys

_SEMVER = re.compile(
    r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
    r"(?:-((?:0|[1-9]\d*|\d*[A-Za-z-][0-9A-Za-z-]*)(?:\.(?:0|[1-9]\d*|\d*[A-Za-z-][0-9A-Za-z-]*))*))?"
    r"(?:\+([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?$"
)


class Version:
    """An immutable semantic version. Build metadata is ignored when comparing."""

    __slots__ = ("major", "minor", "patch", "pre", "build")

    def __init__(self, major, minor, patch, pre=(), build=()):
        self.major, self.minor, self.patch = major, minor, patch
        self.pre, self.build = tuple(pre), tuple(build)

    @classmethod
    def parse(cls, text):
        m = _SEMVER.match(text.strip().lstrip("v"))
        if not m:
            raise ValueError("invalid semantic version: %r" % text)
        major, minor, patch, pre, build = m.groups()
        return cls(int(major), int(minor), int(patch),
                   pre.split(".") if pre else (), build.split(".") if build else ())

    def _key(self):
        # A release sorts after any prerelease of the same core version.
        if not self.pre:
            return (self.major, self.minor, self.patch, 1, ())
        ids = tuple((0, int(p), "") if p.isdigit() else (1, 0, p) for p in self.pre)
        return (self.major, self.minor, self.patch, 0, ids)

    def __eq__(self, other):
        return isinstance(other, Version) and self._key() == other._key()

    def __lt__(self, other):
        return self._key() < other._key()

    def __le__(self, other):
        return self._key() <= other._key()

    def __gt__(self, other):
        return self._key() > other._key()

    def __ge__(self, other):
        return self._key() >= other._key()

    def __hash__(self):
        return hash(self._key())

    def __str__(self):
        s = "%d.%d.%d" % (self.major, self.minor, self.patch)
        if self.pre:
            s += "-" + ".".join(self.pre)
        if self.build:
            s += "+" + ".".join(self.build)
        return s

    __repr__ = lambda self: "Version(%r)" % str(self)

    def bump(self, part):
        """Return the next version. part: major, minor, patch, or prerelease."""
        if part == "major":
            return Version(self.major + 1, 0, 0)
        if part == "minor":
            return Version(self.major, self.minor + 1, 0)
        if part == "patch":
            # Bumping a prerelease's patch just releases it.
            return Version(self.major, self.minor, self.patch if self.pre else self.patch + 1)
        if part == "prerelease":
            if not self.pre:
                return Version(self.major, self.minor, self.patch + 1, ("rc", "1"))
            pre = list(self.pre)
            if pre[-1].isdigit():
                pre[-1] = str(int(pre[-1]) + 1)
            else:
                pre.append("1")
            return Version(self.major, self.minor, self.patch, pre)
        raise ValueError("unknown part: %r" % part)


def compare(a, b):
    a, b = Version.parse(a), Version.parse(b)
    return (a > b) - (a < b)


def sort_versions(items, reverse=False):
    return sorted(items, key=Version.parse, reverse=reverse)


def satisfies(version, constraint):
    """Check a version against comma-separated constraints like '>=1.2.0,<2.0.0', '^1.2.3', '~1.2.3'."""
    v = Version.parse(version)
    for term in (t.strip() for t in constraint.split(",") if t.strip()):
        if term[0] == "^":
            base = Version.parse(term[1:])
            if base.major > 0:
                upper = Version(base.major + 1, 0, 0)
            elif base.minor > 0:
                upper = Version(0, base.minor + 1, 0)
            else:
                upper = Version(0, 0, base.patch + 1)
            ok = base <= v < upper
        elif term[0] == "~":
            base = Version.parse(term[1:])
            ok = base <= v < Version(base.major, base.minor + 1, 0)
        else:
            m = re.match(r"^(>=|<=|==|!=|>|<|=)?\s*(.+)$", term)
            op, rhs = m.group(1) or "==", Version.parse(m.group(2))
            ok = {">=": v >= rhs, "<=": v <= rhs, ">": v > rhs, "<": v < rhs,
                  "==": v == rhs, "=": v == rhs, "!=": v != rhs}[op]
        if not ok:
            return False
    return True


def main(argv=None):
    p = argparse.ArgumentParser(prog="semverkit", description=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("compare", help="print -1, 0 or 1")
    c.add_argument("a"); c.add_argument("b")
    s = sub.add_parser("sort", help="sort versions given as args or on stdin")
    s.add_argument("versions", nargs="*"); s.add_argument("-r", "--reverse", action="store_true")
    b = sub.add_parser("bump", help="bump a version")
    b.add_argument("part", choices=["major", "minor", "patch", "prerelease"]); b.add_argument("version")
    k = sub.add_parser("satisfies", help="exit 0 if version matches constraint")
    k.add_argument("version"); k.add_argument("constraint")
    a = p.parse_args(argv)
    try:
        if a.cmd == "compare":
            print(compare(a.a, a.b))
        elif a.cmd == "sort":
            items = a.versions or [l.strip() for l in sys.stdin if l.strip()]
            print("\n".join(str(Version.parse(v)) for v in sort_versions(items, a.reverse)))
        elif a.cmd == "bump":
            print(Version.parse(a.version).bump(a.part))
        else:
            return 0 if satisfies(a.version, a.constraint) else 1
    except ValueError as e:
        print("error: %s" % e, file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
