# ARGUS

**Analytical Reasoning and Grounded Understanding System**

[![Last Commit](https://img.shields.io/github/last-commit/itsactuallyluna9/ARGUS)](https://github.com/itsactuallyluna9/ARGUS/commits/main)
[![License](https://img.shields.io/github/license/itsactuallyluna9/ARGUS)](https://github.com/itsactuallyluna9/ARGUS/blob/main/LICENSE)
[![Python](https://img.shields.io/badge/python-3.x-blue)](https://www.python.org/)
[![React](https://img.shields.io/badge/react-18.x-61DAFB?logo=react&logoColor=black)](https://react.dev/)
[![Flask](https://img.shields.io/badge/flask-3.x-black?logo=flask)](https://flask.palletsprojects.com/)
![Cornell College Computer Science Capstone](https://img.shields.io/badge/Cornell%20College%20Computer%20Science%20Capstone-8A2BE2)
![Trans Rights](https://pride-badges.pony.workers.dev/static/v1?label=trans%20rights&stripeWidth=6&stripeColors=5BCEFA,F5A9B8,FFFFFF,F5A9B8,5BCEFA)

ARGUS is an open-source, LLM-powered fact-checking application for web articles. Developed as a open source alternative to ChatGPT Deep Research or Grok that can run on consumer hardware. Paste in a URL and ARGUS searches the web for reliable sources, cross-references the article's claims, evaluates reporting bias, and produces a cited summary report.

> Developed as a capstone project at Cornell College.

## Demo

> To be added!

## Features

* **Article Summary** - extracts and summarizes the articles main points
* **Accuracy Evaluation** - cross-references article claims against web sources
* **Completeness Evaluation** - compares reporting against other articles on the same topic to identify what was left out
* **Bias Evaluation** - scores political bias, sensationalism, and emotional language to help identify misleading reporting
* **Progressive Loading** - results populate as each agent finishes; no waiting for the entire pipelines
* **Data Sandbox** - explore trends that ARGUS has discovered using either built-in plots or via custom R scripts, all in the browser, powered by ggplot2 and WebR
* **Mobile Support** - responsive design for use on any device
* **Webhook Notifications** - get notified when a long running analysis completes
* **OpenAI Compatible** - use any OpenAI compatible endpoint - such as Ollama, LlamaCPP, or vLLM

## Architecture

ARGUS is built on top of a Flask web server which processes user requests, routes LLM prompts to all available endpoints, collects, formats, and returns results. The elegant React-native frontend integrates seamlessly to provide a streamlined and comfortable user experience. OpenAI compatible endpoints must be provided, with their routes being configured in the `config.toml` file. LLM requests are routed based on model name and context length, with the system doing its best to balance the load when possible. Additionally, the system runs and accesses a local ChromaDB database, allowing the system to cache article summaries and past fact checks, so that the system can reference that information without having to search the internet again.

## Getting Started

### Prerequsities
- uv (Python package manager)
- Node.js
- OpenAI Compatible Runner - such as Ollama or LlamaCPP

### Installation

```bash
git clone https://github.com/itsactuallyluna9/ARGUS.git
cd ARGUS

uv sync
uv run playwright install # needed for scraping

cd frontend
npm install
cd ..
```

### Running ARGUS (Development)
```bash
# Chroma HTTP Server (if needed)
uv run chroma-server-wrapper.py

# Flask
uv run argus

# Vite
cd frontend && npm run dev
```

The server will be accessible at http://localhost:5173.

### Running ARGUS (Production)

Flask is configured to serve static build files from Vite, if they exist.

```bash
cd frontend && npm run build && cd ..

# Chroma HTTP Server (if needed)
uv run chroma-server-wrapper.py

# Flask
uv run argus
```

The server will be accessible at http://localhost:5000.

> [!NOTE]
> `chroma-server-wrapper.py` spawns a Chroma HTTP server using `chroma run`, but has the ability to be interrupted with <kbd>Ctrl</kbd> + <kbd>C</kbd>.

## Configuration

> [!TIP]
> Refer to `config.toml.sample` for a sample configuration file, with all options.

You will need to create a configuration file (named `config.toml`) in the project's root directory before starting. In this, you'll need to set the `host`, `port`, and where ARGUS should find models.

### Models

Each agent can be configured with a model, with the defaults being `nemotron-3-nano:4b` for the summarizer and `glm-4.7-flash` for the accuracy, bias, and completeness agents. A route for *each* model will need to be present in the `model_routes` section of the config.

You will need to provide your own OpenAI-compatible endpoints. Please see the [Ollama](), [llama.cpp](), or your provider's documentation for details.

### ChromaDB

The default config starts ChromaDB in memory. You will want to change this to either `persistent` or `http` and set `path` or `url` to ensure the data ARGUS collects remains persistent.

## Usage

1. Find an article you'd like to fact check, and copy the link.
2. Go to the main home page, paste the link in, and hit the button to start!
3. Wait. Fact checks will take a bit, depending on the hardware available. You can leave the page and come back to it later.
4. Browse the results!

### Webhooks

ARGUS offers webhook notification support, with first-class support being offered for [Discord](https://discord.com), [Slack](https://slack.com), and [ntfy.sh](https://ntfy.sh). In all other cases, it posts a JSON dictionary, the details of which can be found in [Using Webhooks](docs/webhooks.md).

To use webhooks, create a webhook (using your favorite service), and add it to the configuration file. ARGUS will, upon completion of a fact check, call the webhook.

ARGUS also supports receiving URLs to check programmatically, please see [Using Webhooks](docs/webhooks.md) for further details and a sample bookmarklet.

> [!WARNING]
> ARGUS currently has no rate limits, and no queue system. The system can be overloaded *very* easily.

### Auto-Roam

Auto-Roam is a debug feature that will, when the system is idle, automatically start fact checks from either [Google News]() or a random previously-seen article.

1. Go to the debug page, by enabling `DEV_MODE` in `App.tsx` and going to `<base_url>/debug`.
2. Click `Start Auto-Roam`.
3. Wait. You will need to 

## Data Sandbox

The Data Sandbox is a way to view all of the data that ARGUS has compiled. It's recommended to run a few fact checks before doing any serious investigation.

The sandbox has either premade plots, the data of which will be updated approximately every 24 hours. All plots will be generated on the user's device, and can be filtered based on time and the originating source.

The advanced data sandbox surfaces a R-Studio like interface, where the users can experiment with ARGUS's data, in their browser. All scripts are run on-device. The script for the basic sandbox is loaded, for reference. Additionally, the user can download the generated data as `csv` files to their device, for further processing and analysis.

Please see the [Advanced Data Sandbox Guide]() and [Data Format]() for further details.

## Future Improvements

* User Accounts
  * Per-User Notifications
  * *This also includes some form of rate-limiting.*
* Dynamic Context Cleaning / Session Compaction
  * *This is like Claude Code (or most AI coding agents), where old tool calls are automatically discarded, to save space. Additionally, when the token count reaches some length, the session is compacted (summarized), in order to not exceed the max token count.*
* More Data Visualizations
  * *One we had in mind was a network graph, which demonstrates how articles are connected with each other, as cited as a source.*
* Trend Analysis
  * *How reliable is a source? Is reporting getting better on a topic?*
* General Stability and Performance
  * *We currently have about a 75% success rate, and getting that higher would be nice. Additionally, having a better internal queue system would help the system not get overloaded quite as easily.*

## Credits

* Luna (@itsactuallyluna9) - Frontend, Scraper, Benchmarking v2
* Willow (@willowdennison) - Agents, Prompt Engineering, Routing, Benchmarking v1

### Special Thanks

* Cornell College Computer Science Department - GPU Node

