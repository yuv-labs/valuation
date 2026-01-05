"""
Gemini-based agentic solver with tool-calling for GitHub issues.

This agent can read/write files, run shell commands, and iteratively
solve issues like a human developer would.
"""
import argparse
import json
import os
from pathlib import Path
import subprocess

from google import genai
from google.genai import types

MAX_ITERATIONS = 20
MODEL = 'gemini-2.5-flash-preview-05-20'

TOOLS = [
    types.Tool(function_declarations=[
        types.FunctionDeclaration(
            name='read_file',
            description='Read the contents of a file at the given path.',
            parameters=types.Schema(
                type='OBJECT',
                properties={
                    'path':
                        types.Schema(
                            type='STRING',
                            description='File path relative to repo root',
                        ),
                },
                required=['path'],
            ),
        ),
        types.FunctionDeclaration(
            name='write_file',
            description=
            'Write content to a file. Creates directories if needed.',
            parameters=types.Schema(
                type='OBJECT',
                properties={
                    'path':
                        types.Schema(
                            type='STRING',
                            description='File path relative to repo root',
                        ),
                    'content':
                        types.Schema(
                            type='STRING',
                            description='Content to write',
                        ),
                },
                required=['path', 'content'],
            ),
        ),
        types.FunctionDeclaration(
            name='list_dir',
            description='List files and directories at the given path.',
            parameters=types.Schema(
                type='OBJECT',
                properties={
                    'path':
                        types.Schema(
                            type='STRING',
                            description='Directory path relative to repo root',
                        ),
                },
                required=['path'],
            ),
        ),
        types.FunctionDeclaration(
            name='run_shell',
            description='Run a shell command. Use for pytest, git status, etc.',
            parameters=types.Schema(
                type='OBJECT',
                properties={
                    'command':
                        types.Schema(
                            type='STRING',
                            description='Shell command to execute',
                        ),
                },
                required=['command'],
            ),
        ),
        types.FunctionDeclaration(
            name='done',
            description='Call this when the task is complete.',
            parameters=types.Schema(
                type='OBJECT',
                properties={
                    'summary':
                        types.Schema(
                            type='STRING',
                            description='Summary of changes made',
                        ),
                },
                required=['summary'],
            ),
        ),
    ])
]

SYSTEM_PROMPT = '''You are an expert software engineer solving a GitHub issue.

You have access to these tools:
- read_file(path): Read file contents
- write_file(path, content): Write/create files
- list_dir(path): List directory contents
- run_shell(command): Run shell commands (pytest, git, etc.)
- done(summary): Call when task is complete

Workflow:
1. First, explore the codebase to understand the project structure
2. Read relevant files to understand the existing code
3. Make necessary changes using write_file
4. Run tests with run_shell("pytest") to verify changes
5. If tests fail, read the error and fix the code
6. Call done() when everything works

Rules:
- Always read files before modifying them
- Run pytest after making changes
- Keep changes minimal and focused
- Follow existing code style
- Do NOT commit - just make the code changes
'''


def execute_tool(name: str, args: dict) -> str:
  """Execute a tool and return the result as a string."""
  if name == 'read_file':
    return _execute_read_file(args)
  if name == 'write_file':
    return _execute_write_file(args)
  if name == 'list_dir':
    return _execute_list_dir(args)
  if name == 'run_shell':
    return _execute_run_shell(args)
  if name == 'done':
    summary = args.get('summary', 'No summary')
    return f'TASK_COMPLETE: {summary}'
  return f'Error: Unknown tool: {name}'


def _execute_read_file(args: dict) -> str:
  """Read file contents."""
  try:
    path = Path(args['path'])
    if not path.exists():
      return f'Error: File not found: {path}'
    if path.is_dir():
      return f'Error: Path is a directory, use list_dir: {path}'
    content = path.read_text(encoding='utf-8')
    if len(content) > 50000:
      return f'File too large. First 50000 chars:\n{content[:50000]}'
    return content
  except (OSError, UnicodeDecodeError) as e:
    return f'Error reading file: {e}'


def _execute_write_file(args: dict) -> str:
  """Write content to file."""
  try:
    path = Path(args['path'])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(args['content'], encoding='utf-8')
    content_len = len(args['content'])
    return f'Successfully wrote {content_len} chars to {path}'
  except OSError as e:
    return f'Error writing file: {e}'


