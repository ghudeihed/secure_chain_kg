Here are the steps to run these backend tests:

1. First, navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Make sure you have the required dependencies installed:
   ```bash
   pip install -r requirements.txt
   ```
   
   Or if you're using Poetry (since I see a pyproject.toml file):
   ```bash
   poetry install
   ```

3. Install pytest if you don't already have it
   ```bash
   pip install pytest
   ```

4. Run all tests
   ```bash
   pytest
   ```

5. Run tests with verbose output
   ```bash
   pytest -v
   ```

6. Run specific test file
   ```bash
   pytest tests/test_sparql_client.py -v
   pytest tests/test_sbom_generator.py -v
   ```

7. Run specific test function
   ```bash
   pytest tests/test_sparql_client.py::test_query_caching -v
   ```

8. Generate test coverage report
   ```bash
   pip install pytest-cov
   pytest --cov=app tests/
   ```
