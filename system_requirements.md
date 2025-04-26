## **Functional Requirements**
1. **Parse and Load Knowledge Graph**
   - Load RDF knowledge graph into a triplestore (e.g., Apache Jena Fuseki or oxigraph).
   - Support SPARQL queries on the KG.

2. **Dependency Management Interface**
   - Input a software component.
   - Build a complete dependency tree using Libraries.io and the KG.
   - Show transitive dependencies.

3. **Risk Analysis**
   - Query CVEs/NVD data to associate vulnerabilities with dependencies.
   - Show severity, affected versions, and patch availability.

4. **SBOM Construction Tool**
   - Export SBOM (e.g., in SPDX, CycloneDX, or custom JSON format).
   - Include all third-party components and associated risks.

5. **Visualization Interface**
   - Interactive graph showing dependency tree.
   - Allow exploration of dependency paths and vulnerabilities.

6. **Search and Query Interface**
   - Basic SPARQL-based query builder for researchers.
   - Optional: visual query assistant or templates.
---

## **Non-Functional Requirements**
- **Security**: Sanitize inputs, secure API endpoints.
- **Usability**: Simple, clean UI (even minimalistic is fine).
- **Performance**: Support for moderately large dependency trees (e.g., 100+ nodes).
- **Portability**: Should run locally or on a single cloud VM.
- **Documentation**: Basic README with install/run instructions, API/query examples.