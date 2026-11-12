#!/usr/bin/env bash
# Self-test of scripts/check-private-names against the private-names-guard
# spec, on synthetic names in a throwaway repository. It never reads the real
# list: HOME and AGENT_PLUGINS_PRIVATE_NAMES point at temporary files.
set -euo pipefail

unset -f grep 2>/dev/null || true

here=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
root=$(cd -- "${here}/.." && pwd)
guard="${root}/scripts/check-private-names"

# A hook runs with git's per-repository variables set; the throwaway
# repository must not inherit them, nor the committer's configuration.
# shellcheck disable=SC2046
unset $(git rev-parse --local-env-vars)
export GIT_CONFIG_GLOBAL=/dev/null GIT_CONFIG_NOSYSTEM=1
export GIT_AUTHOR_NAME=Tester GIT_AUTHOR_EMAIL=tester@example.invalid
export GIT_COMMITTER_NAME=Tester GIT_COMMITTER_EMAIL=tester@example.invalid
unset AGENT_PLUGINS_PRIVATE_NAMES

tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
export HOME="${tmp}/home"
mkdir -p "$HOME"

# The synthetic list: a comment and an empty line around one pattern.
list="${tmp}/list"
printf '# qqcomment\n\nzzq-[a-z]+\n' >"$list"
fallback="${HOME}/.config/agent-plugins/private-names"

failures=0
out="${tmp}/out"

# expect CODE DESCRIPTION COMMAND... : run COMMAND, compare its exit code.
expect() {
	local want=$1 desc=$2 rc=0
	shift 2
	"$@" >"$out" 2>&1 || rc=$?
	if [[ $rc == "$want" ]]; then
		printf 'ok    %s\n' "$desc"
	else
		printf 'FAIL  %s (exit %s, wanted %s)\n' "$desc" "$rc" "$want"
		sed -e 's/^/      | /' "$out"
		failures=$((failures + 1))
	fi
}

# expect_output TEXT DESCRIPTION : the last command's output holds TEXT.
expect_output() {
	if grep -q -F -e "$1" "$out"; then
		printf 'ok    %s\n' "$2"
	else
		printf 'FAIL  %s (no "%s" in the output)\n' "$2" "$1"
		sed -e 's/^/      | /' "$out"
		failures=$((failures + 1))
	fi
}

with_list() { AGENT_PLUGINS_PRIVATE_NAMES=$list "$guard" "$@"; }

repo="${tmp}/repo"
git init -q "$repo"
cd "$repo"

# A fresh index: stage exactly the given files, nothing left from before.
stage() {
	git rm -q -r -f --cached --ignore-unmatch . >/dev/null
	git add -- "$@"
}

printf 'nothing to see\n' >clean.txt
printf 'qqcomment\n# qqcomment\n' >comment.txt
stage clean.txt comment.txt

## The list is read from outside the repository

printf 'a\nb\nzzq-content here\n' >content.txt
stage content.txt
expect 1 'the variable names the list' with_list content.txt
mkdir -p "$(dirname "$fallback")"
cp "$list" "$fallback"
expect 1 'the fallback path holds the list' "$guard" content.txt
stage clean.txt comment.txt
expect 0 'comment and empty lines are not patterns' "$guard" clean.txt comment.txt
rm "$fallback"

## The guard fails closed without a usable list

stage content.txt
expect 2 'neither source exists' "$guard" content.txt
expect_output 'AGENT_PLUGINS_PRIVATE_NAMES' 'neither source: the message names the variable'
# shellcheck disable=SC2088 # the literal text of the message
expect_output '~/.config/agent-plugins/private-names' 'neither source: the message names the fallback path'
cp "$list" "$fallback"
expect 2 'the variable names a missing file' \
	env AGENT_PLUGINS_PRIVATE_NAMES="${tmp}/missing" "$guard" content.txt
rm "$fallback"
printf '# only a comment\n\n' >"${tmp}/empty-list"
stage clean.txt
expect 2 'the list has no pattern' \
	env AGENT_PLUGINS_PRIVATE_NAMES="${tmp}/empty-list" "$guard" clean.txt
printf 'zzq-(\n' >"${tmp}/bad-list"
expect 2 'a pattern is invalid' \
	env AGENT_PLUGINS_PRIVATE_NAMES="${tmp}/bad-list" "$guard" clean.txt
expect 2 'a pattern is invalid: --message' \
	env AGENT_PLUGINS_PRIVATE_NAMES="${tmp}/bad-list" "$guard" --message clean.txt
expect 2 'a pattern is invalid: --history' \
	env AGENT_PLUGINS_PRIVATE_NAMES="${tmp}/bad-list" "$guard" --history

