"""Interactive CLI tester for the local GGUF model."""
import asyncio
import sys
from backend.engine.local_gguf_provider import LocalGgufLlmProvider
from backend.config.settings import app_settings


async def run_interactive_session() -> None:
    """Run interactive REPL loop using input() with the local GGUF LLM."""
    print("=" * 60)
    print(" Bureau of Indian Standards (BIS) - Local GGUF Assistant")
    print(f" Model Path : {app_settings.llm.model_path}")
    print(f" Context    : {app_settings.llm.n_ctx} | Threads: {app_settings.llm.n_threads}")
    print(" Type your query and press Enter. Type 'exit' or 'quit' to stop.")
    print("=" * 60)

    # Initialize provider using project configuration
    provider = LocalGgufLlmProvider(
        model_path=app_settings.llm.model_path,
        n_ctx=app_settings.llm.n_ctx,
        n_threads=app_settings.llm.n_threads,
    )

    system_prompt = (
        "You are an expert technical advisor specializing in Indian Standards (IS), "
        "Bureau of Indian Standards (BIS) compliance, and GeM e-procurement specifications."
    )

    while True:
        try:
            user_query = input("\n[You] > ").strip()
            if not user_query:
                continue
            if user_query.lower() in ("exit", "quit", "q"):
                print("\nExiting interactive session.")
                break

            print("\n[AI Assistant Thinking...]")
            response = await provider.generate_text(
                prompt=user_query,
                system_prompt=system_prompt,
            )
            print(f"\n[AI Assistant]:\n{response}\n")
            print("-" * 60)

        except (KeyboardInterrupt, EOFError):
            print("\nSession interrupted. Exiting.")
            break
        except Exception as exc:
            print(f"\n[Error]: {type(exc).__name__}: {exc}")


if __name__ == "__main__":
    asyncio.run(run_interactive_session()) #d:\CODE\Hackathon\.venv\Scripts\python.exe interactive_llm.py