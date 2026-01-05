"""
Gemini-based solver that generates unified diff patches from GitHub issues.
"""
import argparse
import json
import os

from google import genai

PROMPT_TEMPLATE = """You are a coding assistant operating in GitHub Actions.

Task:
- Read the issue (title/body) and latest issue comments.
- Produce ONLY a unified diff patch that applies cleanly with `git apply`.
- The patch MUST be minimal and directly address the issue.
- If you cannot confidently implement, output an empty patch (no text).

Rules:
- Output must start with: diff --git
- No markdown fences. No explanation. No extra text.
- Use correct file paths from the FILE TREE below.

FILE TREE:
{file_tree}

Issue:
TITLE: {title}

BODY:
{body}

COMMENTS (JSON):
{comments_json}
"""


def main():
  ap = argparse.ArgumentParser()
  ap.add_argument("--issue-json", required=True)
  ap.add_argument("--issue-comments-json", required=True)
  ap.add_argument("--file-tree", required=False, default="")
  ap.add_argument("--out", required=True)
  args = ap.parse_args()

  issue = json.load(open(args.issue_json, "r", encoding="utf-8"))
  comments = json.load(open(args.issue_comments_json, "r", encoding="utf-8"))

  file_tree = ""
  if args.file_tree:
    with open(args.file_tree, "r", encoding="utf-8") as f:
      file_tree = f.read()

  title = issue.get("title", "")
  body = issue.get("body", "") or ""
  comments_json = json.dumps(
      [{
          "user": c.get("user", {}).get("login"),
          "body": c.get("body")
      } for c in comments],
      ensure_ascii=False,
      indent=2,
  )

  project = os.environ["GOOGLE_CLOUD_PROJECT"]
  location = os.environ["GOOGLE_CLOUD_LOCATION"]

  client = genai.Client(vertexai=True, project=project, location=location)

  prompt = PROMPT_TEMPLATE.format(
      file_tree=file_tree,
      title=title,
      body=body,
      comments_json=comments_json,
  )

  resp = client.models.generate_content(
      model="gemini-2.5-flash-lite",
      contents=prompt,
  )
  text = (resp.text or "").lstrip()

  # guard: only accept outputs that look like unified diff
  if not text.startswith("diff --git"):
    text = ""

  with open(args.out, "w", encoding="utf-8") as f:
    f.write(text)


if __name__ == "__main__":
  main()
