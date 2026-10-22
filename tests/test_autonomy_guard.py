#!/usr/bin/env python3
"""Tests for tools/autonomy-guard.py, the PreToolUse hook behind the core "Autonomy" policy.
Run from anywhere:  python3 tests/test_autonomy_guard.py
Each test builds a throwaway repo with a local bare remote, so nothing touches GitHub; the
repo's visibility is pinned through the guard's own `playbook.public` cache.
"""
import json
import os
import shutil
import subprocess
import tempfile
import unittest

PLAYBOOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GUARD = os.path.join(PLAYBOOK, "tools", "autonomy-guard.py")


def sh(cwd, *args):
    subprocess.run(args, cwd=cwd, check=True, capture_output=True)


class GuardTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="autonomy-guard-test-")
        self.home = os.path.join(self.tmp, "home")
        os.makedirs(os.path.join(self.home, ".config", "playbook"))
        self.set_autonomy("on")
        self.repo = os.path.join(self.tmp, "repo")
        remote = os.path.join(self.tmp, "remote.git")
        sh(self.tmp, "git", "init", "-q", "--bare", "-b", "main", remote)
        sh(self.tmp, "git", "init", "-q", "-b", "main", self.repo)
        for k, v in (("user.name", "Test User"), ("user.email", "test@example.invalid"),
                     ("commit.gpgsign", "false"), ("tag.gpgsign", "false"),
                     ("playbook.public", "false")):
            sh(self.repo, "git", "config", k, v)
        self.commit("README.md", "hello\n", "init")
        sh(self.repo, "git", "remote", "add", "origin", remote)
        sh(self.repo, "git", "push", "-q", "-u", "origin", "main")
        sh(self.repo, "git", "remote", "set-head", "origin", "main")
        sh(self.repo, "git", "switch", "-q", "-c", "feature")
        self.commit("feature.txt", "work\n", "feat: work")

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def commit(self, name, text, msg):
        with open(os.path.join(self.repo, name), "w") as f:
            f.write(text)
        sh(self.repo, "git", "add", name)
        sh(self.repo, "git", "commit", "-q", "-m", msg)

    def set_autonomy(self, value, words=None):
        with open(os.path.join(self.home, ".config", "playbook", "config"), "w") as f:
            f.write(f'export PLAYBOOK_HOME="{os.path.join(self.tmp, "playbook")}"\n')
            f.write(f"export PLAYBOOK_AUTONOMY={value}\n")
        if words is not None:
            with open(os.path.join(self.home, ".config", "playbook", "pii-words.txt"), "w") as f:
                f.write("# personal words\n" + "".join(w + "\n" for w in words))

    def run_guard(self, tool, tool_input, cwd=None):
        env = {k: v for k, v in os.environ.items()
               if k not in ("PLAYBOOK_AUTONOMY", "PLAYBOOK_HOME")}
        env["HOME"] = self.home
        payload = {"tool_name": tool, "tool_input": tool_input, "cwd": cwd or self.repo,
                   "hook_event_name": "PreToolUse"}
        r = subprocess.run(["python3", "-I", GUARD], input=json.dumps(payload), env=env,
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        if not r.stdout.strip():
            return None, ""
        out = json.loads(r.stdout)["hookSpecificOutput"]
        return out["permissionDecision"], out["permissionDecisionReason"]

    def bash(self, command, cwd=None):
        return self.run_guard("Bash", {"command": command}, cwd)[0]

    # --- main, force and deletion --------------------------------------------------------
    def test_feature_push_passes(self):
        self.assertIsNone(self.bash("git push -u origin feature"))
        self.assertIsNone(self.bash("git push"))

    def test_pushes_to_main_are_denied_in_any_spelling(self):
        for cmd in ("git push origin main", "git -C . push origin HEAD:main",
                    "git push origin feature:refs/heads/main", "cd . && git push origin main",
                    "git -c push.default=current push origin feature:main",
                    'bash -c "git push origin main"', "git push --all origin",
                    "git push --mirror origin"):
            self.assertEqual(self.bash(cmd), "deny", cmd)

    def test_bare_push_from_main_is_denied(self):
        sh(self.repo, "git", "switch", "-q", "main")
        self.assertEqual(self.bash("git push"), "deny")
        self.assertEqual(self.bash("git push origin HEAD"), "deny")

    def test_force_and_no_verify_are_denied(self):
        for cmd in ("git push --force origin feature", "git push -f origin feature",
                    "git push origin +feature", "git push --force-with-lease origin feature",
                    "git push --no-verify origin feature"):
            self.assertEqual(self.bash(cmd), "deny", cmd)

    def test_deleting_branches(self):
        self.assertEqual(self.bash("git push origin --delete main"), "deny")
        self.assertEqual(self.bash("git push origin :main"), "deny")
        self.assertEqual(self.bash("git push origin --delete feature"), "ask")

    def test_dry_run_passes(self):
        self.assertIsNone(self.bash("git push --dry-run origin main"))

    def test_tag_pushes_ask(self):
        sh(self.repo, "git", "tag", "v1.0.0")
        self.assertEqual(self.bash("git push origin v1.0.0"), "ask")
        self.assertEqual(self.bash("git push --tags"), "ask")

    def test_push_hidden_in_substitution_asks(self):
        self.assertEqual(self.bash('echo "$(git push origin feature)"'), "ask")

    # --- autonomy off ---------------------------------------------------------------------
    def test_autonomy_off_asks_for_routine_steps(self):
        self.set_autonomy("off")
        for cmd in ("git commit -m x", "git push origin feature", "gh pr merge 3 --merge",
                    "gh pr create --fill"):
            self.assertEqual(self.bash(cmd), "ask", cmd)
        self.assertEqual(self.bash("git push origin main"), "deny")
        self.assertIsNone(self.bash("git status"))

    def test_autonomy_on_allows_routine_steps(self):
        for cmd in ("git commit -m x", "gh pr merge 3 --merge", "gh pr create --fill"):
            self.assertIsNone(self.bash(cmd), cmd)

    def test_project_yml_switches_autonomy_off(self):
        os.makedirs(os.path.join(self.repo, ".claude"))
        with open(os.path.join(self.repo, ".claude", "project.yml"), "w") as f:
            f.write("kind: python\nautonomy: off\n")
        self.assertEqual(self.bash("git commit -m x"), "ask")

    # --- gh api ---------------------------------------------------------------------------
    def test_gh_api_reads_pass_and_writes_ask(self):
        self.assertIsNone(self.bash("gh api repos/o/r"))
        self.assertIsNone(self.bash("gh api -X GET repos/o/r/pulls -f state=open"))
        self.assertIsNone(self.bash("gh api graphql -f query='query { viewer { login } }'"))
        for cmd in ("gh api -X PATCH repos/o/r -f delete_branch_on_merge=true",
                    "gh api repos/o/r/pulls/1/comments -f body=hi",
                    "gh api --method=PUT repos/o/r/branches/main/protection",
                    "gh api graphql -f query='mutation { resolveReviewThread }'"):
            self.assertEqual(self.bash(cmd), "ask", cmd)

    # --- public repos ---------------------------------------------------------------------
    def test_public_push_needs_a_word_list(self):
        sh(self.repo, "git", "config", "playbook.public", "true")
        self.assertEqual(self.bash("git push origin feature"), "ask")

    def test_public_push_denied_on_personal_word(self):
        sh(self.repo, "git", "config", "playbook.public", "true")
        self.set_autonomy("on", words=["Jane Example"])
        self.assertIsNone(self.bash("git push origin feature"))
        self.commit("notes.md", "Thanks to jane example for the idea\n", "docs: notes")
        decision = self.run_guard("Bash", {"command": "git push origin feature"})
        self.assertEqual(decision[0], "deny")
        self.assertIn("Jane Example", decision[1])

    def test_public_push_denied_on_word_in_message_or_author(self):
        sh(self.repo, "git", "config", "playbook.public", "true")
        self.set_autonomy("on", words=["secret-codename"])
        self.commit("a.txt", "a\n", "feat: ship secret-codename")
        self.assertEqual(self.bash("git push origin feature"), "deny")

    def test_private_push_skips_the_scan(self):
        self.set_autonomy("on", words=["Jane Example"])
        self.commit("notes.md", "Jane Example\n", "docs: notes")
        self.assertIsNone(self.bash("git push origin feature"))

    # --- playbook edits -------------------------------------------------------------------
    def test_playbook_edits_from_other_projects(self):
        pb = os.path.join(self.tmp, "playbook")
        os.makedirs(os.path.join(pb, "core"))
        edit = lambda path, cwd: self.run_guard("Edit", {"file_path": path}, cwd)[0]
        self.assertEqual(edit(os.path.join(pb, "core", "agents-core.md"), self.repo), "deny")
        self.assertIsNone(edit(os.path.join(pb, "inbox.md"), self.repo))
        self.assertIsNone(edit(os.path.join(pb, "core", "agents-core.md"), pb))
        self.assertIsNone(edit(os.path.join(self.repo, "README.md"), self.repo))

    # --- robustness -----------------------------------------------------------------------
    def test_other_tools_and_bad_input_are_ignored(self):
        self.assertIsNone(self.run_guard("Read", {"file_path": "/etc/hosts"})[0])
        r = subprocess.run(["python3", "-I", GUARD], input="not json", capture_output=True,
                           text=True)
        self.assertEqual((r.returncode, r.stdout), (0, ""))


if __name__ == "__main__":
    unittest.main()
