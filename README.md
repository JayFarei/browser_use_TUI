# Browser Agent Demo

A simple demonstration of a browser automation agent.

## Setup

1. Create a `.env` file with your secrets:
```
OPENAI_API_KEY=your_openai_key
BROWSERLESS_API_KEY=your_browserless_key
```

## Commands

Use the following make commands to manage the project:

- `make` - Creates environment, installs dependencies, and runs the agent
- `make venv` - Sets up virtual environment and installs dependencies
- `make run` - Ensures venv is set up and runs the agent
- `make clean` - Removes the virtual environment 