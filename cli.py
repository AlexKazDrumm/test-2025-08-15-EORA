import argparse
import asyncio
from pathlib import Path

from app.ingest import ingest_urls
from app.rag import answer
from app.config import settings
from app.links import load_links_from_file, resolve_links


def cmd_ingest(args):
    urls = None
    if args.file:
        urls = load_links_from_file(args.file)
    elif args.urls:
        urls = args.urls
    else:
        urls = resolve_links()

    asyncio.run(ingest_urls(urls))


def cmd_ask(args):
    txt, srcs = answer(args.q, args.mode, args.top_k)
    if args.out_md:
        out = Path(args.out_md)
        out.write_text(txt, encoding="utf-8")
        print(f"\n[Saved Markdown to] {out.resolve()}")
    print("\n=== ANSWER ===\n")
    print(txt)
    if srcs:
        print("\n=== SOURCES ===")
        for i, u in enumerate(srcs, 1):
            print(f"[{i}] {u}")


def main():
    p = argparse.ArgumentParser(description="EORA RAG CLI")
    sub = p.add_subparsers()

    p_ing = sub.add_parser("ingest", help="Index seed links / file / custom URLs")
    p_ing.add_argument("--file", help="Path to links.txt (one URL per line, lines starting with # ignored)")
    p_ing.add_argument("--urls", nargs="*", help="Override URLs (space-separated)")
    p_ing.set_defaults(func=cmd_ingest)

    p_ask = sub.add_parser("ask", help="Ask a question")
    p_ask.add_argument("-q", required=True, help="Question")
    p_ask.add_argument("--mode", choices=["simple", "sources", "inline", "extractive"], default="inline")
    p_ask.add_argument("--top-k", type=int, default=None)
    p_ask.add_argument("--out-md", help="Save answer as Markdown file")
    p_ask.set_defaults(func=cmd_ask)

    args = p.parse_args()
    if hasattr(args, "func"):
        args.func(args)
    else:
        p.print_help()


if __name__ == "__main__":
    main()
