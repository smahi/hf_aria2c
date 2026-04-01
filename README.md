# hf-aria2c

A fast Hugging Face model downloader that uses **aria2** for multi-connection downloads while staying compatible with the official Hugging Face cache layout.

It fetches repository metadata via the Hugging Face API, generates direct file URLs, and downloads everything efficiently using aria2 with parallel and resumable transfers.

---

## ✨ Features

- Multi-threaded downloads using aria2
- Hugging Face API integration
- Cache-compatible directory structure
- Supports authentication (private/gated models)
- File filtering (include/exclude extensions)
- Resume support
- Dry-run mode to preview downloads

---

## 📦 Prerequisites

- Python 3.10+
- aria2 installed

### Install aria2

**Ubuntu / Debian:**
```bash
sudo apt update
sudo apt install aria2