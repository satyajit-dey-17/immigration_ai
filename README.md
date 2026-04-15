# 🇺🇸 ImmigrationIQ

A production-grade Retrieval-Augmented Generation (RAG) platform that scrapes, processes, and indexes US immigration data from federal sources — enabling natural language Q&A on immigration policies, forms, and procedures.







***

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        ImmigrationIQ                        │
├───────────────┬─────────────────┬───────────────────────────┤
│   Scraper     │    Backend      │       Frontend            │
│  (Scrapy +    │   (FastAPI)     │     (Streamlit)           │
│  Playwright)  │                 │                           │
├───────────────┼─────────────────┼───────────────────────────┤
│         OpenAI Embeddings       │    Qdrant Vector DB       │
│         (text-embedding-3-small)│    (49,000+ chunks)       │
├─────────────────────────────────┴───────────────────────────┤
│              Observability Stack                            │
│     Prometheus · Grafana · Loki · Promtail · cAdvisor       │
└─────────────────────────────────────────────────────────────┘
```

***

## 🕷️ Data Sources

| Source | Topic | Crawl Schedule |
|--------|-------|----------------|
| [USCIS](https://www.uscis.gov) | Immigration forms & policies | Daily + Weekly |
| [IRS](https://www.irs.gov) | Tax obligations for immigrants | Weekly |
| [DOL](https://www.dol.gov) | Labor/wage certifications (PERM, LCA) | Weekly |
| [CBP](https://www.cbp.gov) | Border & customs procedures | Weekly |
| [EOIR](https://www.justice.gov/eoir) | Immigration court & board decisions | Weekly |
| [Federal Register](https://www.federalregister.gov) | Immigration rulemaking | Weekly |
| [Visa Bulletin](https://travel.state.gov) | Monthly visa priority dates | Weekly |
| [E-Verify](https://www.e-verify.gov) | Employment eligibility | Weekly |

***

## 🛠️ Tech Stack

### Core Services
- **Scraper** — Scrapy + Playwright, 8 custom spiders, APScheduler
- **Backend** — FastAPI with REST endpoints for Q&A and document retrieval
- **Frontend** — Streamlit conversational UI
- **Vector DB** — Qdrant with `text-embedding-3-small` (1536 dimensions)
- **Relational DB** — PostgreSQL for content hash deduplication

### Observability
- **Metrics** — Prometheus + custom pipeline counters (ingestion rate, latency p50/p99)
- **Dashboards** — Grafana with real-time ImmigrationIQ Pipeline dashboard
- **Logs** — Loki + Promtail (structured JSON log ingestion)
- **Container metrics** — cAdvisor (CPU, memory per container)

***

## 📊 Grafana Dashboard Panels

| Panel | Metric | Source |
|-------|--------|--------|
| Pages Ingested (Total) | `pages_ingested_total` | Prometheus |
| Pages Skipped (Unchanged) | `pages_skipped_total` | Prometheus |
| Pages Failed | `pages_failed_total` | Prometheus |
| Ingestion Rate (pages/min) | Rate over time by topic | Prometheus |
| OpenAI Embed Latency p50/p99 | `embed_duration_seconds` | Prometheus |
| Qdrant Upsert Duration p99 | `qdrant_upsert_duration_seconds` | Prometheus |
| Postgres Write Duration p99 | `db_write_duration_seconds` | Prometheus |
| Pages Ingested by Topic | Pie chart per topic | Prometheus |
| Scraper Memory Usage | `container_memory_rss` | cAdvisor |
| Scraper CPU Usage | `container_cpu_usage_seconds_total` | cAdvisor |

***

## 🚀 Getting Started

### Prerequisites
- Docker + Docker Compose
- OpenAI API key

### 1. Clone the repo
```bash
git clone https://github.com/yourusername/immigrationiq.git
cd immigrationiq
```

### 2. Set up environment variables
```bash
cp .env.example .env
# Edit .env and add your OpenAI API key
```

### 3. Start all services
```bash
docker compose up -d
```

### 4. Access the services

| Service | URL |
|---------|-----|
| Frontend (Streamlit) | http://localhost:8501 |
| Backend (FastAPI) | http://localhost:8000 |
| Grafana Dashboard | http://localhost:3000 |
| Prometheus | http://localhost:9090 |
| Qdrant | http://localhost:6333/dashboard |

### 5. Run the scraper
```bash
# Daily delta scrape (fast, changed pages only)
docker compose exec scraper python bulk_ingest.py daily

# Full crawl (all 8 spiders)
docker compose exec scraper python bulk_ingest.py full
```

***

## 📁 Project Structure

```
immigrationiq/
├── scraper/
│   ├── spiders/              # 8 Scrapy spiders
│   ├── utils/
│   │   ├── metrics.py        # Prometheus counters & histograms
│   │   ├── embedder.py       # OpenAI embedding logic
│   │   ├── chunker.py        # Text chunking
│   │   ├── qdrant_client.py  # Qdrant upsert logic
│   │   └── db.py             # PostgreSQL hash deduplication
│   ├── pipeline.py           # Core ingestion pipeline
│   ├── scheduler.py          # APScheduler + metrics server
│   └── bulk_ingest.py        # Manual scrape trigger
├── api/                      # FastAPI backend
├── frontend/                 # Streamlit app
├── monitoring/
│   ├── prometheus.yml
│   ├── promtail.yml
│   └── grafana/
│       ├── dashboards/
│       └── provisioning/
├── docker-compose.yml
└── .env.example
```

***

## ⚙️ How It Works

1. **Crawl** — Spiders fetch pages from federal immigration websites using Scrapy + Playwright (for JS-rendered content)
2. **Deduplicate** — SHA-256 hash of page content is checked against PostgreSQL; unchanged pages are skipped
3. **Chunk** — New pages are split into overlapping text chunks with metadata (URL, topic, scraped date)
4. **Embed** — Chunks are sent to OpenAI `text-embedding-3-small` in batches
5. **Store** — Vectors are upserted into Qdrant; old chunks for the same URL are deleted first
6. **Query** — User questions are embedded and matched against Qdrant via cosine similarity
7. **Answer** — Relevant chunks are passed to GPT as context for grounded, cited responses

***

## 📈 Current Stats

- **49,000+** document chunks indexed
- **8** federal data sources
- **10+** containerized microservices
- **Real-time** observability across all pipeline stages

***

## 🔮 Roadmap

- [ ] Increase crawl depth to 3 for USCIS, IRS, EOIR, DOL
- [ ] Add CI/CD pipeline with Jenkins
- [ ] Add sitemap-based crawling for all spiders
- [ ] User authentication and query history
- [ ] Deploy to AWS (ECS or EKS)
- [ ] Add Azure and GCP immigration resource sources

***

## 👤 Author

**Satyajit** — MS Information Systems @ UMBC  
[LinkedIn](https://www.linkedin.com/in/satyajit-/) · [GitHub](https://github.com/satyajit-dey-17)

***

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.
