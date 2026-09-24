# Help Center → SharePoint Pipeline for RAG

## Overview

A Python pipeline that synchronizes public Zendesk Help Center articles to **SharePoint**, preparing a maintained knowledge source for **Retrieval-Augmented Generation (RAG)** applications.

## What it does

- Discovers English-language articles through a sitemap
- Converts article content into lightweight HTML
- Uploads new and updated articles through Microsoft Graph
- Reconciles removed articles and stores sync state in Azure Blob Storage
- Runs hourly updates and daily cleanup with Azure Functions

## Architecture

**Zendesk Help Center → Content Processing & Sync → SharePoint → Downstream RAG Application**

This repository provides the ingestion layer; retrieval and AI inference run separately.

## Run locally

Requires Python 3.10+, an Azure app with access to the target SharePoint library, and Azure Blob Storage.

```bash
pip install -r requirements.txt
cp .env.example .env
# Fill in .env with your own configuration.
python main.py updates
python main.py cleanup
```

Use a dedicated target folder. Cleanup deletes files that are not represented in the current sitemap and saved state; run updates successfully before cleanup. Azure Functions uses the same settings as environment variables.
