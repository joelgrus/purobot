# Purobot

Purobot is a small Python agent framework for a meetup talk. It uses a real OpenRouter model, a generic browser tool, drop-in Markdown commands, and a fake B-E-H storefront you can point it at explicitly.

## Slides

I built this for a talk at the Alamo Python meetup in April 2026.

The slides for the talk are [here](https://docs.google.com/presentation/d/1oERg-NhjfDZCth6ALQrZ03bXx6Ede0NjxMPuBWNVZkI/edit?usp=sharing)

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

Install browser support first:

```bash
uv sync
uv run playwright install chromium
```

## Environment

Required:

```bash
export OPENROUTER_API_KEY=...
```

Optional:

```bash
export PUROBOT_MAX_HISTORY_MESSAGES=100
export TELEGRAM_BOT_TOKEN=...
export TELEGRAM_CHAT_ID=...
```

What they do:

- `OPENROUTER_API_KEY`: required for all model calls
- `PUROBOT_MAX_HISTORY_MESSAGES`: keep only the last `N` session messages, default `100`
- `TELEGRAM_BOT_TOKEN`: required only if you use `--telegram`
- `TELEGRAM_CHAT_ID`: optional Telegram allowlist for your personal chat

## Local Run

Use OpenRouter through the official `openai` client:

```bash
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

## Telegram Setup

1. In Telegram, message `@BotFather`.
2. Run `/newbot`.
3. Pick a bot name and username.
4. Copy the bot token BotFather gives you.
5. Export it locally:

```bash
export TELEGRAM_BOT_TOKEN=...
```

6. Start a chat with your bot from your phone and send it a message like `hello`.
7. Verify the token works:

```bash
curl "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/getMe"
```

8. Fetch your chat ID:

```bash
curl "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/getUpdates"
```

9. Look for:

```json
"chat":{"id":123456789,...}
```

10. Export that value if you want to restrict the bot to just your chat:

```bash
export TELEGRAM_CHAT_ID=123456789
```

11. Run Purobot with Telegram enabled:

```bash
uv run python -m purobot.cli --telegram --show-browser
```

Telegram messages will show up in the terminal, and browser actions will still run locally on your laptop.

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
