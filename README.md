# Purobot

Purobot is a small Python agent framework for a meetup talk. It uses a real OpenRouter model, a generic browser tool, drop-in Markdown commands, and a fake B-E-H storefront you can point it at explicitly.

## Current scope

This repository currently includes:

- a synchronous console channel
- a minimal agent loop
- an OpenRouter-backed LLM adapter
- a Playwright-backed browser tool with action-level approval policy
- an optional Telegram polling channel that shares the same session as the console
- drop-in Markdown commands under `commands/`
- a richer fake grocery site at `demo/beh_store/` for local iteration and live demos

## Run

```bash
uv run python -m purobot.cli
```

Install browser support first:

```bash
uv sync
uv run playwright install chromium
```

Use OpenRouter through the official `openai` client:

```bash
export OPENROUTER_API_KEY=...
uv run python -m purobot.cli
```

The default model is `google/gemini-3-flash-preview`. Override it with `--model ...` if needed.

Allow dangerous browser actions:

```bash
uv run python -m purobot.cli --allow-dangerous-browser-actions
```

Watch the site in a visible browser window:

```bash
uv run python -m purobot.cli --show-browser
```

Enable Telegram on the same laptop session:

```bash
export TELEGRAM_BOT_TOKEN=...
uv run python -m purobot.cli --telegram --show-browser
```

Optionally lock it to your personal chat:

```bash
export TELEGRAM_CHAT_ID=...
```

List available commands:

```bash
 /commands
```

Example command:

```bash
/alliteration-recipe b
```

Serve the demo store yourself when you want shopping behavior:

```bash
cd demo/beh_store
python -m http.server 8888
```

## Example

```text
Use http://localhost:8888 to shop for pasta tonight with 1 lb spaghetti, 2 cloves garlic, olive oil, parmesan, and basil
```

The current implementation is intentionally simple. The model will not know about the store unless you explicitly tell it which URL to use. Commands are loaded from Markdown files so new command behavior can be added without changing the core loop.
