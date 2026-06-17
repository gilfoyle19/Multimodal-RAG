$localIssues = if (Test-Path "issues/*.md") {
  Get-Content "issues/*.md" -Raw
} else {
  "No local issues found"
}

$githubIssues = "GitHub issues were not checked."
if (Get-Command gh -ErrorAction SilentlyContinue) {
  $repo = gh repo view --json nameWithOwner 2>$null
  if ($LASTEXITCODE -eq 0) {
    $githubIssues = gh issue list --state open --limit 100 --json number,title,body,comments,labels,url,state,createdAt,updatedAt 2>$null
    if ($LASTEXITCODE -ne 0 -or -not $githubIssues) {
      $githubIssues = "GitHub issue check failed. Run 'gh auth status' and verify this repository has a GitHub remote."
    }
  } else {
    $githubIssues = "GitHub issue check skipped. Run 'gh auth status' and verify this repository has a GitHub remote."
  }
} else {
  $githubIssues = "GitHub issue check skipped because the GitHub CLI ('gh') is not installed or not on PATH."
}

$commits = git log --grep="RALPH" -n 10 --format="%H%n%ad%n%B---" --date=short 2>$null
if (-not $commits) {
  $commits = "No RALPH commits found"
}

$prompt = Get-Content "ralph/prompt.md" -Raw

$fullPrompt = @"
Previous RALPH commits:

$commits

GitHub issues:

$githubIssues

Local issues:

$localIssues

$prompt
"@

codex exec --sandbox workspace-write $fullPrompt
