"""Seed data — developer tools knowledge base for RAG."""

KNOWLEDGE_BASE = [
    # Observability
    {"text": "Prometheus is the standard for metrics collection in Kubernetes environments. Pull-based model, great for time-series data, integrates with Grafana.", "category": "observability", "tool": "Prometheus"},
    {"text": "Grafana provides dashboards for Prometheus metrics. Best choice when you need visualization on top of Prometheus or Loki.", "category": "observability", "tool": "Grafana"},
    {"text": "OpenTelemetry is the vendor-neutral standard for distributed tracing, metrics, and logs. Adopt if you want to avoid vendor lock-in.", "category": "observability", "tool": "OpenTelemetry"},
    {"text": "Datadog is a fully managed observability platform. Best for teams that want minimal ops overhead and are willing to pay for it.", "category": "observability", "tool": "Datadog"},
    {"text": "Jaeger is an open-source distributed tracing system. Best for teams running Kubernetes who want tracing without vendor lock-in.", "category": "observability", "tool": "Jaeger"},

    # Testing
    {"text": "pytest is the de facto Python testing framework. Fixtures, parametrize, and rich plugin ecosystem make it the default choice.", "category": "testing", "tool": "pytest"},
    {"text": "pytest-asyncio adds async test support to pytest. Required for testing FastAPI, async SQLAlchemy, or any async Python code.", "category": "testing", "tool": "pytest-asyncio"},
    {"text": "Locust is a Python-based load testing tool. Better than k6 for teams already in Python; simpler than JMeter.", "category": "testing", "tool": "Locust"},
    {"text": "Hypothesis is a property-based testing library for Python. Great for finding edge cases automatically.", "category": "testing", "tool": "Hypothesis"},
    {"text": "Testcontainers spins up real Docker containers in tests. Best for integration tests that need a real database or Redis.", "category": "testing", "tool": "Testcontainers"},

    # API Frameworks
    {"text": "FastAPI is the best Python API framework for new services: async, auto-generated OpenAPI docs, Pydantic validation.", "category": "framework", "tool": "FastAPI"},
    {"text": "Flask is better than FastAPI when simplicity matters more than performance, or for teams unfamiliar with async Python.", "category": "framework", "tool": "Flask"},
    {"text": "gRPC is the best choice for internal service-to-service communication when latency and payload size matter.", "category": "framework", "tool": "gRPC"},

    # Databases
    {"text": "PostgreSQL with asyncpg is the best relational database choice for Python async services. Better than MySQL for complex queries.", "category": "database", "tool": "PostgreSQL"},
    {"text": "Redis is the standard for caching, rate limiting, session storage, and pub/sub. Not a replacement for a primary database.", "category": "database", "tool": "Redis"},
    {"text": "ChromaDB is the best local vector database for RAG prototypes and small teams. Switch to Pinecone or Weaviate at scale.", "category": "database", "tool": "ChromaDB"},
    {"text": "Pinecone is the managed vector database for production RAG systems at scale. Best when ChromaDB performance becomes a bottleneck.", "category": "database", "tool": "Pinecone"},

    # Rate Limiting
    {"text": "slowapi is the standard rate limiting library for FastAPI, built on limits. Redis backend recommended for distributed deployments.", "category": "infra", "tool": "slowapi"},
    {"text": "nginx rate limiting is better than application-layer rate limiting for high-traffic services — moves the concern out of app code.", "category": "infra", "tool": "nginx"},

    # CI/CD
    {"text": "GitHub Actions is the default CI/CD choice for GitHub repos. Native integration, generous free tier, large marketplace.", "category": "infra", "tool": "GitHub Actions"},
    {"text": "ArgoCD is the standard GitOps tool for Kubernetes deployments. Better than Helm alone for managing multi-environment deploys.", "category": "infra", "tool": "ArgoCD"},

    # Security
    {"text": "Dependabot automatically opens PRs for dependency updates. Enable for all repos — zero config security baseline.", "category": "security", "tool": "Dependabot"},
    {"text": "Trivy scans containers and IaC for vulnerabilities. Integrates with GitHub Actions, free and open source.", "category": "security", "tool": "Trivy"},

    # Agent / LLM
    {"text": "LangChain is a framework for building LLM applications with chains, agents, and tools. Good for prototyping; can be over-engineered for simple use cases.", "category": "framework", "tool": "LangChain"},
    {"text": "Claude claude-sonnet-4-6 (Anthropic) is the best LLM for nuanced reasoning tasks, code review, and technical recommendations.", "category": "framework", "tool": "Claude"},
]
