from typing import List
from dotenv import load_dotenv
from typer import Typer
from rich.console import Console
import typer

from giraffes_can_speak.openai.embeddings import create_embeddings
from giraffes_can_speak.pinecone.db_ops import query_embeddings, upsert_embeddings
from giraffes_can_speak.youtube.transcript_availability import (
    analyze_channel_transcripts,
    get_channel_id_from_handle,
)
from giraffes_can_speak.youtube.youtube import (
    get_transcript_from_video_id,
    get_transcript_from_video_id_raw,
)

app = Typer()
console = Console()

load_dotenv()


@app.command()
def hello():
    print("Hello, World!")


@app.command()
def get_channel_id(handle: str):
    console.print("Getting channel ID for handle: [bold cyan]{handle}[/bold cyan]")
    channel_id = get_channel_id_from_handle(handle)
    console.print(f"Channel ID: [bold cyan]{channel_id}[/bold cyan]")


@app.command()
def put_transcript_in_db(video_id: str):
    transcript = get_transcript_from_video_id(video_id)
    console.print(
        f"Got transcript (length): [bold cyan]{transcript.video_info}[/bold cyan]"
    )
    embedding = create_embeddings(transcript)
    console.print(
        f"Got embedding (length): [bold cyan]{embedding.video_info}[/bold cyan]"
    )
    upsert_embeddings(embedding)


@app.command()
def get_transcript(
    video_id: str,
    output_file: str = typer.Option(None, "--output", "-o", help="Output file path"),
    raw: bool = typer.Option(False, "--raw", "-r", help="Output raw transcript"),
):
    if raw:
        transcript = get_transcript_from_video_id_raw(video_id)
        console.out(transcript)
        return

    console.print(f"Getting transcript for video ID: [bold cyan]{video_id}[/bold cyan]")

    transcript = get_transcript_from_video_id(video_id)
    console.print(f"Got transcript: [bold cyan]{transcript}[/bold cyan]")
    print(transcript.video_info)


@app.command()
def analyze_transcripts(channel_id: str):
    console.print(
        "Analyzing transcripts for channel ID: [bold cyan]{channel_id}[/bold cyan]"
    )
    analyze_channel_transcripts(channel_id)


@app.command()
def discord_demo(question: str):
    from giraffes_can_speak.config import clients
    from giraffes_can_speak.prompts.prompts import (
        team_house_system_prompt,
        team_house_user_prompt,
    )

    openai = clients.openai

    # Get the embedding for the question
    emb_model = "text-embedding-3-small"
    response = openai.embeddings.create(input=[question], model=emb_model)
    question_embedding = response.data[0].embedding

    # Query Pinecone
    results = query_embeddings(question_embedding)
    context = "\n".join([result["metadata"]["text"] for result in results["matches"]])

    # Get completion from OpenAI
    response = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": team_house_system_prompt.format(context=context),
            },
            {
                "role": "user",
                "content": team_house_user_prompt.format(user_query=question),
            },
        ],
        max_tokens=400,
        n=1,
        stop=None,
        temperature=0.7,
    )

    # Extract and print the answer
    answer = response.choices[0].message.content
    typer.echo(f"Question: {question}")
    typer.echo(f"Answer: {answer}")


@app.command()
def process_list(
    items: List[str] = typer.Argument(None, help="List of items to process"),
    use_stdin: bool = typer.Option(
        False, "--stdin", "-s", help="Read items from stdin"
    ),
):
    if use_stdin:
        # Read items from stdin
        import sys

        items = [line.strip() for line in sys.stdin]
    elif not items:
        console.print(
            "[bold red]Error:[/bold red] No items provided. Use arguments or --stdin option."
        )
        raise typer.Exit(code=1)

    console.print(f"Processing {len(items)} items:")
    for item in items:
        console.print(f"- [cyan]{item}[/cyan]")


if __name__ == "__main__":
    app()