## Every staged path and its staged content are checked

stage content.txt
expect 1 'staged content names a private name' with_list content.txt
expect_output 'content.txt:3: zzq-content' 'a content finding names its path, line and match'

mkdir -p dir
printf 'nothing\n' >dir/zzq-path.txt
stage dir/zzq-path.txt
expect 1 'a staged path names a private name' with_list dir/zzq-path.txt
expect_output 'dir/zzq-path.txt' 'a path finding names the path'

ln -s zzq-link link
stage link
expect 1 'a symbolic link points at a private name' with_list link
expect_output 'link: link target matches: zzq-link' 'a link finding names the link and its target'

mkdir -p .claude/commands/opsx openspec/changes/archive/old
printf 'zzq-generated\n' >.claude/commands/opsx/x.md
printf 'zzq-archived\n' >openspec/changes/archive/old/y.md
stage .claude/commands/opsx/x.md
expect 1 'generated files are not exempt' with_list .claude/commands/opsx/x.md
stage openspec/changes/archive/old/y.md
expect 1 'archived files are not exempt' with_list openspec/changes/archive/old/y.md

printf 'bin\000zzq-binary\000\n' >blob.bin
stage blob.bin
expect 1 'binary files are not exempt' with_list blob.bin

printf 'zzq-staged\n' >dirty.txt
stage dirty.txt
printf 'clean now\n' >dirty.txt
expect 1 'the index is read, not the working tree' with_list dirty.txt

stage clean.txt
printf 'zzq-unstaged\n' >>clean.txt
expect 0 'an unstaged match does not fail the commit' with_list clean.txt
printf 'nothing to see\n' >clean.txt

stage clean.txt comment.txt
expect 0 'a clean commit passes' with_list clean.txt comment.txt
expect 0 'no paths handed passes' with_list

## The commit message is checked

printf 'Subject\n\nbody zzq-message\n' >"${tmp}/msg"
expect 1 'the message names a private name' with_list --message "${tmp}/msg"
expect_output 'commit message:3: zzq-message' 'a message finding names its line and match'
printf 'Subject\n# zzq-comment\n# ------------------------ >8 ------------------------\nzzq-diff\n' \
	>"${tmp}/msg"
expect 0 "git's comment lines are ignored" with_list --message "${tmp}/msg"

## One install enables both checks

config="${root}/.pre-commit-config.yaml"
if grep -q -E '^default_install_hook_types: \[pre-commit, commit-msg\]$' "$config"; then
	printf 'ok    %s\n' 'one install enables both checks'
else
	printf 'FAIL  %s\n' 'one install enables both checks'
	failures=$((failures + 1))
fi

## The guard runs only locally

if git -C "$root" grep -q -F check-private-names -- \
	.github .gitlab-ci.yml .circleci .woodpecker .forgejo .gitea 2>/dev/null; then
	printf 'FAIL  %s\n' 'no workflow runs the guard'
	failures=$((failures + 1))
else
	printf 'ok    %s\n' 'no workflow runs the guard'
fi

## The whole history can be checked

stage clean.txt
git commit -q --no-verify -m 'clean start'
expect 0 'a clean history passes' with_list --history

stage content.txt
git commit -q --no-verify -m 'made without the hooks'
bad=$(git rev-parse HEAD)
git commit -q --no-verify --allow-empty -m 'clean on top'
expect 1 'an earlier commit names a private name' with_list --history
expect_output "$bad" 'a history finding names the commit'

git reset -q --hard HEAD~2
expect 0 'the history is clean again' with_list --history

git commit -q --no-verify --allow-empty -m 'clean subject' -m 'zzq-history-message'
expect 1 'a commit message in the history' with_list --history
git reset -q --hard HEAD~1

GIT_AUTHOR_NAME=zzq-author git commit -q --no-verify --allow-empty -m 'clean'
expect 1 'an author identity in the history' with_list --history
git reset -q --hard HEAD~1

ln -s zzq-history-link hlink
git add hlink
git commit -q --no-verify -m 'a link'
expect 1 'a symbolic link in the history' with_list --history
git reset -q --hard HEAD~1

git branch zzq-branch
expect 1 'a ref name' with_list --history
git branch -q -D zzq-branch

git tag -a -m 'zzq-tag-message' v0
expect 1 'an annotated tag message' with_list --history
git tag -d v0 >/dev/null

expect 0 'the history is clean at the end' with_list --history

if ((failures)); then
	printf '%s assertion(s) failed\n' "$failures"
	exit 1
fi
printf 'all assertions passed\n'
