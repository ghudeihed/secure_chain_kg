# 🛡️ Secure SaaS Supply Chain: SBOM Construction & Risk Visualization Tool

[![Hackathon](https://img.shields.io/badge/Hackathon-Purdue%20%2F%20NSF-blue)](https://www.purdue.edu/discoverypark/cyberinfrastructure/events/hackathon.php)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> A graph-based tool to generate SBOMs and visualize software supply chain risk using RDF knowledge graphs, SPDX/CycloneDX standards, and interactive frontend visualizations.

🎥 [**View Project Slides**](https://docs.google.com/presentation/d/1QKhC_lt7iXGSyTRPbYnwLI02zMuzPoemjOYngwvBCYo/edit?usp=sharing)  
📦 [**View GitHub Repo**](https://github.com/ghudeihed/secure_chain_kg)

---

## 🚀 Overview

This project extracts dependency and vulnerability information from a C/C++ software supply chain knowledge graph (RDF format), automatically constructs standardized SBOMs, and provides an interactive UI for exploring dependencies and visualizing risk.

The tool is ideal for researchers and DevSecOps teams aiming to manage third-party component risk in modern SaaS environments.

---

## 🧠 Key Features

- ✅ **SBOM Generation**: Outputs in [SPDX](https://spdx.dev/) and [CycloneDX](https://cyclonedx.org/) formats  
- 🧠 **Knowledge Graph Integration**: RDF graph querying via SPARQL and Apache Jena Fuseki  
- 🌐 **REST API**: SPARQL-based dependency resolution and SBOM construction  
- 📊 **Frontend Visualization**:
  - Cytoscape.js: Interactive dependency graph
  - D3.js: Risk overlays using CVE data
- 🐳 **Dockerized Environment**: One-line setup via `docker-compose`

---

## 🏗️ System Architecture

<img src="./assets/high_level_diagram.png">

---

## 📦 Installation

### 🔧 Prerequisites
- Docker + Docker Compose

### 🚀 Quick Start

```bash
git clone https://github.com/ghudeihed/secure_chain_kg
cd secure_chain_kg
docker-compose up --build
````

### 🖥️ Access the Services

| Service     | URL                                                                    |
| ----------- | ---------------------------------------------------------------------- |
| Frontend UI | [http://localhost:3000](http://localhost:3000)                         |
| Fuseki UI   | [http://localhost:3030/securechain](http://localhost:3030/securechain) |
| API Docs    | [http://localhost:8000/docs](http://localhost:8000/docs)               |

---

## 🔍 Usage

1. Select a root component (e.g., `openssl`, `zlib`)
2. Backend resolves dependencies using SPARQL
3. SBOM (SPDX or CycloneDX) is generated
4. UI displays:

   * Interactive dependency graph
   * CVE severity heatmap

---

## 🛠️ API Endpoints

| Method | Endpoint             | Description                    |
| ------ | -------------------- | ------------------------------ |
| GET    | `/api/sbom/generate` | Generate SBOM for a package    |
| GET    | `/api/components`    | List available root components |
| GET    | `/api/dependencies`  | Get full dependency graph      |

Explore all via [Swagger UI](http://localhost:8000/docs)

---

## 📂 Project Structure

```
secure_chain_kg/
│
├── frontend/         # React app with Cytoscape/D3 visualizations
├── backend/          # FastAPI server with SPARQL logic
├── fuseki/           # RDF store config + .ttl file (SecureChain KG)
├── docker-compose.yml
└── README.md
```

---

## 🧪 Sample SBOM Output (CycloneDX)

```json
{
  "bomFormat": "CycloneDX",
  "components": [
    {
      "type": "library",
      "name": "zlib",
      "version": "1.2.11",
      "licenses": ["Zlib"],
      "vulnerabilities": [
        {
          "id": "CVE-2022-37434",
          "severity": "HIGH"
        }
      ]
    }
  ]
}
```

---

## 📉 Known Limitations

* Demo RDF graph is small for illustrative purposes
* CVE severity is mapped manually (no dynamic CVSS feed)
* No auth / access control (assumes local trusted use)

---

## 📊 Presentation Slides

📽️ **Project Pitch & Demo Slides**:
[https://docs.google.com/presentation/d/1QKhC\_lt7iXGSyTRPbYnwLI02zMuzPoemjOYngwvBCYo](https://docs.google.com/presentation/d/1QKhC_lt7iXGSyTRPbYnwLI02zMuzPoemjOYngwvBCYo)

---

## 🤝 Contributing

Pull requests are welcome! For major changes, please open an issue to discuss what you’d like to change.

---

## 📝 License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

## 🙌 Acknowledgments

* Purdue University & NSF for the Hackathon challenge
* SPDX, CycloneDX, and OWASP for SBOM standards
* Apache Jena, Cytoscape.js, D3.js for ecosystem support