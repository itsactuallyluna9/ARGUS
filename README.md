# ARGUS

**Analytical Reasoning and Grounded Understanding System**

[![Last Commit](https://img.shields.io/github/last-commit/itsactuallyluna9/ARGUS)](https://github.com/itsactuallyluna9/ARGUS/commits/main)
[![License](https://img.shields.io/github/license/itsactuallyluna9/ARGUS)](https://github.com/itsactuallyluna9/ARGUS/blob/main/LICENSE)
[![Python](https://img.shields.io/badge/python-3.x-blue)](https://www.python.org/)
[![React](https://img.shields.io/badge/react-18.x-61DAFB?logo=react&logoColor=black)](https://react.dev/)
[![Flask](https://img.shields.io/badge/flask-3.x-black?logo=flask)](https://flask.palletsprojects.com/)
![Cornell College Computer Science Capstone](https://img.shields.io/badge/Cornell%20College%20Computer%20Science%20Capstone-8A2BE2)
![Trans Rights](https://pride-badges.pony.workers.dev/static/v1?label=trans%20rights&stripeWidth=6&stripeColors=5BCEFA,F5A9B8,FFFFFF,F5A9B8,5BCEFA)

ARGUS is an open-source, LLM-powered fact-checking application for web articles. Developed as a open source altertanive to ChatGPT Deep Research or Grok, that can run on consumer hardware. Paste in a URL and ARGUS searches the web for reliable sources, cross-references the article's claims, evaluates reporting bias, and produces a cited summary report.

> Developed as a capstone project at Cornell College.

## Demo

> To be added!

## Features

* **Article Summary** - extracts and summarizes the articles main points
* **Accuracy Evaluation** - cross-references article claims against web sorces
* **Completeness Evaluation** - compares reporting against other articles on the same topic to identify what was left out
* **Bias Evaluation** - scores political bias, sensationalism, and emotional language to help identify misleading reporting
* **Progressive Loading** - results populate as each agent finishes; no waiting for the entire pipelines
* **Data Sandbox** - explore trends that ARGUS has discovered using either built-in plots or via custom R scripts, all in the browser, powered by ggplot2 and WebR
* **Mobile Support** - responsive design for use on any device
* **Webhook Notifications** - get notified when a long running analysis completes
* **OpenAI Compatable** - use any OpenAI compatable endpoint - such as Ollama, LlamaCPP, or vLLM

## Architecture

## Getting Started

### Prerequsities
- uv (Python package manager)
- Node.js
- OpenAI Compatable Runner - such as Ollama or LlamaCPP

### Installation

```bash
git clone https://github.com/itsactuallyluna9/ARGUS.git
cd ARGUS

uv sync

cd frontend
npm install
cd ..
```

### Running ARGUS
```bash
```

## Usage

TODO

## Configuration

## Data Sandbox

## Future Improvements

## Credits

### Special Thanks

