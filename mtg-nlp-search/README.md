# MTG Natural Language Search

This app uses OpenAI + Scryfall API to let you find Magic: The Gathering cards via natural language queries.

## Example Prompt

> "I want a 2 mana instant that creates tokens and counters a spell"

## Setup

1. Add your OpenAI API key to `.env`
2. Run locally with:

```
uvicorn app.main:app --reload
```

## Deploy on Render

Push this repo to GitHub and connect it to [Render](https://render.com).