# SecureChain RDF Service

This project sets up an RDF/SPARQL service for managing and querying knowledge graph data using [Apache Jena Fuseki](https://jena.apache.org/documentation/fuseki2/). It uses a pre-configured dataset with a TDB2 backend and includes scripts and configuration for easy deployment via Docker.

## 🧾 Project Structure

```
.
├── config.ttl             # Fuseki server configuration (Turtle format)
├── data/
│   └── securechain_data.ttl    # Optional RDF data to load
├── databases/
│   └── securechain/            # Preloaded TDB2 dataset
├── Dockerfile             # Dockerfile to build the Fuseki container
├── load_data.sh           # Script to load data into the TDB2 store
├── README.md              # Additional setup notes (optional)
└── shiro.ini              # (Optional) Auth configuration - currently disabled in dev
```

## 🚀 Running the Service with Docker

### 1. **Build the Docker Image**

```bash
docker build -t securechain-fuseki .
```

### 2. **Run the Container**

```bash
docker run -it --rm -p 3030:3030 securechain-fuseki
```

* The Fuseki web UI will be available at:
  **[http://localhost:3030](http://localhost:3030)**

* The SPARQL endpoint will be available at:
  **[http://localhost:3030/securechain/query](http://localhost:3030/securechain/query)**

### 3. **(Optional) Load Additional RDF Data**

To reload or update data from `data/securechain_data.ttl`:

```bash
./load_data.sh
```

> Note: This script may use `curl` or Fuseki's update endpoint to load TTL data into the TDB2 store.

## ⚙️ Configuration Overview

* **`config.ttl`** – Defines the Fuseki server and the `securechain` dataset with TDB2 backend.
* **`shiro.ini`** – Authentication config (not used in dev mode; all requests are anonymous).
* **Query Timeout** – Set to 10 seconds by default in `config.ttl`.

## 📬 Endpoints Summary

| Type          | URL                                        |
| ------------- | ------------------------------------------ |
| SPARQL Query  | `http://localhost:3030/securechain/query`  |
| SPARQL Update | `http://localhost:3030/securechain/update` |
| Graph Store   | `http://localhost:3030/securechain/data`   |
| Upload        | `http://localhost:3030/securechain/upload` |

## 🛠 Dependencies

* [Apache Jena Fuseki](https://jena.apache.org/documentation/fuseki2/)
* Docker