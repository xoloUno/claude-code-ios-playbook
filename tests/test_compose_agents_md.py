#!/usr/bin/env python3
"""Acceptance tests for the AGENTS.md core-block generator (compose-claude.sh opt-in path).

Run from anywhere:  python3 tests/test_compose_agents_md.py
Builds throwaway fixtures, runs the real compose-claude.sh, and compares bytes.
The legacy test composes with BASE_REF's compose-claude.sh (default: main) and requires
byte-identical output for projects that have not opted in.
"""
import hashlib
import os
import shutil
import subprocess
import tempfile
import unittest

PLAYBOOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE_REF = os.environ.get("BASE_REF", "main")
BEGIN = b"<!-- playbook:core:begin -->"
END = b"<!-- playbook:core:end -->"
CORE_RULES = ["assertion-discipline.md", "git-workflow.md", "manual-tasks.md",
              "playbook-inbox.md", "session-health.md", "work-log.md"]
ENV = dict(os.environ, PLAYBOOK_HOME="/fixture/playbook-home")
# Composed files this branch changes on purpose for unmarked (legacy) projects too: the
# instructions-file wording, the R3 attribution fix, and the one-sentence ASC addition.
# The legacy test fails on any change outside this set, and passes trivially once merged.
INTENDED_LEGACY_CHANGES = {
    os.path.join(".claude", "commands", n) for n in (
        "wrapup.md", "status.md", "inbox.md", "upgrade.md", "conform.md",
        "deploy.md", "feature.md", "release.md", "review.md")
} | {os.path.join(".claude", "command-profile.md"),
     os.path.join(".claude", "rules", "asc-troubleshooting.md")}

PREFIX = b"# AGENTS.md \xe2\x80\x94 Fixture\n\nProject intro line.\n\n" + BEGIN + b"\n"
SUFFIX = END + b"\n\n## Current State\n\nFixture state.\n"
OPTED_IN = PREFIX + b"stale block text\n" + SUFFIX


def compose(target, playbook=PLAYBOOK):
    return subprocess.run(["bash", os.path.join(playbook, "compose-claude.sh"), target, "ios"],
                          capture_output=True, env=ENV)


def snapshot(root):
    out = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames.sort()
        for name in sorted(filenames + [d for d in dirnames if os.path.islink(os.path.join(dirpath, d))]):
            p = os.path.join(dirpath, name)
            rel = os.path.relpath(p, root)
            if os.path.islink(p):
                out.append(("L", rel, os.readlink(p)))
            else:
                with open(p, "rb") as f:
                    out.append(("F", rel, hashlib.sha256(f.read()).hexdigest()))
    return out


def read(path):
    with open(path, "rb") as f:
        return f.read()


