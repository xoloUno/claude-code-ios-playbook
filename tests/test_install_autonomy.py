#!/usr/bin/env python3
"""Tests for tools/install-autonomy.py, settings/autonomy.json and tools/codex-review.sh.
Run from anywhere:  python3 tests/test_install_autonomy.py
Everything runs against a throwaway HOME; the Codex wrapper runs against a stub CLI.
"""
import json
import os
import shutil
import stat
import subprocess
import tempfile
import unittest

PLAYBOOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INSTALL = os.path.join(PLAYBOOK, "tools", "install-autonomy.py")
TEMPLATE = os.path.join(PLAYBOOK, "settings", "autonomy.json")
WRAPPER = os.path.join(PLAYBOOK, "tools", "codex-review.sh")


class InstallTest(unittest.TestCase):
    def setUp(self):
        self.home = tempfile.mkdtemp(prefix="install-autonomy-test-")

    def tearDown(self):
        shutil.rmtree(self.home)

    def path(self, *parts):
        return os.path.join(self.home, *parts)

    def install(self, *args):
        env = dict(os.environ, HOME=self.home)
        r = subprocess.run(["python3", "-I", INSTALL, *args], env=env, capture_output=True,
                           text=True, input="")
        self.assertEqual(r.returncode, 0, r.stderr)
        return r.stdout

    def read(self, *parts):
        with open(self.path(*parts)) as f:
            return f.read()

    def test_template_is_generic_and_points_at_the_installed_guard(self):
        with open(TEMPLATE) as f:
            text = f.read()
        settings = json.loads(text)
        self.assertNotIn("/Users/", text)
        hook = settings["hooks"]["PreToolUse"][0]["hooks"][0]["command"]
        self.assertIn("/.config/playbook/tools/autonomy-guard.py", hook)
        self.assertFalse(settings["sandbox"]["allowUnsandboxedCommands"])
        # Only commands the sandbox breaks (keychain, CoreSimulator) or that sandbox themselves.
        self.assertEqual(settings["sandbox"]["excludedCommands"], [
            "~/.config/playbook/tools/codex-review.sh *", "git push *", "git fetch *",
            "git pull *", "git clone *", "git ls-remote *", "gh *", "xcodebuild *",
            "xcrun simctl *"])
        # Read grants stay narrow: other apps keep data in ~/Library/Caches and Developer.
        self.assertEqual(settings["sandbox"]["filesystem"]["allowRead"], ["~/Library/Python"])
        self.assertNotIn("allowWrite", settings["sandbox"]["filesystem"])

    def test_dry_run_writes_nothing(self):
        out = self.install("--dry-run")
        self.assertIn("settings.json", out)
        self.assertEqual(os.listdir(self.home), [])

    def test_off_switch_is_written_before_the_guard(self):
        out = self.install("--dry-run")
        guard = out.index("--- create ~/.config/playbook/tools/autonomy-guard.py")
        self.assertLess(out.index("--- create ~/.config/playbook/config"), guard)
        self.assertLess(out.index("--- create ~/.claude/settings.json"), guard)
        self.assertNotIn("--- create", out[guard + 1:])

    def test_no_answer_writes_nothing(self):
        out = self.install()
        self.assertIn("Nothing written.", out)
        self.assertEqual(os.listdir(self.home), [])

    def test_install_merges_and_leaves_autonomy_off(self):
        os.makedirs(self.path(".claude"))
        os.makedirs(self.path(".config", "playbook"))
        existing = {"enabledPlugins": {"x@y": True},
                    "permissions": {"allow": ["Bash(npm test)"], "deny": ["Bash(git push -f*)"]},
                    "sandbox": {"enabled": False}}
        with open(self.path(".claude", "settings.json"), "w") as f:
            json.dump(existing, f)
        with open(self.path(".config", "playbook", "config"), "w") as f:
            f.write('export PLAYBOOK_HOME="/somewhere"\n')
        self.install("--yes")

        s = json.loads(self.read(".claude", "settings.json"))
        self.assertEqual(s["enabledPlugins"], {"x@y": True})
        self.assertIn("Bash(npm test)", s["permissions"]["allow"])
        self.assertEqual(s["permissions"]["deny"].count("Bash(git push -f*)"), 1)
        self.assertIn("Bash(bundle exec fastlane *)", s["permissions"]["ask"])
        self.assertTrue(s["sandbox"]["enabled"])
        self.assertNotIn("__PLAYBOOK_HOME__", json.dumps(s))
        self.assertEqual(len(s["hooks"]["PreToolUse"]), 1)
        self.assertTrue([p for p in os.listdir(self.path(".claude"))
                         if p.startswith("settings.json.bak-")])

        cfg = self.read(".config", "playbook", "config")
        self.assertIn('export PLAYBOOK_HOME="/somewhere"', cfg)
        self.assertIn("export PLAYBOOK_AUTONOMY=off", cfg)
        for name in ("autonomy-guard.py", "codex-review.sh"):
            mode = os.stat(self.path(".config", "playbook", "tools", name)).st_mode
            self.assertTrue(mode & stat.S_IXUSR, name)
        self.assertTrue(self.read(".config", "playbook", "pii-words.txt").startswith("#"))

    def test_second_run_changes_nothing(self):
        self.install("--yes")
        first = {p: self.read(*p) for p in ((".claude", "settings.json"),
                                            (".config", "playbook", "config"))}
        self.assertIn("already installed", self.install("--yes"))
        for p, text in first.items():
            self.assertEqual(self.read(*p), text)

    def test_commented_switch_does_not_count(self):
        os.makedirs(self.path(".config", "playbook"))
        with open(self.path(".config", "playbook", "config"), "w") as f:
            f.write("# export PLAYBOOK_AUTONOMY=off\n")
        self.install("--yes")
        self.assertIn("\nexport PLAYBOOK_AUTONOMY=off\n", self.read(".config", "playbook", "config"))

    def test_existing_file_permissions_are_kept(self):
        os.makedirs(self.path(".claude"))
        os.makedirs(self.path(".config", "playbook"))
        for p in ((".claude", "settings.json"), (".config", "playbook", "config")):
            with open(self.path(*p), "w") as f:
                f.write("{}\n" if p[-1].endswith(".json") else "# config\n")
            os.chmod(self.path(*p), 0o600)
        self.install("--yes")
        for p in ((".claude", "settings.json"), (".config", "playbook", "config")):
            self.assertEqual(stat.S_IMODE(os.stat(self.path(*p)).st_mode), 0o600, p)

    def test_existing_switch_and_word_list_are_kept(self):
        os.makedirs(self.path(".config", "playbook"))
        with open(self.path(".config", "playbook", "config"), "w") as f:
            f.write("export PLAYBOOK_AUTONOMY=on\n")
        with open(self.path(".config", "playbook", "pii-words.txt"), "w") as f:
            f.write("Jane Example\n")
        self.install("--yes")
        self.assertEqual(self.read(".config", "playbook", "config").count("PLAYBOOK_AUTONOMY"), 1)
        self.assertEqual(self.read(".config", "playbook", "pii-words.txt"), "Jane Example\n")


class CodexWrapperTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="codex-wrapper-test-")  # $TMPDIR: a root the wrapper allows
        self.stub = os.path.join(self.tmp, "codex")
        self.args = os.path.join(self.tmp, "args.txt")
        with open(self.stub, "w") as f:
            f.write('#!/bin/bash\n[ "$1" = "--version" ] && { echo stub; exit 0; }\n'
                    f'printf "%s\\n" "$@" > "{self.args}"\n'
                    'while [ $# -gt 0 ]; do [ "$1" = "-o" ] && echo "Verdict: ok" > "$2"; '
                    'shift; done\n')
        os.chmod(self.stub, 0o755)
        self.prompt = os.path.join(self.tmp, "prompt.md")
        with open(self.prompt, "w") as f:
            f.write("review\n")

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def run_wrapper(self, *args):
        env = dict(os.environ, CODEX_BIN=self.stub, CODEX_REVIEWS_DIR=self.tmp)
        return subprocess.run(["bash", WRAPPER, *args], env=env, capture_output=True,
                              text=True, cwd=self.tmp)

    def test_runs_codex_under_the_read_deny_profile(self):
        r = self.run_wrapper(self.prompt, "unit-test")
        self.assertEqual(r.returncode, 0, r.stderr)
        with open(self.args) as f:
            args = f.read()
        self.assertNotIn("--sandbox", args)
        self.assertIn('default_permissions="playbook-review"', args)
        self.assertIn('"~/Documents"="deny"', args)
        self.assertIn('"~/Library/Mobile Documents"="deny"', args)
        shutil.rmtree(r.stdout.split("out: ")[1].split()[0])

    def test_rejects_bad_names_and_prompt_paths(self):
        for args in ((self.prompt, "../escape"), (self.prompt, "Bad Name"),
                     (os.path.expanduser("~/.zshenv"), "ok-name"), (self.prompt,)):
            r = self.run_wrapper(*args)
            self.assertNotEqual(r.returncode, 0, args)
            self.assertFalse(os.path.exists(self.args), args)


if __name__ == "__main__":
    unittest.main()
