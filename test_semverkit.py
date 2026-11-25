import unittest

from semverkit import Version, compare, main, satisfies, sort_versions


class TestParse(unittest.TestCase):
    def test_roundtrip(self):
        for s in ["1.2.3", "1.0.0-alpha.1", "1.0.0+build.5", "2.0.0-rc.1+sha.abc"]:
            self.assertEqual(str(Version.parse(s)), s)

    def test_leading_v(self):
        self.assertEqual(Version.parse("v1.2.3"), Version.parse("1.2.3"))

    def test_invalid(self):
        for s in ["1.2", "01.2.3", "1.2.3-", "1.2.3-01", "a.b.c", "1.2.3+"]:
            with self.assertRaises(ValueError, msg=s):
                Version.parse(s)


class TestCompare(unittest.TestCase):
    def test_spec_precedence_chain(self):
        chain = ["1.0.0-alpha", "1.0.0-alpha.1", "1.0.0-alpha.beta", "1.0.0-beta",
                 "1.0.0-beta.2", "1.0.0-beta.11", "1.0.0-rc.1", "1.0.0"]
        for lo, hi in zip(chain, chain[1:]):
            self.assertEqual(compare(lo, hi), -1, (lo, hi))
            self.assertEqual(compare(hi, lo), 1)

    def test_build_ignored(self):
        self.assertEqual(compare("1.0.0+a", "1.0.0+b"), 0)

    def test_numeric_not_lexical(self):
        self.assertEqual(compare("1.10.0", "1.9.0"), 1)

    def test_sort(self):
        self.assertEqual(sort_versions(["1.10.0", "1.2.0", "1.2.0-rc.1"]),
                         ["1.2.0-rc.1", "1.2.0", "1.10.0"])
        self.assertEqual(sort_versions(["1.0.0", "2.0.0"], reverse=True), ["2.0.0", "1.0.0"])


class TestBump(unittest.TestCase):
    def test_parts(self):
        v = Version.parse("1.2.3")
        self.assertEqual(str(v.bump("major")), "2.0.0")
        self.assertEqual(str(v.bump("minor")), "1.3.0")
        self.assertEqual(str(v.bump("patch")), "1.2.4")

    def test_prerelease(self):
        self.assertEqual(str(Version.parse("1.2.3").bump("prerelease")), "1.2.4-rc.1")
        self.assertEqual(str(Version.parse("1.2.4-rc.1").bump("prerelease")), "1.2.4-rc.2")
        self.assertEqual(str(Version.parse("1.2.4-rc.2").bump("patch")), "1.2.4")

    def test_bad_part(self):
        with self.assertRaises(ValueError):
            Version.parse("1.0.0").bump("nope")


class TestSatisfies(unittest.TestCase):
    def test_ranges(self):
        self.assertTrue(satisfies("1.5.0", ">=1.2.0,<2.0.0"))
        self.assertFalse(satisfies("2.0.0", ">=1.2.0,<2.0.0"))
        self.assertTrue(satisfies("1.2.3", "1.2.3"))
        self.assertTrue(satisfies("1.2.4", "!=1.2.3"))

    def test_caret_tilde(self):
        self.assertTrue(satisfies("1.9.9", "^1.2.3"))
        self.assertFalse(satisfies("2.0.0", "^1.2.3"))
        self.assertTrue(satisfies("0.2.9", "^0.2.3"))
        self.assertFalse(satisfies("0.3.0", "^0.2.3"))
        self.assertFalse(satisfies("0.0.4", "^0.0.3"))
        self.assertTrue(satisfies("1.2.9", "~1.2.3"))
        self.assertFalse(satisfies("1.3.0", "~1.2.3"))


class TestCli(unittest.TestCase):
    def test_exit_codes(self):
        self.assertEqual(main(["satisfies", "1.2.3", "^1.0.0"]), 0)
        self.assertEqual(main(["satisfies", "2.0.0", "^1.0.0"]), 1)
        self.assertEqual(main(["compare", "x", "1.0.0"]), 2)


if __name__ == "__main__":
    unittest.main()
