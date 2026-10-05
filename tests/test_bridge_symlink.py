#!/usr/bin/env python3
"""Acceptance tests for bridge-symlink.sh, including the AGENTS.md opt-in path.

Run from anywhere:  python3 tests/test_bridge_symlink.py
Each fixture places a playbook copy and a repo as siblings under one parent, the layout the
bridge's relative links assume. The legacy test runs BRIDGE_BASE's bridge-symlink.sh and
requires identical links for repos that have not opted in.
"""
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from test_compose_agents_md import BEGIN, END, CORE_RULES, read, snapshot, write  # noqa: E402

PLAYBOOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# Playbook main before the bridge learned the opt-in. Pinned so the gate survives the merge.
BRIDGE_BASE = os.environ.get("BRIDGE_BASE", "d525afb")
PB_NAME = "_playbook"
ENV = dict(os.environ, PLAYBOOK_HOME="/fixture/playbook-home")
COMMANDS = ["status", "wrapup", "conform", "context-health", "inbox", "test"]
AGENTS = (b"# AGENTS.md \xe2\x80\x94 Repo\n\nIntro.\n\n" + BEGIN + b"\nstale\n" + END
          + b"\n\n## Current State\n\nState.\n")


def bridge(repo, pack="python"):
    script = os.path.join(os.path.dirname(repo), PB_NAME, "bridge-symlink.sh")
    return subprocess.run(["bash", script, repo, pack], capture_output=True, env=ENV)


class BridgeSymlinkTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="bridge-test-")
        self.body = read(os.path.join(PLAYBOOK, "core", "agents-core.md"))

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def parent(self, name, base_ref=None):
        """A parent dir holding a playbook copy (current tree, or base_ref) named _playbook."""
        parent = os.path.join(self.tmp, name)
        pb = os.path.join(parent, PB_NAME)
        if base_ref:
            os.makedirs(pb)
            archive = subprocess.run(["git", "-C", PLAYBOOK, "archive", base_ref],
                                     capture_output=True, check=True)
            subprocess.run(["tar", "-x", "-C", pb], input=archive.stdout, check=True)
        else:
            shutil.copytree(PLAYBOOK, pb, ignore=shutil.ignore_patterns(".git", "tests", "PlaybookLauncher"))
        return parent

    def repo(self, parent, opted_in=False):
        root = os.path.join(parent, "repo")
        write(os.path.join(root, "README.md"), b"repo\n")
        write(os.path.join(root, ".claude", "settings.local.json"), b"{}\n")
        if opted_in:
            write(os.path.join(root, "AGENTS.md"), AGENTS)
            os.symlink("AGENTS.md", os.path.join(root, "CLAUDE.md"))
        return root

    def opt_in(self, root):
        write(os.path.join(root, "AGENTS.md"), AGENTS)
        os.symlink("AGENTS.md", os.path.join(root, "CLAUDE.md"))

    def block(self, root):
        a = read(os.path.join(root, "AGENTS.md"))
        return a[a.index(BEGIN) + len(BEGIN) + 1:a.index(END)]

    # --- legacy -------------------------------------------------------------------
    def test_legacy_links_identical_to_base(self):
        a = self.repo(self.parent("base", base_ref=BRIDGE_BASE))
        b = self.repo(self.parent("new"))
        self.assertEqual(bridge(a).returncode, 0)
        r = bridge(b)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(snapshot(a), snapshot(b))
        self.assertIn(b"6 core rules", r.stdout)

    # --- opted-in -----------------------------------------------------------------
    def test_opt_in_replaces_known_core_links_with_block(self):
        root = self.repo(self.parent("opt"))
        self.assertEqual(bridge(root).returncode, 0)            # legacy bridge first
        self.opt_in(root)
        r = bridge(root)
        self.assertEqual(r.returncode, 0, r.stderr)
        for rule in CORE_RULES:
            self.assertFalse(os.path.lexists(os.path.join(root, ".claude", "rules", rule)), rule)
        for cmd in COMMANDS:
            self.assertTrue(os.path.islink(os.path.join(root, ".claude", "commands", cmd + ".md")), cmd)
        self.assertTrue(os.path.islink(os.path.join(root, ".claude", "command-profile.md")))
        self.assertEqual(self.block(root), self.body)
        self.assertEqual(os.readlink(os.path.join(root, "CLAUDE.md")), "AGENTS.md")
        self.assertEqual(read(os.path.join(root, ".claude", "settings.local.json")), b"{}\n")
        self.assertIn(b"6 core-rule links removed", r.stdout)

    def test_opt_in_rerun_is_idempotent(self):
        root = self.repo(self.parent("idem"), opted_in=True)
        self.assertEqual(bridge(root).returncode, 0)
        first = snapshot(root)
        r = bridge(root)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(snapshot(root), first)

    def test_rerun_refreshes_block_after_source_change(self):
        parent = self.parent("refresh")
        root = self.repo(parent, opted_in=True)
        self.assertEqual(bridge(root).returncode, 0)
        changed = self.body + b"\nA new shared line.\n"
        write(os.path.join(parent, PB_NAME, "core", "agents-core.md"), changed)
        self.assertEqual(bridge(root).returncode, 0)
        self.assertEqual(self.block(root), changed)

    def test_opt_in_keeps_real_core_rule_file_and_warns(self):
        root = self.repo(self.parent("realfile"), opted_in=True)
        write(os.path.join(root, ".claude", "rules", "git-workflow.md"), b"custom\n")
        r = bridge(root)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(read(os.path.join(root, ".claude", "rules", "git-workflow.md")), b"custom\n")
        self.assertIn(b"keeping", r.stderr)

    def test_opt_in_keeps_foreign_symlink_and_warns(self):
        root = self.repo(self.parent("foreign"), opted_in=True)
        write(os.path.join(root, "shared", "rule.md"), b"x\n")
        os.makedirs(os.path.join(root, ".claude", "rules"), exist_ok=True)
        os.symlink("../../shared/rule.md", os.path.join(root, ".claude", "rules", "session-health.md"))
        r = bridge(root)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(os.readlink(os.path.join(root, ".claude", "rules", "session-health.md")),
                         "../../shared/rule.md")
        self.assertIn(b"keeping", r.stderr)

    def test_invalid_opt_in_layout_changes_nothing(self):
        root = self.repo(self.parent("invalid"))
        self.assertEqual(bridge(root).returncode, 0)            # legacy links exist
        write(os.path.join(root, "AGENTS.md"), AGENTS)
        write(os.path.join(root, "CLAUDE.md"), b"@AGENTS.md\n")  # not the required symlink
        before = snapshot(root)
        r = bridge(root)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn(b"Nothing was written", r.stderr)
        self.assertEqual(snapshot(root), before)

    def test_post_write_failure_reports_possible_partial_changes(self):
        root = self.repo(self.parent("readonly"), opted_in=True)
        os.makedirs(os.path.join(root, ".claude", "rules"), exist_ok=True)
        os.chmod(root, stat.S_IRUSR | stat.S_IXUSR)  # .claude/ stays writable; AGENTS.md can't be replaced
        try:
            r = bridge(root)
        finally:
            os.chmod(root, stat.S_IRWXU)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn(b"may be partially updated", r.stderr)
        self.assertEqual(read(os.path.join(root, "AGENTS.md")), AGENTS)


if __name__ == "__main__":
    unittest.main(verbosity=2)
