# ARGUS Benchmarking

This document covers the methodology for benchmarking models for use in ARGUS, as well as recorded results across hardware tiers. There are two distinct phases: controlled model benchmarks (which are isolated and reproducible) and pipeline benchmarks (which are full end-to-end tests).

## Hardware

### Laptop A

### Laptop B

| Component   | Spec                                          |
| ----------- | --------------------------------------------- |
| CPU         | Apple M1 Max (8 Performance and 2 Efficiency) |
| GPU         | Apple M1 Max (32 Core GPU)                    |
| Unified RAM | 32 GB LPDDR5                                  |
| Storage     | Internal SSD                                  |
| OS          | macOS Tahoe 26.3.1                            |

### Desktop A

| Component | Spec                                                 |
| --------- | ---------------------------------------------------- |
| CPU       | 12th Gen Intel(R) Core(TM) i5-12600K (16) @ 4.90 GHz |
| RAM       | 32 GB LPDDR5                                         |
| GPU       | EVGA NVIDIA GeForce RTX 3070 Ti                      |
| VRAM      | 8 GB GDDR6X                                          |
| Storage   | NVMe SSD                                             |
| OS        | Arch Linux (6.19.10-arch1-1)                         |

### Desktop B

| Component | Spec                                     |
| --------- | ---------------------------------------- |
| CPU       | 16 x AMD EPYC 7232P 8-Core Processor     |
| RAM       | 64 GB LPDDR5                             |
| GPU       | NVIDIA A2                                |
| VRAM      | 16 GB GDDR6                              |
| Storage   | HDD                                      |
| OS        | Ubuntu Server 24.04.4 LTS (Noble Numbat) |

### Server

| Component | Spec                                     |
| --------- | ---------------------------------------- |
| CPU       | 16 x AMD EPYC 7232P 8-Core Processor     |
| RAM       | 64 GB LPDDR5                             |
| GPU       | NVIDIA A2                                |
| VRAM      | 16 GB GDDR6                              |
| Storage   | HDD                                      |
| OS        | Ubuntu Server 24.04.4 LTS (Noble Numbat) |

## Models

| Name                                                            | Thinking | Tools | Size   | Notes |
| --------------------------------------------------------------- | -------- | ----- | ------ | ----- |
| deepseek-r1:14b                                                 | Yes      | Yes   | 9.0 GB |
| deepseek-r1:8b                                                  | Yes      | Yes   | 5.2 GB |
| gemma3:12b                                                      | No       | No    | 8.1 GB |
| gemma3:4b                                                       | No       | No    | 3.3 GB |
| gemma3n:e2b                                                     | No       | No    | 5.6 GB |
| gemma3n:e4b                                                     | No       | No    | 7.5 GB |
| gemma4:e2b                                                      | No       | Yes   | 7.2 GB |
| gemma4:e4b                                                      | No       | Yes   | 9.6 GB |
| glm-4.7-flash:q4_K_M                                            | Yes      | Yes   | 19 GB  |
| gpt-oss:20b                                                     | Yes      | Yes   | 14 GB  |
| granite4:3b-h                                                   | No       | Yes   | 1.9 GB |
| granite4:7b-a1b-h                                               | No       | Yes   | 4.2 GB |
| granite4:32b-a9b-h                                              | No       | Yes   | 19 GB  |
| llama3.1:8b                                                     | No       | Yes   | 4.9 GB |
| llama3:8b                                                       | No       | No    | 4.7 GB |
| lfm2:24b                                                        | No       | Yes   | 15 GB  |
| lfm2.5-thinking:1.2b                                            | Yes      | Yes   | 731 MB |
| phi3.5:3.8                                                      | No       | No    | 2.2 GB |
| kwangsuklee/Qwen3.5-9B-Claude-4.6-Opus-Reasoning-Distilled-GGUF | Yes      | Yes   | 5.6 GB |
| magistral:24b                                                   | Yes      | Yes   | 14 GB  |
| nemotron-3-nano:4b                                              | Yes      | Yes   | 2.8GB  |
| qwen3.5:27b                                                     | Yes      | Yes   | 17 GB  |
| qwen3.5:2b                                                      | Yes      | Yes   | 2.7 GB |
| qwen3.5:9b                                                      | Yes      | Yes   | 6.6 GB |
| qwen3:14b                                                       | Yes      | Yes   | 9.3 GB |
| qwen3:30b                                                       | Yes      | Yes   | 19 GB  |
| qwen3:8b                                                        | Yes      | Yes   | 5.2 GB |
| Apple Foundation Model (v1 - On Device ~3b)                     | Unknown  | Yes?  | 7 GB   |

## Test Article Set

| #   | URL                                                                                                                                                                                                                               | Notes (known issues, bias, etc.) |
| --- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------- |
| 1   | https://blog.google/innovation-and-ai/technology/developers-tools/gemma-4/                                                                                                                                                        |                                  |
| 2   | https://www.kcrg.com/2026/04/04/empty-downtown-cedar-rapids-office-spaces-converting-apartments/                                                                                                                                  |                                  |
| 3   | https://techcrunch.com/2026/04/02/nasa-artemis-microsoft-outlook-astronauts/                                                                                                                                                      |                                  |
| 4   | https://www.theguardian.com/us-news/2026/mar/20/fema-gregg-phillips-waffle-house                                                                                                                                                  |                                  |
| 5   | https://theonion.com/pete-hegseth-replaces-top-general-with-horse-that-drinks-beer/                                                                                                                                               |                                  |
| 6   | https://www.vaticannews.va/en/pope/news/2026-04/pope-leo-xiv-leads-way-of-the-cross-colosseum.html                                                                                                                                |                                  |
| 7   | https://defector.com/the-wild-card-race-gives-me-a-tummy-ache                                                                                                                                                                     |                                  |
| 8   | https://www.foxnews.com/us/one-americas-prettiest-cities-scrambles-reclaim-storybook-streets-homeless-camps-drug-dens                                                                                                             |                                  |
| 9   | https://lwn.net/Articles/1063717/                                                                                                                                                                                                 |                                  |
| 10  | https://www.whitehouse.gov/releases/2026/03/president-trump-ended-democrats-transgender-for-everybody-insanity/                                                                                                                   |                                  |
| 11  | https://www.whitehouse.gov/presidential-actions/2026/04/liberating-the-department-of-homeland-security-from-the-democrat-caused-shutdown/                                                                                         |                                  |
| 12  | https://maia.crimew.gay/posts/fuckstalkerware-8/                                                                                                                                                                                  |                                  |
| 13  | https://www.thenewcivilrightsmovement.com/2026/04/the-app-trump-wants-you-to-download-has-a-blank-privacy-policy-and-a-russia-founded-widget/                                                                                     |                                  |
| 14  | https://www.france24.com/fr/france/20260404-proposition-loi-caroline-yadan-contre-formes-renouvelees-antisemitisme-juif-israel-polemique                                                                                          |                                  |
| 15  | https://www.salon.com/2026/04/04/the-far-right-christians-pushing-trumps-war-to-bring-on-the-apocalypse/                                                                                                                          |                                  |
| 16  | https://www.tomshardware.com/tech-industry/artificial-intelligence/microsoft-says-copilot-is-for-entertainment-purposes-only-not-serious-use-firm-pushing-ai-hard-to-consumers-tells-users-not-to-rely-on-it-for-important-advice |                                  |

## Controlled Article Benchmarks

### Methodology

For each model confgiguration and hardware tier:

1. Run a fixed summarization prompt against each article
2. Run a fixed agent
