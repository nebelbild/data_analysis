# Product Overview

DataAnalysisAgent is an AI-powered data analysis automation agent built for the book "現場で活用するためのAIエージェント実践入門" (Practical Introduction to AI Agents for Real-World Applications).

## Core Purpose

Automates end-to-end data analysis workflows using LLMs and Jupyter kernels to generate insights, visualizations, and reports from CSV data.

## Key Features

- **Automated Analysis Pipeline**: 9-step workflow from data loading to report generation
- **LLM-Driven Code Generation**: Azure OpenAI with Structured Outputs for type-safe Python code generation
- **Safe Code Execution**: IPython kernel sandbox for isolated code execution
- **Multi-Format Reports**: HTML and Markdown output with embedded visualizations
- **Japanese Language Support**: Full Japanese support including matplotlib/seaborn font configuration
- **Clean Architecture**: Dependency injection and layered design for maintainability

## Workflow Stages

1. Load CSV data
2. Analyze dataframe (describe, info, sample)
3. Generate analysis plan (LLM breaks down hypothesis)
4-7. Execute tasks (code generation → execution → save results)
8. Review results (LLM quality evaluation)
9. Generate final report (HTML/Markdown)

## Target Users

Developers learning to build production-ready AI agent systems with clean architecture patterns.
