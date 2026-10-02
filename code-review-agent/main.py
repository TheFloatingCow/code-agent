import click
import json
from anthropic import Anthropic
from schema import ReviewResult
from diff_utils import get_diff
from tools import TOOLS, run_tool

client = Anthropic()
MAX_STEPS = 10

SYSTEM_PROMPT = """You are a code reviewer. You will be given a git diff.
Review it for bugs, security issues, and significant style problems.
Do not comment on trivial nits unless asked.
You have tools: read_file, search_repo, and run_tests.
Use read_file and search_repo to check surrounding code, function definitions,
and usages before flagging an issue.
Use run_tests when test results would help verify a suspected bug.
Passing tests do not prove the changed code is correct, because the relevant
behavior may not be covered by tests.
Your final message must be only the JSON.
Respond ONLY with valid JSON matching this schema, no other text:
{
  "findings": [
    {"file": "...", "line": 0, "severity": "blocker|suggestion|nit",
     "category": "bug|security|style|performance", "message": "..."}
  ],
  "summary": "..."
}
If there are no issues, return an empty findings list and a brief summary."""

def extract_review_json(raw_text: str) -> dict:
    decoder = json.JSONDecoder()
    matches = []

    for i, char in enumerate(raw_text):
        if char != "{":
            continue

        try:
            data, _ = decoder.raw_decode(raw_text[i:])
        except json.JSONDecodeError:
            continue

        if (
            isinstance(data, dict)
            and "findings" in data
            and "summary" in data
        ):
            matches.append(data)

    if matches:
        return matches[-1]

    raise RuntimeError(
        f"Model returned no valid review JSON:\n{raw_text}"
    )

def review_diff(diff_text: str, repo: str) -> ReviewResult:
    messages = [{"role": "user", "content": diff_text}]
    for _ in range(MAX_STEPS):
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=4000,
            system=SYSTEM_PROMPT,
            tools=TOOLS,
            messages=messages,
        )
        if response.stop_reason != "tool_use":
            break
        messages.append({"role": "assistant", "content": response.content})
        results = []
        for block in response.content:
            if block.type == "tool_use":
                click.echo(f"tool: {block.name} {block.input}", err=True)
                output = run_tool(repo, block.name, block.input)
                results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": output,
                })
        messages.append({"role": "user", "content": results})
    else:
        raise RuntimeError("Hit step limit without a final answer")
    
    text_blocks = [
        b.text
        for b in response.content
        if b.type == "text" and b.text.strip()
    ]

    if not text_blocks:
        raise RuntimeError(
            f"Model returned no final text. Stop reason: {response.stop_reason}"
        )

    raw_text = "\n".join(text_blocks)

    data = extract_review_json(raw_text)

    return ReviewResult(**data)

@click.command()
@click.option("--repo", default=".", help="Path to git repo")
@click.option("--range", "range_spec", default=None, help="e.g. main..HEAD")
def cli(repo, range_spec):
    diff_text = get_diff(repo, range_spec)
    if not diff_text.strip():
        click.echo("No changes to review.")
        return

    result = review_diff(diff_text, repo)

    for f in result.findings:
        click.echo(f"[{f.severity.upper()}] {f.file}:{f.line} ({f.category})")
        click.echo(f"  {f.message}\n")

    click.echo(f"Summary: {result.summary}")

if __name__ == "__main__":
    cli()