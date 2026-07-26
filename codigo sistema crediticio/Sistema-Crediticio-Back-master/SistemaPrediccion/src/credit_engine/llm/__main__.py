"""Console runner for testing the LLM module interactively.

Usage::

    python -m credit_engine.llm -n "Carlos" -p "Crédito Libre Inversión" \\
        -b "Tasa 1.2%, sin codeudor, aprobación 24h" -c whatsapp

    python -m credit_engine.llm  # interactive mode — prompts for each input
"""

from __future__ import annotations

import argparse
import sys

from credit_engine.llm import (
    CHANNEL_WRAPPERS,
    LLMClientError,
    MessageGenerator,
    OllamaClient,
)
from credit_engine.llm.generator import Channel


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate a personalised message using the LLM",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "examples:\n"
            '  python -m credit_engine.llm -n Carlos -p "Crédito Libre" '
            '-b "Tasa 1.2%%, sin codeudor" -c whatsapp\n'
            "  python -m credit_engine.llm                              # interactive mode"
        ),
    )
    parser.add_argument("-n", "--name", help="Person's name")
    parser.add_argument("-p", "--product", help="Product / credit name")
    parser.add_argument("-b", "--benefits", help="Product benefits (comma-separated)")
    parser.add_argument(
        "-c",
        "--channel",
        choices=list(CHANNEL_WRAPPERS),
        default="whatsapp",
        help="Communication channel (default: whatsapp)",
    )
    parser.add_argument(
        "--endpoint",
        default=None,
        help="Ollama base URL (default: $LLM_BASE_URL or http://localhost:12434)",
    )
    parser.add_argument(
        "--model",
        default=None,
        help="Model identifier (default: $LLM_MODEL or docker.io/ai/qwen2.5:latest)",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=30.0,
        help="Request timeout in seconds (default: 30)",
    )
    parser.add_argument(
        "--raw",
        action="store_true",
        help="Print raw LLM output without cleaning",
    )

    args = parser.parse_args()

    name: str = args.name or _prompt("Nombre de la persona")
    product: str = args.product or _prompt("Nombre del producto / crédito")
    benefits: str = args.benefits or _prompt("Beneficios del producto")
    channel: Channel = args.channel

    if not name.strip() or not product.strip():
        parser.error("--name and --product are required (or use interactive mode)")

    client = OllamaClient(
        base_url=args.endpoint,
        model=args.model,
        timeout=args.timeout,
    )
    generator = MessageGenerator(client)

    try:
        message: str = generator.generate_message(name, product, benefits, channel)
        print(f"\n{'─' * 50}")
        print(f"Canal: {channel}")
        print(f"Producto: {product}")
        print(f"Beneficios: {benefits}")
        print(f"{'─' * 50}")
        print(f"\n{message}\n")
    except LLMClientError as exc:
        print(f"\nError: {exc}\n", file=sys.stderr)
        sys.exit(1)


def _prompt(label: str) -> str:
    """Read a line from stdin, stripping trailing whitespace."""
    try:
        return input(f"{label}: ").strip()
    except (KeyboardInterrupt, EOFError):
        print()
        sys.exit(0)


if __name__ == "__main__":
    main()
