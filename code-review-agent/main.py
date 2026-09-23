import click
import json
from anthropic import Anthropic
from schema import ReviewResult
from diff_utils import get_diff

client = Anthropic()

SYSTEM_PROMPT = """You are a code reviewer. You will be given a git diff.
Review it for bugs, security issues, and significant style problems.
Do not comment on trivial nits unless asked.
Respond ONLY with valid JSON matching this schema, no other text:
{
  "findings": [
    {"file": "...", "line": 0, "severity": "blocker|suggestion|nit",
     "category": "bug|security|style|performance", "message": "..."}
  ],
  "summary": "..."
}
If there are no issues, return an empty findings list and a brief summary."""

def review_diff(diff_text: str) -> ReviewResult:
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": diff_text}]
    )
    raw_text = response.content[0].text
    # strip markdown fences if the model adds them
    cleaned = raw_text.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    data = json.loads(cleaned)
    return ReviewResult(**data)

@click.command()
@click.option("--repo", default=".", help="Path to git repo")
@click.option("--range", "range_spec", default=None, help="e.g. main..HEAD")
def cli(repo, range_spec):
    diff_text = get_diff(repo, range_spec)
    if not diff_text.strip():
        click.echo("No changes to review.")
        return

    result = review_diff(diff_text)

    for f in result.findings:
        click.echo(f"[{f.severity.upper()}] {f.file}:{f.line} ({f.category})")
        click.echo(f"  {f.message}\n")

    click.echo(f"Summary: {result.summary}")

if __name__ == "__main__":
    cli()