def write(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(data)


class ComposeAgentsMdTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="agents-md-test-")
        self.body = read(os.path.join(PLAYBOOK, "core", "agents-core.md"))

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def project(self, name, agents=OPTED_IN, claude=b"@AGENTS.md\n"):
        root = os.path.join(self.tmp, name)
        write(os.path.join(root, "README.md"), b"fixture\n")
        write(os.path.join(root, ".claude", "rules", "project-owned.md"), b"project rule\n")
        if agents is not None:
            write(os.path.join(root, "AGENTS.md"), agents)
        if claude is not None:
            write(os.path.join(root, "CLAUDE.md"), claude)
        return root

    def playbook_copy(self, name):
        dst = os.path.join(self.tmp, name)
        shutil.copytree(PLAYBOOK, dst, ignore=shutil.ignore_patterns(".git", "tests", "PlaybookLauncher"))
        return dst

    # --- legacy -------------------------------------------------------------------
    def test_legacy_output_matches_base_except_intended(self):
        base = os.path.join(self.tmp, "base-playbook")
        os.makedirs(base)
        archive = subprocess.run(["git", "-C", PLAYBOOK, "archive", BASE_REF], capture_output=True, check=True)
        subprocess.run(["tar", "-x", "-C", base], input=archive.stdout, check=True)
        a = self.project("legacy-a", agents=None, claude=b"# Project\n")
        b = self.project("legacy-b", agents=None, claude=b"# Project\n")
        self.assertEqual(compose(a, base).returncode, 0)
        r = compose(b)
        self.assertEqual(r.returncode, 0, r.stderr)
        sa = {(k, p): h for k, p, h in snapshot(a)}
        sb = {(k, p): h for k, p, h in snapshot(b)}
        self.assertEqual(set(sa), set(sb), "legacy compose must emit the same file set")
        changed = {p for (k, p) in sa if sa[(k, p)] != sb[(k, p)]}
        unintended = changed - INTENDED_LEGACY_CHANGES
        self.assertFalse(unintended, f"unintended legacy output changes: {sorted(unintended)}")

    def test_unmarked_agents_md_stays_legacy(self):
        agents = b"# AGENTS.md\n\nNo markers here.\n"
        p = self.project("unmarked", agents=agents, claude=b"@AGENTS.md\n")
        r = compose(p)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(read(os.path.join(p, "AGENTS.md")), agents)
        for rule in CORE_RULES:
            self.assertTrue(os.path.exists(os.path.join(p, ".claude", "rules", rule)), rule)

    # --- opted-in ------------------------------------------------------------------
    def test_opted_in_renders_block_and_skips_core_rules(self):
        p = self.project("opted")
        r = compose(p)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(read(os.path.join(p, "AGENTS.md")), PREFIX + self.body + SUFFIX)
        self.assertEqual(read(os.path.join(p, "AGENTS.md")).count(BEGIN), 1)
        for rule in CORE_RULES:
            self.assertFalse(os.path.exists(os.path.join(p, ".claude", "rules", rule)), rule)
        self.assertTrue(os.path.exists(os.path.join(p, ".claude", "rules", "code-style.md")))
        self.assertEqual(read(os.path.join(p, ".claude", "rules", "project-owned.md")), b"project rule\n")
        self.assertEqual(read(os.path.join(p, "CLAUDE.md")), b"@AGENTS.md\n")

    def test_repeat_run_is_idempotent(self):
        p = self.project("idem")
        self.assertEqual(compose(p).returncode, 0)
        first = snapshot(p)
        r = compose(p)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn(b"already current", r.stdout)
        self.assertEqual(snapshot(p), first)

    def test_source_change_touches_only_marked_region(self):
        p = self.project("region")
        self.assertEqual(compose(p).returncode, 0)
        pb2 = self.playbook_copy("pb-changed")
        changed = self.body + b"\nAn added source line.\n"
        write(os.path.join(pb2, "core", "agents-core.md"), changed)
        r = compose(p, pb2)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(read(os.path.join(p, "AGENTS.md")), PREFIX + changed + SUFFIX)

    def test_crlf_outside_bytes_preserved_and_block_uses_crlf(self):
        crlf = OPTED_IN.replace(b"\n", b"\r\n")
        p = self.project("crlf", agents=crlf)
        r = compose(p)
        self.assertEqual(r.returncode, 0, r.stderr)
        expected_block = b"".join(l.rstrip(b"\r\n") + b"\r\n" for l in self.body.splitlines(True))
        self.assertEqual(read(os.path.join(p, "AGENTS.md")),
                         PREFIX.replace(b"\n", b"\r\n") + expected_block + SUFFIX.replace(b"\n", b"\r\n"))

    def test_missing_final_newline_after_end_is_preserved(self):
        p = self.project("no-eol", agents=PREFIX + b"x\n" + END)
        r = compose(p)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(read(os.path.join(p, "AGENTS.md")), PREFIX + self.body + END)

    # --- failures leave the whole tree unchanged ------------------------------------
    def assert_rejected(self, p, playbook=PLAYBOOK, msg=None):
        before = snapshot(p)
        r = compose(p, playbook)
        self.assertNotEqual(r.returncode, 0, f"expected failure; stdout={r.stdout!r}")
        self.assertIn(b"Nothing was written", r.stderr)
        if msg:
            self.assertIn(msg.encode(), r.stderr)
        self.assertEqual(snapshot(p), before)

    def test_reject_reversed_markers(self):
        self.assert_rejected(self.project("rev", agents=END + b"\nx\n" + BEGIN + b"\n"), msg="reversed")

    def test_reject_duplicate_begin(self):
        self.assert_rejected(self.project("dup", agents=BEGIN + b"\n" + OPTED_IN), msg="exactly one")

    def test_reject_missing_end(self):
        self.assert_rejected(self.project("noend", agents=PREFIX + b"x\n"), msg="exactly one")

    def test_reject_inline_marker_text(self):
        agents = OPTED_IN + b"See " + BEGIN + b" for details.\n"
        self.assert_rejected(self.project("inline", agents=agents), msg="not exactly a delimiter")

    def test_reject_wrapper_with_extra_content(self):
        self.assert_rejected(self.project("wrap-extra", claude=b"@AGENTS.md\n\nMore.\n"), msg="exactly '@AGENTS.md'")

    def test_reject_wrapper_without_final_newline(self):
        self.assert_rejected(self.project("wrap-noeol", claude=b"@AGENTS.md"), msg="exactly '@AGENTS.md'")

    def test_reject_missing_wrapper(self):
        self.assert_rejected(self.project("wrap-missing", claude=None), msg="CLAUDE.md is missing")

    def test_reject_symlinked_agents_md(self):
        p = self.project("sym-agents", agents=None)
        write(os.path.join(p, "real-agents.md"), OPTED_IN)
        os.symlink("real-agents.md", os.path.join(p, "AGENTS.md"))
        self.assert_rejected(p, msg="symlink")

    def test_reject_symlinked_claude_md(self):
        p = self.project("sym-claude", claude=None)
        os.symlink("AGENTS.md", os.path.join(p, "CLAUDE.md"))
        self.assert_rejected(p, msg="symlink")

    def test_reject_second_instruction_body(self):
        p = self.project("dot-claude")
        write(os.path.join(p, ".claude", "CLAUDE.md"), b"extra\n")
        self.assert_rejected(p, msg=".claude/CLAUDE.md")

    def test_reject_source_containing_marker(self):
        pb = self.playbook_copy("pb-bad-source")
        write(os.path.join(pb, "core", "agents-core.md"), self.body + BEGIN + b"\n")
        self.assert_rejected(self.project("bad-source"), playbook=pb, msg="must not contain marker")

    def test_reject_empty_source(self):
        pb = self.playbook_copy("pb-empty-source")
        write(os.path.join(pb, "core", "agents-core.md"), b"\n")
        self.assert_rejected(self.project("empty-source"), playbook=pb, msg="empty")


if __name__ == "__main__":
    unittest.main(verbosity=2)
