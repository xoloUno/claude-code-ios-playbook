# Playbook Inbox

Lessons learned, gotchas, suggestions, and patterns discovered during Claude Code
sessions across all projects. Entries are written automatically by sessions in other
project directories. Periodically review this file in a dedicated playbook session to
curate worthwhile additions into the playbook, templates, or rules.

## How entries get here

Each bootstrapped project has a `.claude/rules/playbook-inbox.md` rule that tells
Claude Code to add entries here when it discovers something worth capturing.

## Curation process

In a Claude Code session in the `_playbook/` directory:
1. Read this file
2. Give each unnumbered entry the next entry number (below), raising the counter each time,
   then sort all entries newest first, with higher numbers first on the same date
3. For each entry, decide: **adopt** (update playbook/template/rules), **defer**, or **discard**
4. Adopted entries → make the change, then delete the entry
5. Deferred entries → leave them for next review
6. Discarded entries → delete them
7. If all entries are processed, leave only this header

## Entry format

**Next entry number:** 76

Capturing sessions append new entries at the bottom of this file without a number; curation
numbers them. Numbers are permanent IDs: never renumber an entry or reuse a removed number,
and keep the counter when the inbox is empty. Use the IDs when discussing entries. A numbered
entry's heading reads `### #[NUMBER] — [DATE] — [PROJECT_NAME]`.

```markdown
### [DATE] — [PROJECT_NAME]

**Category:** gotcha | suggestion | pattern | correction | tooling
**Context:** [what was being done when this was discovered]
**Lesson:** [the actual insight — be specific]
**Suggested action:** [what should change in playbook/template/rules, or "none — just FYI"]
```

---

