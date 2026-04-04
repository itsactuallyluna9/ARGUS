# ARGUS Benchmarking

This document covers the methodology for benchmarking models for use in ARGUS, as well as recorded results across hardware tiers. There are two distinct phases: controlled model benchmarks (which are isolated and reproducible) and pipeline benchmarks (which are full end-to-end tests).

## Hardware

### Laptop A

### Laptop B

|Component|Spec|
|-|-|
|CPU|Apple M1 Max (8 Performance and 2 Efficiency)|
|GPU|Apple M1 Max (32 Core GPU)|
|Unified RAM|32 GB LPDDR5|
|Storage|SSD|
|OS|macOS Tahoe 26.3.1|

### Desktop A

|Component|Spec|
|-|-|
|CPU|16 x AMD EPYC 7232P 8-Core Processor|
|RAM|64 GB LPDDR5|
|GPU|NVIDIA A2|
|VRAM|16 GB GDDR6|
|Storage|SSD|
|OS|Arch Linux|

### Desktop B

|Component|Spec|
|-|-|
|CPU|16 x AMD EPYC 7232P 8-Core Processor|
|RAM|64 GB LPDDR5|
|GPU|NVIDIA A2|
|VRAM|16 GB GDDR6|
|Storage|HDD|
|OS|Ubuntu Server 24.04.4 LTS (Noble Numbat)|

### Server

|Component|Spec|
|-|-|
|CPU|16 x AMD EPYC 7232P 8-Core Processor|
|RAM|64 GB LPDDR5|
|GPU|NVIDIA A2|
|VRAM|16 GB GDDR6|
|Storage|HDD|
|OS|Ubuntu Server 24.04.4 LTS (Noble Numbat)|

## Models

|Name|Thinking|Tools|Size|Notes|
|-|-|-|-|-|
|deepseek-r1:14b|Yes|Yes|9.0 GB|
|deepseek-r1:8b|Yes|Yes|5.2 GB|
|gemma3:12b|No|No|8.1 GB|
|gemma3:4b|No|No|3.3 GB|
|gemma3n:e2b|No|No|5.6 GB|
|gemma3n:e4b|No|No|7.5 GB|
|gemma4:e2b|No|Yes|7.2 GB|
|gemma4:e4b|No|Yes|9.6 GB|
|glm-4.7-flash:q4_K_M|Yes|Yes|19 GB|
|gpt-oss:20b|Yes|Yes|14 GB|
|granite4:3b-h|No|Yes|1.9 GB|
|granite4:7b-a1b-h|No|Yes|4.2 GB|
|granite4:32b-a9b-h|No|Yes|19 GB|
|llama3.1:8b|No|Yes|4.9 GB|
|llama3:8b|No|No|4.7 GB|
|lfm2:24b|No|Yes|15 GB|
|lfm2.5-thinking:1.2b|Yes|Yes|731 MB|
|magistral:24b|Yes|Yes|14 GB|
|nemotron-3-nano:4b|Yes|Yes|2.8GB|
|qwen3.5:27b|Yes|Yes|17 GB|
|qwen3.5:2b|Yes|Yes|2.7 GB|
|qwen3.5:9b|Yes|Yes|6.6 GB|
|qwen3:14b|Yes|Yes|9.3 GB|
|qwen3:30b|Yes|Yes|19 GB|
|qwen3:8b|Yes|Yes|5.2 GB|
|Apple Foundation Model (v1 - On Device ~3b)|Unknown|Yes?|7 GB|


## Test Article Set

| # | URL | Notes (known issues, bias, etc.) |
|---|-----|----------------------------------|
| 1 | | |
| 2 | | |
| 3 | | |
| 4 | | |
| 5 | | |
| 6 | | |
| 7 | | |
| 8 | | |
| 9 | | |
| 10 | | |

## Controlled Article Benchmarks

### Methodology

For each model confgiguration and hardware tier:

1. Run a fixed summarization prompt against each article
2. Run a fixed agent