def _execute_list_dir(args: dict) -> str:
  """List directory contents."""
  try:
    path = Path(args['path']) if args['path'] else Path('.')
    if not path.exists():
      return f'Error: Directory not found: {path}'
    if not path.is_dir():
      return f'Error: Not a directory: {path}'
    items = sorted(path.iterdir())
    result = []
    for item in items[:100]:
      prefix = '[DIR] ' if item.is_dir() else '[FILE]'
      result.append(f'{prefix} {item.name}')
    if len(items) > 100:
      result.append(f'... and {len(items) - 100} more items')
    return '\n'.join(result) if result else '(empty directory)'
  except OSError as e:
    return f'Error listing directory: {e}'


def _execute_run_shell(args: dict) -> str:
  """Run shell command."""
  try:
    proc = subprocess.run(
        args['command'],
        shell=True,
        capture_output=True,
        text=True,
        timeout=120,
        cwd=Path.cwd(),
        check=False,
    )
    output = f'Exit code: {proc.returncode}\n'
    if proc.stdout:
      stdout = proc.stdout[:10000] if len(proc.stdout) > 10000 else proc.stdout
      output += f'STDOUT:\n{stdout}\n'
    if proc.stderr:
      stderr = proc.stderr[:5000] if len(proc.stderr) > 5000 else proc.stderr
      output += f'STDERR:\n{stderr}\n'
    return output
  except subprocess.TimeoutExpired:
    return 'Error: Command timed out after 120 seconds'
  except OSError as e:
    return f'Error running command: {e}'


def run_agent(client: genai.Client, issue_context: str, max_iter: int) -> str:
  """Run the agent loop until done or max iterations."""
  messages = [
      types.Content(role='user', parts=[types.Part(text=issue_context)]),
  ]

  for iteration in range(max_iter):
    print(f'[Iteration {iteration + 1}/{max_iter}]')

    response = client.models.generate_content(
        model=MODEL,
        contents=messages,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            tools=TOOLS,
            temperature=0.2,
        ),
    )

    if not response.candidates:
      print('No response from model')
      break

    candidate = response.candidates[0]
    assistant_content = candidate.content
    messages.append(assistant_content)

    function_calls = []
    text_parts = []

    for part in assistant_content.parts:
      if part.function_call:
        function_calls.append(part.function_call)
      if part.text:
        text_parts.append(part.text)

    if text_parts:
      text_preview = ' '.join(text_parts)[:200]
      print(f'Agent: {text_preview}...')

    if not function_calls:
      print('No function calls, agent finished')
      break

    tool_results = []
    for fc in function_calls:
      print(f'  Tool: {fc.name}({dict(fc.args)})')
      result = execute_tool(fc.name, dict(fc.args))

      if result.startswith('TASK_COMPLETE:'):
        print(f'Agent completed: {result}')
        return result

      result_preview = result[:200] + '...' if len(result) > 200 else result
      print(f'  Result: {result_preview}')

      tool_results.append(
          types.Part(function_response=types.FunctionResponse(
              name=fc.name,
              response={'result': result},
          )))

    messages.append(types.Content(role='user', parts=tool_results))

  return 'Agent reached max iterations without completing'


def main() -> None:
  """Main entry point."""
  ap = argparse.ArgumentParser()
  ap.add_argument('--issue-json', required=True)
  ap.add_argument('--issue-comments-json', required=True)
  ap.add_argument('--max-iterations', type=int, default=MAX_ITERATIONS)
  args = ap.parse_args()

  max_iter = args.max_iterations

  with open(args.issue_json, 'r', encoding='utf-8') as f:
    issue = json.load(f)
  with open(args.issue_comments_json, 'r', encoding='utf-8') as f:
    comments = json.load(f)

  title = issue.get('title', '')
  body = issue.get('body', '') or ''
  comment_lines = []
  for c in comments:
    user = c.get('user', {}).get('login', 'unknown')
    body_text = c.get('body', '')
    comment_lines.append(f'**{user}**: {body_text}')
  comments_text = '\n\n'.join(comment_lines)

  issue_context = f'''# GitHub Issue to Solve

## Title
{title}

## Description
{body}

## Comments
{comments_text if comments_text else '(no comments)'}

---

Please solve this issue. Start by exploring the codebase with list_dir and
read_file, then make the necessary changes with write_file, and verify with
run_shell("pytest"). Call done() when complete.
'''

  project = os.environ['GOOGLE_CLOUD_PROJECT']
  location = os.environ['GOOGLE_CLOUD_LOCATION']

  client = genai.Client(vertexai=True, project=project, location=location)

  print('Starting Gemini agent...')
  print(f'Issue: {title}')
  print(f'Max iterations: {max_iter}')
  print('---')

  result = run_agent(client, issue_context, max_iter)
  print('---')
  print(f'Final result: {result}')


if __name__ == '__main__':
  main()