### #75 — 2026-11-04 — Kendibah
**Category:** gotcha
**Context:** Merging a stack of PRs in order, each based on the previous PR's branch, with `gh pr merge N --merge --delete-branch`.
**Lesson:** Deleting the merged PR's branch closed the next PR in the stack, whose base it was, instead of retargeting it to `main`; a closed PR can't change its base. Recovery: push the merged commit back to the deleted branch name (it's already in `main`, so nothing is lost or force-pushed), `gh pr reopen`, `gh pr edit <next> --base main`, then delete the branch again. Safe order for each step: `gh pr merge N --merge` without `--delete-branch`, `gh pr edit <next> --base main`, then `git push origin --delete <branch>`.
**Suggested action:** Add the safe order to the core Git section or the stacked-PR notes in the Autonomy merge checklist.

### #74 — 2026-11-04 — Kendibah
**Category:** gotcha
**Context:** An autonomous local run pushing a stack of 10 PRs and their merge-commit updates to a private repo on GitHub Free.
**Lesson:** Build Check runs on every push to every non-main branch (bootstrap.sh template), on the `xcode-27` macOS runner at $0.062/min against Free's $12/month of included Actions usage (about 190 macOS minutes). Without `[skip ci]` on intermediate pushes, 121 runs (~261 min) in 4 days used it up, and every later run was blocked with the "payments have failed or your spending limit" annotation. The playbook already says local sessions add `[skip ci]` and leave it off only on the last push before a merge, but the Autonomy section and the merge checklist don't repeat it, so an autonomous run missed it.
**Suggested action:** Repeat the `[skip ci]` rule in the core Autonomy section (intermediate pushes, stacked-branch merge commits). The trigger part is in PR #68 (owner OK, 2026-11-04): the template runs on `pull_request` plus `workflow_dispatch`, so pushes without a PR cost nothing.

### #73 — 2026-11-04 — Kendibah
**Category:** gotcha
**Context:** Merging one stacked feature branch into the next with `git merge` in a repo whose lefthook runs a conventional-commit check on `commit-msg`.
**Lesson:** Git's default "Merge branch 'x' into y" message fails the conventional-commit hook, and the merge stops with "Not committing merge". Use `git merge --no-commit <branch>` then `git commit -m "chore(merge): bring in <branch>"`. Merge commits keep stacked PRs current without the force pushes Autonomy reserves for the owner.
**Suggested action:** Note it in the Git section of the core, or allow `Merge` subjects in the template's commit-msg check.

### #70 — 2026-11-04 — Kendibah
**Category:** gotcha
**Context:** Every GitHub Actions run on new branches failed in about 6 seconds with no steps, and `gh run view --log-failed` said "log not found".
**Lesson:** That shape is a billing block, not a build failure. The check run's annotation says so ("The job was not started because recent account payments have failed or your spending limit needs to be increased"): `gh api repos/<owner>/<repo>/check-runs/<job id>/annotations`. The Autonomy merge checklist then can't pass (no check ran), so a whole autonomous run parks its merges and TestFlight uploads.
**Suggested action:** In the merge checklist or CI notes, say to read the annotations of a step-less failed job first, and to park with one owner ping (billing is the owner's) rather than debug.

### #67 — 2026-11-03 — Flara
**Category:** suggestion
**Context:** After App Review approved 2.2.1, the plan was to bump `MARKETING_VERSION` to 2.3.0, per the Version Lifecycle rule. The only change waiting was one Swift line (the legal-pages base URL), metadata URLs and a description link fix, and the app's roadmap already used 2.3.0 for a feature tier. The owner asked whether this was really 2.2.2, and it shipped as 2.2.2.
**Lesson:** Brainstorm topic, not a settled lesson. Bumping to the next minor right after an approval guesses the next release's size before any work exists. A patch bump (2.2.1 → 2.2.2) is the smallest valid number that reopens the version train, and it can still be raised to 2.3.0 while that version is unsubmitted, once a feature lands. Bumping to minor by default can mislabel hotfixes and use up version numbers a roadmap has already assigned.
**Suggested action:** Discuss changing `packs/ios/rules/build-deploy.md` (Version Lifecycle, line 113) and `ios-project-playbook.md` §6.5 (lines 1515 and 1529) to: bump to the next patch after approval, and raise it to minor or major when feature work starts. Check first that App Store Connect lets you change a prepared version's number before submission.

### #63 — 2026-11-02 — Kendibah
**Category:** correction
**Context:** Corrects the 2026-10-28 Kendibah suggestion to add `tools/cursor-review.sh` as the merge-review fallback when Codex runs out. Since then most Kendibah merge reviews ran on Cursor + `grok-4.7-xhigh-fast`.
**Lesson:** Grok reviews took about 25 minutes per PR, and the owner judged that they miss bugs Claude and Codex catch (one had already missed a concurrency bug the GitHub Codex bot found). Cursor's monthly quota (88% used by Nov 2, resets Nov 11) does more good writing bounded code that Claude or Codex reviews. The owner now keeps Cursor for delegated implementation only. When Codex is out, the merge review is Claude Code's own `/code-review` skill, run in the session at high effort with the same Code Review Rules.
**Suggested action:** Drop the `cursor-review.sh` idea. In core "Second opinions" and the Autonomy merge checklist, name the fallback order: local Codex, then Claude Code's `/code-review` (high effort), never another model from the same vendor as the code's author. Keep Cursor in the delegation guidance only.

### #61 — 2026-11-02 — KendibahApp
**Category:** suggestion
**Context:** Every `/deploy` run prompted for permission, even right after the owner approved
the upload in chat.
**Lesson:** The pack's deploy step is one inline command (`export PATH=… && export LC_ALL=… &&
set -a && source .env.fastlane && set +a && bundle exec fastlane beta`). It reads credentials
and uploads, so auto mode asks every time, and a prefix allow rule can't match it because it
starts with `export`. A project script (`scripts/testflight-upload.sh`) that checks for a clean
`main`, runs the lane with Homebrew Ruby, logs to `$TMPDIR`, prints the build number, and undoes
fastlane's pbxproj and Info.plist edits can be allowed by exact name in
`.claude/settings.local.json`. That removes the prompt and the manual restore step. The chat
approval per upload stays.
**Suggested action:** Have bootstrap emit `scripts/testflight-upload.sh` (and a release
counterpart), point `packs/ios/commands/deploy.md` and `release.md` at them, and mention the
optional local allow rule in getting-started.

### #60 — 2026-11-02 — KendibahApp
**Category:** correction
**Context:** Running `/deploy` for a TestFlight upload. Step 1 says to `ls
~/Library/MobileDevice/Provisioning\ Profiles/` and stop if a Fastfile profile is missing.
**Lesson:** On this Mac (Xcode 27), the project's four App Store profiles live only in
`~/Library/Developer/Xcode/UserData/Provisioning Profiles/`, the folder current Xcode and
`fastlane sigh` use; the legacy `~/Library/MobileDevice/Provisioning Profiles/` holds only older
apps' profiles. Read literally, step 1 reports every profile missing and blocks a deploy that
works. Match by the profile's `Name` (`security cms -D -i <file> | plutil -extract Name raw -o -
-`), not the filename, across both folders. Separately, an earlier session left
`*.mobileprovision.bak-*` backups inside the legacy folder: `xcodebuild` tries to load every file
there and logs a "No provisioning profile provider found" warning per backup on every archive,
which buries real signing errors. Keep profile backups outside both folders.
**Suggested action:** In `packs/ios/commands/deploy.md` and `release.md` step 1, check both
folders by profile Name, and say where to install a downloaded profile (the UserData folder).
Add a line to the playbook's signing section: never back up a profile inside a profiles folder.

### #58 — 2026-11-02 — Kendibah
**Category:** suggestion
**Context:** An autonomous run shipped three feature PRs, then opened a separate PR (with its own
full suite, CI and Cursor + Grok merge review) for a small flash fix, and another for a docs-only
TestFlight note. The owner asked to roll such pieces into the next chunk to save time and tokens.
**Lesson:**
- A merge review's cost is mostly fixed: the reviewer re-reads AGENTS.md and the surrounding files
  before it looks at the diff, which here took 5–15 minutes whether the diff was 10 lines or 300.
  The full test run, CI, PR text and merge bookkeeping are also per PR. A tiny PR or a docs-only
  record pays all of that for almost no diff.
- Batch small, related fixes and records (TestFlight notes, Current State updates) onto the next
  real feature branch and review once per chunk. Keep risky or unrelated work (session-model
  concurrency, new reverse-engineered protocols) in its own PR, so a finding there doesn't hold up
  everything else.
- A very long session costs more per turn because every turn re-sends the history. Once the
  handoff (WORKLOG, MANUAL-TASKS, Current State) is saved, starting the next chunk in a fresh
  session is cheaper than continuing.
**Suggested action:** In the core "Autonomy" section, say a merge review covers a meaningful
chunk: fold small fixes and docs-only records into the next PR rather than opening one each, and
keep separate PRs for risky or independent work. Consider the same note in the `/deploy` skill's
step 7 (record the deploy in the next PR instead of a `chore/` PR of its own). Under "Session
hygiene", suggest a fresh session once a long run's handoff is written.

### #53 — 2026-11-02 — Kendibah
**Category:** pattern
**Context:** Autonomous batch 4: three features (keyboard, a drawer of app and input tiles, a
device picker) delegated to Cursor (grok-4.7-xhigh-fast) in parallel worktrees, with Codex
reviewing every merge.
**Lesson:**
- Running one `codex-review.sh` pass on the written PLAN, before any brief, found six design
  gaps the merge reviews would have met as bugs in delegated code: a text queue diffed against
  confirmed rather than queued text (double characters), a rejected command left in a field and
  resent after purchase, multi-character sends that can half-land, queued commands reaching a
  newly selected device, a hide action with no path back, and a "favorite" with no stored state.
- With those fixes written into the briefs, all three delegates compiled, passed tests and
  linted clean on the first run. The four merge reviews then found one defect (closing a sheet
  dropped queued text), where batches 1 to 3 found one in nearly every PR.
- Delegate models took closures returning `Result`, not the session object, so they built on
  `main` without the API PR; the API PR still merged first so the closures had a real target.
**Suggested action:** In "Second opinions", say the plan review is most valuable right before
delegating, and that its findings go into the briefs as explicit requirements (with the test
that proves each). Record per-batch first-run pass rates in the delegation notes.

### #48 — 2026-11-01 — Kendibah
**Category:** pattern
**Context:** Delegation batch 3: Cursor (`grok-4.7-xhigh-fast`) wrote the remote screen and the
purchase sheet; Claude wired them into the app. Each PR got the local Codex merge review
(`codex-review.sh`, scoped to the PR's diff), and the repo also has the GitHub Codex bot.
**Lesson:**
- Merge reviews found a real defect in all three PRs (eight of nine across batches 1–3). Green
  delegate tests caught none of them: VoiceOver could power the TV off without the hold, and a
  pending-approval purchase closed the sheet.
- The diff-scoped local review misses what a PR leaves out. The GitHub bot caught two of these:
  - the app wired Samsung control, but nothing in production ever called `pair()`, so a new
    Samsung TV could never be controlled (P1);
  - Lifetime wasn't offered during an active trial.

  The bot posted within minutes of the PR opening, before CI finished, so the core rule "fix any
  the bot has posted by then" caught both.
- Orchestrator chores:
  - Resolve `project.pbxproj` conflicts between parallel delegate branches with `git checkout
    --theirs` plus `xcodegen generate`, never by hand.
  - Lefthook's conventional-commit hook rejects git's default "Merge remote-tracking branch"
    message, so finish a main-into-branch merge with `git commit -m "chore(merge): …"`.
**Suggested action:**
- Add a missing-caller check to the merge-review prompt for wiring or integration PRs: for every
  required user step the change depends on (pairing, sign-in, purchase, permission), name its
  production caller, or report it missing.
- In "Autonomy", note that the GitHub Codex bot finds a different class of bug than the local
  review, and that it usually posts before CI ends.

### #47 — 2026-11-01 — Kendibah
**Category:** pattern
**Context:** From 2026-10-28 to 11-01, Claude Code orchestrated while delegating production code
to local delegates. Batches 1 and 2 ran five bounded tasks: four with `cursor-agent` on
`grok-4.7-xhigh-fast`, and one with `codex exec`. Every PR also got a local Codex merge review.
This closes the experiment proposed in the 10-28 "six bounded tasks" entry.
**Lesson:**
- **Roles that worked:**
  - Claude writes the brief, keeps concurrency and new-API work, builds and tests everything,
    commits, opens PRs and merges.
  - Delegates write bounded code, each in its own worktree.
  - The local Codex review runs before every merge.
- **Results:**
  - **Codex (`codex exec`):** about 3 minutes per task. It compiled and passed on the first real
    build, with no fix-ups. It can't build inside its sandbox (`~/.cache/clang/ModuleCache:
    Operation not permitted`), and it spends the Codex quota the owner reserves for reviews.
  - **Cursor, launched from the wrong directory:** it couldn't build. It shipped a typed-throws
    closure helper that didn't compile.
  - **Cursor, launched from its worktree:** about 13 minutes per task, two tasks in parallel. It
    built and tested its own work, and both passed first time.
  - **The experiment's answer:** once Cursor can build, compile-error fix-ups drop to zero, but
    logic bugs remain.
- **Codex merge reviews found a real defect in five of six PRs, including Claude's own, and green
  tests caught none of them:**
  - a stale-state race across awaits on one actor;
  - keypresses interleaving mid-text;
  - a missed device-info flag;
  - a reconnect race that could show a pairing prompt (P1);
  - StoreKit transactions finished before being persisted, and a listener registered after the
    first refresh;
  - a superseded report still written to disk.
- **Launch recipes:**
  - Cursor: `cd <worktree> && cursor-agent -p --trust --workspace "$PWD" --model
    grok-4.7-xhigh-fast "<brief>"`, with `.cursor/cli.json` allowing only xcodebuild, xcodegen
    and swiftlint, and with neither `--force` nor `--sandbox`. The allowlist loads from the
    working directory, not `--workspace`; otherwise the global config applies (here, `ls` only).
  - Codex: `codex exec -C <worktree> -s workspace-write -m <model> -c
    model_reasoning_effort=high -o <last-message-file> "<brief>"`.
- **Brief must-haves:**
  - exact files to edit, and a ban on everything else (unprompted, Cursor hand-edited
    `project.pbxproj` in an XcodeGen project, and `.swiftlint.yml`);
  - the existing pattern to copy;
  - required tests, including error, cancellation and race paths;
  - the exact build and test command, on a reserved simulator UDID;
  - no git, network or device traffic;
  - no closure parameters with typed `throws(E)`;
  - a reply listing files, test counts and doubts.
- **Orchestrator chores:**
  - Regenerate the project with XcodeGen in a clean worktree.
  - Delete the delegates' DerivedData, and stage explicit paths (never `.cursor/`).
  - After each merge, merge main into the next branch, re-test, push, and wait for CI. Those
    sequential CI rounds are the slowest part: three PRs mean three rounds.
  - Three parallel `xcodebuild` runs pushed one test past 10 minutes, so serialize the
    orchestrator's own test runs.
**Suggested action:**
- Write a "delegating implementation" section, in core "Second opinions" or in a pack, covering:
  - the roles;
  - both launch recipes;
  - the brief template with the must-haves above;
  - the rule that the local Codex review before merge is mandatory, because green delegate tests
    aren't enough.
- Default implementation to Cursor and keep Codex for reviews when the Codex quota is tight.
- This replaces two earlier 2026-11-01 Kendibah entries.

### #46 — 2026-10-31 — Kendibah
**Category:** gotcha
**Context:** A Debug device build after Apple granted a restricted entitlement (multicast). The
Xcode-managed development profile predated the grant, so it had to be regenerated with
`xcodebuild -allowProvisioningUpdates`.
**Lesson:** From an agent's shell, `xcodebuild` reported "No Accounts: Add a new account in
Accounts settings" even though Xcode had an Apple ID signed in, sandboxed or not. It then
blamed the entitlement ("requires approval from Apple"), which was misleading: the App ID
already had it. Passing the App Store Connect API key fixed it:
`-authenticationKeyPath "$ASC_KEY_FILEPATH" -authenticationKeyID "$ASC_KEY_ID"
-authenticationKeyIssuerID "$ASC_ISSUER_ID"` (sourced from `.env.fastlane`). The regenerated
dev profile then carried the entitlement. Earlier device builds never hit this because the
existing profile already matched the entitlements.
**Suggested action:** In `build-deploy.md` (or the device-build notes), say that an agent's
device build that needs a profile refresh should pass the ASC API key flags, and that "requires
approval from Apple" after a granted entitlement usually means the profile couldn't refresh.

### #45 — 2026-10-30 — Kendibah
**Category:** gotcha
**Context:** First `fastlane beta` run for Kendibah, using the Fastfile that `bootstrap.sh` emits.
**Lesson:** The lane failed before gym with `undefined method 'sub' for nil` at `scheme: Dir.glob("*.xcodeproj").first.sub(".xcodeproj", "")`. fastlane runs the lane's own Ruby with `Dir.chdir` into `fastlane/` and runs each action from the project root (fastlane 2.232.1, `runner.rb`), so a bare `Dir.glob("*.xcodeproj")` written in the lane returns `[]`. The `xcodeproj:` and `path:` globs silently become nil, and the actions fall back to their own defaults, which hides the bug until `.sub` hits nil. Flara works because it uses literal names (`"Flara.xcodeproj"`). broadsheet, dachipari and teewye still carry the template pattern.
**Suggested action:** In `bootstrap.sh`'s Fastfile template (lines ~497–545), emit the literal project and scheme names (`"<App>.xcodeproj"`, `"<Scheme>"`) instead of `Dir.glob`. Check the downstream Fastfiles before their first upload.

### #42 — 2026-10-28 — Kendibah
**Category:** gotcha
**Context:** Codex launched `cursor-agent -p` with the per-worktree `.cursor/cli.json` allowlist (xcodebuild, xcodegen, swiftlint) to build a transport while Codex worked.
**Lesson:** Started from inside Codex's own command sandbox, Cursor had every shell command rejected, including allowlisted `swiftlint` and `xcodebuild`. It reported only "Rejected:", with no reason, and returned code that had never compiled or run (three test bugs). Launched from Claude Code the same day, the same allowlist ran `swiftlint` and `xcodegen` and refused `whoami` and `git`. A nested agent inherits its parent's sandbox, so the parent decides what the child can run, whatever the child's own permissions say.
**Suggested action:** In delegation guidance, say to launch Cursor from an unsandboxed parent, or to check its first shell call, before counting a run as "Cursor built and tested it". Treat "Rejected:" in Cursor's output as "nothing ran".

### #28 — 2026-10-27 — DachipariApp
**Category:** gap
**Context:** `bootstrap.sh` produced an iPhone-first, portrait, iOS-only project (XcodeGen target, CI building only the iOS simulator, fastlane `platform :ios`). The spec is a tvOS + iPadOS app with Universal Purchase.
**Lesson:** A multiplatform app needs one XcodeGen target with `supportedDestinations: [iOS, tvOS]` (one bundle ID, so Universal Purchase works), `TARGETED_DEVICE_FAMILY` `2,3` for iPad + TV with no iPhone, and a CI build per platform. The playbook has no tvOS guidance, so each project has to retarget by hand.
**Suggested action:** Add a bootstrap platforms option (iphone / ipad / tvos) that sets destinations, device family, orientation and CI destinations, or note in getting-started.md what to change for non-iPhone apps.

### #26 — 2026-10-27 — DachipariApp
**Category:** gotcha
**Context:** Planning a tvOS + iPadOS camera app (Continuity Camera on Apple TV). The spike plan logged results to a JSONL file in Documents and assumed the TV could use two Continuity Cameras at once.
**Lesson:** WWDC23 session 10256 ("Discover Continuity Camera for tvOS") says `.documentDirectory` is in the tvOS headers but fails with a runtime error. tvOS apps should use only `.cachesDirectory`, which can be purged between launches. The same session says only one Continuity Camera can be connected to an Apple TV at a time. The SDK headers don't mention either limit.
**Suggested action:** If the playbook adds tvOS guidance, include both: Caches-only file storage on tvOS (pull logs before the app quits, or move data to iCloud), and a single Continuity Camera per Apple TV.
