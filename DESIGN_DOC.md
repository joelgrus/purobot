# Purobot Design Doc

## Purpose

Purobot is a small Python agent framework for an AI + Python meetup talk.

The goal is not to build a huge agent platform. The goal is to build a system that is:

- easy to explain on stage
- credible to Python developers
- small enough to understand quickly
- capable of one strong end-to-end demo

The current demo story is:

`phone or keyboard -> Purobot -> browser automation on laptop -> fake local B-E-H store`

## What Purobot Is

Purobot is a local Python app with:

- one agent loop
- one real model backend through OpenRouter
- one generic browser tool powered by Playwright
- one shared session
- multiple channels into that same session
- optional Markdown commands for demo-specific behavior

It is intentionally synchronous and simple.

## Current Product Shape

The current runtime has two user-facing channels:

- console
- Telegram

Both channels can drive the same assistant session on the laptop. That means:

- messages typed in the terminal and messages sent from Telegram both hit the same loop
- the browser always runs locally on the laptop
- Telegram is only a chat surface, not a remote execution environment

## Core Architecture

### App

`purobot/app.py` owns the top-level assembled system:

- one `Agent`
- one `Session`
- one lock around the shared loop

The lock exists so console and Telegram do not step on each other while the agent is mid-turn.

### Session

`Session` stores:

- plain message history as dicts
- one active command context when a slash command is running
- one pending approval
- small transient browser state

There is no long-term memory layer.

### Agent

`Agent` runs a direct tool loop:

1. append the user message
2. ask the model for the next action
3. if the model returns text, emit it
4. if the model returns a tool call, execute it or request approval
5. append tool results and continue

Dangerous actions are handled directly in the agent, not through a separate policy framework.

### Model

`OpenRouterModel` is intentionally thin:

- build chat-completions messages
- call the OpenAI Python client against OpenRouter
- return either text or a tool call

The system prompt is generic. It tells the model:

- browser use is for explicit browsing/site interaction
- ordinary knowledge requests should be answered directly when possible
- dangerous browser actions must be marked with `dangerous=true`

### Tooling

The main tool is `BrowserTool`.

It supports:

- `open`
- `click`
- `type`
- `read`
- `wait`

It is a generic browser tool, not a grocery-specific tool.

The browser tool should only be used when the user explicitly wants site interaction or when live page interaction is actually necessary.

### Commands

Commands are optional extensions invoked through slash syntax.

They are loaded from:

- `commands/<name>.md`

Commands are not Python plugin functions. They are Markdown instruction files that become temporary command context for a single run.

Example:

- `/alliteration-recipe b`

This loads `commands/alliteration-recipe.md`, passes the command arguments into prompt context, and runs that command through the normal model and tool loop.

## Demo Website

The grocery site is a fake local storefront under:

- `demo/beh_store/`

It is not served by Purobot itself. The user serves it separately, typically with:

```bash
cd demo/beh_store
python -m http.server 8888
```

Purobot does not know about that site unless the user explicitly tells it to use:

- `http://localhost:8888`

That is an intentional design choice. It keeps the base assistant generic.

## Approval Model

Irreversible browser actions require approval.

In practice:

- the model marks a browser action as `dangerous=true`
- the agent pauses
- the user replies `approve` or `reject`
- the action runs only after approval

Approval prompts are human-readable and describe the pending browser action, for example:

- opening a URL
- clicking a selector
- typing into a field

## Design Principles

### 1. Glue code, not architecture

Purobot prefers direct code over frameworks and abstractions.

That means:

- plain dict messages
- a thin model wrapper
- one obvious browser tool
- minimal indirection

### 2. General core, explicit user intent

The assistant should not silently enter “grocery mode.”

If the user wants shopping behavior, they should explicitly ask to use a site such as:

- `Use http://localhost:8888 to shop for these ingredients`

### 3. Demo-friendly behavior matters

The system should be understandable while projected live.

This is why:

- console output is readable
- Telegram traffic is mirrored into the terminal
- commands are explicit and easy to demo
- approval messages are explicit

### 4. Keep the dependency surface small

Current core dependencies are:

- `openai`
- `playwright`

Telegram is implemented with the Python standard library against the Telegram Bot HTTP API.

## Current Package Shape

```text
purobot/
  app.py
  cli.py
  config.py
  channels/
    console.py
    telegram.py
    whatsapp.py
  core/
    agent.py
    model.py
    session.py
  commands/
    loader.py
  tools/
    base.py
    browser.py
commands/
  alliteration-recipe.md
demo/
  beh_store/
```

## Non-Goals

Currently out of scope:

- long-term memory
- vector databases
- multi-agent orchestration
- plugin frameworks
- server-side hosting of the demo store
- broad browser generality beyond the demo needs
- fully featured multi-user bot semantics

## Current Demo Path

Recommended talk flow:

1. run Purobot on the laptop
2. optionally enable Telegram
3. serve the local B-E-H site on `localhost:8888`
4. tell Purobot explicitly to use that site
5. watch the browser automation on the laptop
6. show approval before final submission

This gives a clear story:

- real model
- real browser tool
- real phone integration
- explicit human approval
- optional behavioral specialization through dropped-in Markdown commands
