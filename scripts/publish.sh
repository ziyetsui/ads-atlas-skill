#!/usr/bin/env bash
# Publish the workspace to the user's GitHub Pages. Run from the workspace root, only after the user confirmed
# the repo name and visibility.
#   bash scripts/publish.sh <repo-name> [--private] ["commit message"]
# Creates <gh user>/<repo-name> if missing, pushes main, switches Pages to "GitHub Actions", waits for the deploy,
# prints the site URL. GitHub Pages on a private repo needs a paid plan.
set -euo pipefail
[ $# -ge 1 ] || { echo "usage: bash scripts/publish.sh <repo-name> [--private] [\"commit message\"]"; exit 2; }
REPO="$1"; shift
VIS="--public"; MSG="Update competitor briefs"
for a in "$@"; do case "$a" in --private) VIS="--private" ;; *) MSG="$a" ;; esac; done
gh auth status >/dev/null 2>&1 || { echo "gh 没登录：在 Claude 输入框跑  ! gh auth login -h github.com -p https --web"; exit 2; }
OWNER=$(gh api user -q .login)
[ -d .git ] || git init -q -b main
git config user.name >/dev/null || git config user.name "$OWNER"
git config user.email >/dev/null || git config user.email "$OWNER@users.noreply.github.com"
gh auth setup-git >/dev/null 2>&1 || true

git add -A
git diff --cached --quiet || git commit -q -m "$MSG"
if ! gh repo view "$OWNER/$REPO" >/dev/null 2>&1; then
  gh repo create "$OWNER/$REPO" $VIS --source . --remote origin >/dev/null
fi
git remote get-url origin >/dev/null 2>&1 || git remote add origin "https://github.com/$OWNER/$REPO.git"
# Pages must serve from the Actions workflow (.github/workflows/pages.yml) before the push triggers it
gh api -X POST "repos/$OWNER/$REPO/pages" -f build_type=workflow >/dev/null 2>&1 \
  || gh api -X PUT "repos/$OWNER/$REPO/pages" -f build_type=workflow >/dev/null 2>&1 || true
BEFORE=$(gh run list -R "$OWNER/$REPO" -L 1 --json databaseId -q '.[0].databaseId' 2>/dev/null || true)
git push -q -u origin HEAD:main
sleep 8
RUN=$(gh run list -R "$OWNER/$REPO" -L 1 --json databaseId -q '.[0].databaseId' 2>/dev/null || true)
if [ -z "$RUN" ] || [ "$RUN" = "$BEFORE" ]; then  # nothing new pushed under site/: deploy anyway
  gh workflow run pages.yml -R "$OWNER/$REPO" >/dev/null; sleep 8
  RUN=$(gh run list -R "$OWNER/$REPO" -L 1 --json databaseId -q '.[0].databaseId')
fi
if ! gh run watch "$RUN" -R "$OWNER/$REPO" --exit-status >/dev/null; then
  # a brand-new empty repo can refuse the Pages switch before its first push: switch now and deploy once more
  gh api -X POST "repos/$OWNER/$REPO/pages" -f build_type=workflow >/dev/null 2>&1 \
    || gh api -X PUT "repos/$OWNER/$REPO/pages" -f build_type=workflow >/dev/null 2>&1 || true
  gh workflow run pages.yml -R "$OWNER/$REPO" >/dev/null; sleep 8
  RUN=$(gh run list -R "$OWNER/$REPO" -L 1 --json databaseId -q '.[0].databaseId')
  gh run watch "$RUN" -R "$OWNER/$REPO" --exit-status >/dev/null || { echo "deploy failed: gh run view $RUN -R $OWNER/$REPO --log-failed"; exit 1; }
fi
echo "deployed"
URL=$(gh api "repos/$OWNER/$REPO/pages" -q .html_url 2>/dev/null || echo "https://$OWNER.github.io/$REPO/")
echo "$URL"
