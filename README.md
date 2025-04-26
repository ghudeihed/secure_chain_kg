# Secure SaaS Supply Chains
## Challenge Page: 
[Secure SaaS Supply Chains ](https://app.knowhax.com/challenge_pop-hack/1741242356385x837731923223175000)

## Challenge definition: 
Over the past few years, there have been increasing attacks on software supply chains, such as the SolarWinds hack that impacted nine federal agencies in 2020. 
In response to the risks of software supply chains, Software Bills of Materials (SBOMs) have emerged as tools to facilitate the management of software dependencies and vulnerabilities in the supply chain.

However, it is challenging to manually create SBOMs accurately and comprehensively due to the complexity of software dependencies and vulnerabilities.

The NSF Proto-OKN (Proto-Open Knowledge Network) team led by Prof. Zhang from Purdue University has developed the first large-scale knowledge graph (KG) that tracks the dependency and vulnerability information of software libraries and applications in the C/C++ ecosystem. 
Specifically, it covers 11168 software, 54369 hardware, and 259334 vulnerabilities. 

The KG has been stored in an RDF format and can be easily loaded into graph databases such as Apache Jena Fuseki and oxigraph for analysis.  

In this challenge, you are expected to build tools on top of this knowledge graph to support effective risk management of third-party components in software products. 

Example tools include but are not limited to:
   . An easy-to-use KG query interface for cybersecurity researchers and end-users to analyze the software composition and vulnerability risks
   . An interactive visualization for the KG
   . A KG-based SBOM construction tool.

Beneficiaries: Our OKN team, NSF, Anyone interested (Open Source)
Sponsors: Currently NSF but open to any new sponsors. 

## Enviornement Setup:
### Backend
#### Via pip
```
# Change directory 
cd backend/

# Create virtual env 
python3 -m venv ven

# Activate the virtual env
source ./venv/bin/activate

# Install requirements.txt
pip install -r requirements.txt
```

#### Via poetry 
```
# Change directory 
cd backend/

# Activate the virtual env
poetry shell

# Install requirements.txt
poetry install
```

## Useful Resources:
- [Project Github Repo](https://github.com/ghudeihed/secure_chain_kg)
- [Knowledge Graph for Software Supply Cha​in Security Project](https://purdue-hcss.github.io/nsf-software-supply-chain_security/)
- [Ontology Documentation](https://w3id.org/secure-chain)
- [Data Dump](https://github.com/purdue-hcss/secure-chain-knowledge-graph)
- The dataset can be accessed in multiple ways:
  - [Zenodo](https://zenodo.org/records/808273#.WV35s9Pytcw) 
  - [Google Cloud](https://console.cloud.google.com/marketplace/product/libraries-io/librariesio?pli=1&project=the-onr-project)
  - [Libraries.io Web API](https://libraries.io/api)
  - [Project Github Repo](https://github.com/ghudeihed/secure_chain_kg)
  - [CVE List](https://www.cve.org/Downloads)
  - [National Vulnerability Database (NVD)](https://nvd.nist.gov/vuln/data-feeds)