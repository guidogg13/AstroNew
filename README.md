<div align="center">

# 🌌 AstroNew

### A Desktop Suite for Exploring the ESA Gaia DR3 Archive — with a Built-in AI Assistant

[![License: PolyForm Noncommercial](https://img.shields.io/badge/license-PolyForm%20Noncommercial%201.0.0-blue.svg)](./LICENSE.md)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![Gaia](https://img.shields.io/badge/data-Gaia%20DR3-orange.svg)](https://www.cosmos.esa.int/web/gaia/data-release-3)
[![Status](https://img.shields.io/badge/status-active-brightgreen.svg)]()

**[Download](#-download)** • **[Installation](#-installation)** • **[Usage](#-usage)** • **[Features](#-features)** • **[Credits](#-data-credits)** • **[License](#-license)**

</div>

---

## 📖 About AstroNew

**AstroNew** is a free desktop application built for astronomers, astrophysicists, students, and anyone curious about the sky, designed to make querying and exploring the **ESA Gaia DR3** archive fast, visual, and accessible — without requiring deep knowledge of ADQL or the TAP protocol.

Gaia DR3 remains one of the richest astrometric and astrophysical datasets ever released, containing positions, parallaxes, proper motions, and physical parameters for over a billion stars. But accessing it directly usually means writing raw ADQL queries against ESA's TAP service — a barrier for many students, amateur astronomers, and even professionals who just need quick answers.

AstroNew removes that barrier. It provides:

- A clean desktop interface to build and run Gaia DR3 queries without writing ADQL by hand
- An **integrated AI assistant** that can help you formulate queries, interpret results, and navigate the archive using natural language
- Built-in tools for visualizing, filtering, and exporting the data you retrieve

The long-term goal of AstroNew is to become a **standard reference tool** for the astronomical community — a free, transparent, and actively maintained alternative to writing raw queries or juggling multiple scripts every time you need Gaia data.

> Whether you're a researcher cross-matching targets, a student learning stellar astrometry, or an astrophotographer curious about a field of stars — AstroNew is built to get you from question to data in minutes.

---

## ✨ Features

- 🔭 **Gaia DR3 Access** — Query the archive directly via TAP/ADQL, no authentication required (fully public and legal access, even after the Gaia satellite's decommission in March 2025 — the archive remains permanently available)
- 🤖 **AI Assistant** — An integrated conversational assistant helps you build queries, explains results, and answers astronomy-related questions in natural language, right inside the app
- 📊 **Data Visualization** — Instantly plot color-magnitude diagrams, sky maps, proper motion diagrams, and more using built-in `matplotlib` tools
- 📁 **Data Export** — Export any query result to CSV or other formats for further analysis in your own pipeline
- 🖥️ **Cross-Platform Desktop App** — Runs locally on your machine; no data leaves your computer except the queries sent to the official ESA Gaia archive
- 🧩 **No Coding Required** — Designed so that anyone, regardless of programming background, can retrieve real Gaia DR3 data
- 🔐 **Privacy-Respecting** — Gaia data access is anonymous by design; the optional AI assistant requires only your own API key, stored locally

---

## 🖼️ Screenshots

> *Screenshots and a short demo GIF will be added here shortly — showcasing the main dashboard, the query builder, and the AI assistant in action.*

<div align="center">
<i>[ Main Dashboard — coming soon ]</i><br>
<i>[ AI Assistant in Action — coming soon ]</i><br>
<i>[ Data Visualization Panel — coming soon ]</i>
</div>

---

## ⬇️ Download

**Don't want to install Python or deal with the command line?**

You can download a ready-to-use build of AstroNew directly from the official website:

### 👉 [Download AstroNew](#) *(link to be added once published)*

This is the recommended option for most users — astronomers, students, and hobbyists who just want to open the app and start exploring Gaia data.

---

## ⚙️ Installation

If you're a developer, or you want to run AstroNew from source, follow the steps below.

### Requirements

- Python 3.10 or higher
- pip (Python package manager)
- Git

### 1. Clone the repository

```bash
git clone https://github.com/your-username/AstroNew.git
cd AstroNew
```

### 2. Create a virtual environment (recommended)

```bash
python3 -m venv venv
source venv/bin/activate      # on macOS/Linux
venv\Scripts\activate         # on Windows
```

### 3. Install the dependencies

```bash
pip install -r requirements.txt
```

### 4. (Optional) Set up the AI Assistant

AstroNew's AI assistant runs on an external model via an OpenAI-compatible provider such as [OpenRouter](https://openrouter.ai/) (free for many models). **You don't need to edit any file by hand** — the first time you launch AstroNew, a **guided setup wizard** runs automatically whenever the configuration is missing:

1. Create a free account on OpenRouter and generate an API key
2. Launch AstroNew (see step 5) — the wizard will prompt you to:
   - **Paste your API key**
   - **Choose a model** (press Enter to accept the suggested default, `nvidia/nemotron-3-super-120b-a12b:free`)
   - **Optionally set the API base URL** (press Enter to keep the default, `https://openrouter.ai/api/v1`)
3. Your answers are saved automatically to `astronew/.env`, and the app continues to the main menu

The wizard only appears when `astronew/.env` is missing or the API key is still the placeholder. Once a valid key is saved, **subsequent launches skip the wizard** and go straight to the menu.

> The app works fully without an API key — just press **Enter** at the key prompt to skip. You can still query Gaia DR3 and generate plots; the AI assistant stays disabled until you configure a key (the wizard will offer to set it up again on the next launch).

### 5. Run AstroNew

```bash
python3 -m astronew
```

---

## 🚀 Usage

Once launched, AstroNew presents a simple menu-driven interface:

1. **Query Gaia DR3** — Build a query using guided filters (region of sky, magnitude range, parallax, proper motion, etc.) without writing ADQL yourself
2. **AI Assistant** — Ask questions in plain language, such as *"Find all stars within 50 parsecs with a parallax error under 5%"*, and let the assistant translate that into a valid query
3. **Visualize Results** — Generate color-magnitude diagrams, sky distribution plots, and more from your retrieved dataset
4. **Export Data** — Save your results locally as CSV for further analysis

### Example: A Basic ADQL Query

Behind the scenes, a simple AstroNew query might translate to something like:

```sql
SELECT TOP 1000 source_id, ra, dec, parallax, phot_g_mean_mag
FROM gaiadr3.gaia_source
WHERE parallax > 10
```

AstroNew builds and runs queries like this for you — but you can also write and run your own ADQL directly if you prefer full control.

---

## 🧠 About the AI Assistant

The AI backend uses a large cloud-hosted language model (via OpenRouter) rather than a local model, chosen specifically because smaller local models proved unreliable for structured tasks like tool calling and query generation. The assistant can:

- Translate natural language questions into valid ADQL queries
- Explain what a set of returned columns means
- Suggest follow-up queries or filters based on your results
- Answer general astrophysics questions related to your data

The assistant is entirely optional — AstroNew is fully functional as a Gaia DR3 query and visualization tool without it.

---

## 🛰️ Data Credits

AstroNew is built on top of the **ESA Gaia mission** archive. In accordance with ESA's data usage terms, the following credit applies to any use of Gaia data, including through this application:

> *This work has made use of data from the European Space Agency (ESA) mission Gaia (https://www.cosmos.esa.int/gaia), processed by the Gaia Data Processing and Analysis Consortium (DPAC, https://www.cosmos.esa.int/web/gaia/dpac/consortium). Funding for the DPAC has been provided by national institutions, in particular the institutions participating in the Gaia Multilateral Agreement.*

If you use AstroNew as part of published research, please cite both the Gaia mission and the relevant Gaia DR3 data release paper, in addition to acknowledging AstroNew itself.

---

## 🗺️ Roadmap

- [ ] Publish official binaries for Windows, macOS, and Linux
- [x] Add a first-run setup wizard for API key and model configuration
- [ ] Expand visualization tools (interactive sky maps, 3D plots)
- [ ] Register AstroNew with the Astrophysics Source Code Library (ASCL)
- [ ] Obtain a citable DOI via Zenodo
- [ ] Add support for cross-matching with other major catalogs (2MASS, SDSS, WISE)
- [ ] Community-requested features (open an issue to suggest one!)

---

## 🤝 Contributing

Contributions, bug reports, and feature suggestions are welcome! Please note that AstroNew is distributed under a **noncommercial license** (see below) — by contributing, you agree that your contributions will be distributed under the same terms.

To contribute:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/my-feature`)
3. Commit your changes
4. Open a Pull Request describing what you've done and why

For bugs or feature requests, please open an [Issue](../../issues).

---

## 📜 License

AstroNew is distributed under the **[PolyForm Noncommercial License 1.0.0](./LICENSE.md)**.

In short: you are free to use, study, modify, and share AstroNew for **any noncommercial purpose** — personal use, academic research, teaching, and use within public or nonprofit institutions are all explicitly permitted. **Commercial use, resale, or redistribution of AstroNew (or derivative works) for profit is not permitted** under this license.

See the [LICENSE.md](./LICENSE.md) file for the full legal text.

---

## 📬 Contact

For questions, suggestions, or collaboration inquiries, feel free to open an issue on this repository or reach out via the official AstroNew website *(link to be added)*.

<div align="center">

---

Made with ☄️ for the astronomy community.

</div>
