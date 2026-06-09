# URIS-AI System Architecture

## 1. System Overview

```mermaid
graph LR
    USER(("👤\nUser\nBrowser"))

    subgraph GCP["☁️ Google Cloud Platform — asia-southeast1"]
        direction LR
        CR["🐳 Cloud Run\nurisai-api\nPython 3.12 · FastAPI\nPort 8080"]
        AR["📦 Artifact Registry\nurisai-repo\nDocker Image ~196MB"]
        CB["🔨 Cloud Build\nCI/CD Pipeline\n~90 detik build"]
    end

    subgraph AZURE["🔷 Microsoft Azure — southeastasia"]
        DB[("🗄️ MySQL\nurisai-mysql\nFree Tier B1MS\n8 tabel · 25 wilayah")]
        MAPS["🗺️ Azure Maps\nurisai-maps\nGen2 · Night Style\nSubscription Key"]
        STORAGE["💾 Blob Storage\nurisaistorage\nData raw & processed"]
        KV["🔐 Key Vault\nurisai-kv\nSecrets Management"]
    end

    USER -->|"HTTPS"| CR
    CB -->|"push image"| AR
    AR -->|"pull image"| CR
    CR -->|"SQLAlchemy\nPyMySQL"| DB
    CR -->|"Subscription Key\n→ Browser"| MAPS
    CR -.->|"opsional"| STORAGE
    CR -.->|"opsional"| KV

    style GCP fill:#e8f5e9,stroke:#43a047,stroke-width:2px
    style AZURE fill:#e3f2fd,stroke:#1e88e5,stroke-width:2px
    style USER fill:#fff8e1,stroke:#f9a825,stroke-width:2px
    style CR fill:#ffffff,stroke:#43a047,stroke-width:2px
    style AR fill:#ffffff,stroke:#43a047,stroke-width:2px
    style CB fill:#ffffff,stroke:#43a047,stroke-width:2px
    style DB fill:#ffffff,stroke:#1e88e5,stroke-width:2px
    style MAPS fill:#ffffff,stroke:#1e88e5,stroke-width:2px
    style STORAGE fill:#ffffff,stroke:#1e88e5,stroke-width:2px
    style KV fill:#ffffff,stroke:#1e88e5,stroke-width:2px
```

---

## 2. Application Stack (Docker Container)

```mermaid
graph TB
    subgraph CONTAINER["🐳 Docker Container — Cloud Run"]
        direction TB

        subgraph FRONTEND["⚛️ React Frontend (Static Files)"]
            LP["Landing Page\n/"]
            DASH["Dashboard\n/dashboard"]
            MAPS_UI["Azure Maps SDK\nBubble Markers\nFlood Overlay"]
            CHARTS["Recharts\nTren URS 24 jam"]
        end

        subgraph BACKEND["🐍 FastAPI Backend (uvicorn)"]
            MW["Middleware\nCORS · Logging · Rate Limit"]
            EP["Endpoints\nGET /api/dashboard\nGET /regions/{id}/risk\nGET /regions/{id}/risk/trend\nGET /regions/{id}/recommendations\nPOST /routes/safe\nGET /health"]
            ML["ML & Business Logic\nFloodRiskEngine\nRiskScoringEngine\nRecommendationEngine"]
            ORM["SQLAlchemy ORM\nPyMySQL Driver"]
        end
    end

    LP --> DASH
    DASH --> MAPS_UI
    DASH --> CHARTS
    FRONTEND -->|"fetch /api/*"| BACKEND
    MW --> EP
    EP --> ML
    ML --> ORM

    style CONTAINER fill:#f3e5f5,stroke:#8e24aa,stroke-width:2px
    style FRONTEND fill:#e8f5e9,stroke:#43a047,stroke-width:1px
    style BACKEND fill:#e3f2fd,stroke:#1e88e5,stroke-width:1px
```

---

## 3. Data Pipeline

```mermaid
graph LR
    subgraph SOURCES["📡 Data Sources"]
        BMKG["🌧️ BMKG\nPrakiraan Cuaca\n432 records"]
        OSM["🗺️ OpenStreetMap\n27.835 jalan\n11.233 fasilitas"]
        FLOOD["🌊 Historis Banjir\nJakarta 2 tahun\n646 events"]
        PB["📡 PetaBencana\nLaporan real-time"]
    end

    subgraph PROCESS["⚙️ Processing Scripts"]
        IMP["import_raw_data.py\nseed_data.py"]
        GEN["generate_risk_scores.py\nML Model scikit-learn"]
        HIST["generate_urs_history.py\n23 titik/wilayah/jam"]
        REC["generate_recommendations.py\n39 rekomendasi"]
    end

    subgraph DB["🗄️ Azure MySQL — uris-ai-db"]
        T1[("regions\n25 wilayah")]
        T2[("weather_data\n432 rec")]
        T3[("flood_events\n646 rec")]
        T4[("roads\n27.835 rec")]
        T5[("public_facilities\n11.233 rec")]
        T6[("risk_scores\n600 rec")]
        T7[("recommendations\n39 rec")]
    end

    BMKG --> IMP
    OSM --> IMP
    FLOOD --> IMP
    PB --> IMP

    IMP --> T1
    IMP --> T2
    IMP --> T3
    IMP --> T4
    IMP --> T5

    T1 --> GEN
    T2 --> GEN
    T3 --> GEN
    GEN --> T6

    T6 --> HIST
    HIST --> T6

    T6 --> REC
    REC --> T7

    style SOURCES fill:#fff8e1,stroke:#f9a825,stroke-width:2px
    style PROCESS fill:#fce4ec,stroke:#e91e63,stroke-width:2px
    style DB fill:#e3f2fd,stroke:#1e88e5,stroke-width:2px
```

---

## 4. Urban Risk Score — Calculation Flow

```mermaid
graph LR
    subgraph INPUT["📥 Input Factors"]
        A["🌧️ Curah Hujan\nElevasi Wilayah\nKapasitas Drainase\nHistoris Banjir"]
        B["🚗 Kepadatan Jalan\nTipe Jalan\nRoad Density"]
        C["🏥 Jumlah Fasilitas\nTipe Fasilitas\nStatus Operasional"]
    end

    subgraph SCORE["📊 Component Scores (0–100)"]
        FR["Flood Risk\n⚖️ Bobot 50%"]
        TI["Traffic Impact\n⚖️ Bobot 30%"]
        SA["Service Access\n⚖️ Bobot 20%"]
    end

    URS["🎯 Urban Risk Score\nURS = FR×0.5 + TI×0.3 + SA×0.2\nRange: 0 – 100"]

    subgraph CAT["🏷️ Kategori Risiko"]
        R1["🟢 RENDAH\n0 – 25"]
        R2["🟡 SEDANG\n26 – 50"]
        R3["🔴 TINGGI\n51 – 75"]
        R4["🟣 KRITIS\n76 – 100"]
    end

    OUT["📋 Rekomendasi Tindakan\nalert · route · service\nevacuation · resource_allocation"]

    A --> FR
    B --> TI
    C --> SA
    FR --> URS
    TI --> URS
    SA --> URS
    URS --> R1
    URS --> R2
    URS --> R3
    URS --> R4
    R4 -->|"Penjaringan\nURS = 84.2"| OUT

    style INPUT fill:#fff8e1,stroke:#f9a825,stroke-width:2px
    style SCORE fill:#fce4ec,stroke:#e91e63,stroke-width:2px
    style URS fill:#e8f5e9,stroke:#43a047,stroke-width:3px
    style CAT fill:#f3e5f5,stroke:#8e24aa,stroke-width:2px
    style OUT fill:#e3f2fd,stroke:#1e88e5,stroke-width:2px
```

---

## 5. CI/CD Deployment Pipeline

```mermaid
graph LR
    DEV(("💻\nDeveloper"))

    subgraph LOCAL["🖥️ Local"]
        BUILD_FE["npm run build\nReact → static/"]
        CODE["Source Code\n+ Dockerfile\n+ .gcloudignore"]
    end

    subgraph GCP_BUILD["☁️ GCP Cloud Build"]
        UPLOAD["Upload Source\n~104 files · 9.4 MB"]
        DOCKER["Docker Build\npython:3.12-slim\npip install ~35 pkg\n~90 detik"]
        PUSH["Push Image\n~196 MB"]
    end

    subgraph REGISTRY["📦 Artifact Registry"]
        IMAGE["urisai-api:latest\nsha256:xxxx"]
    end

    subgraph CLOUDRUN["🚀 Cloud Run"]
        REV["New Revision\nHealth Check ✓"]
        TRAFFIC["Traffic 100%\nLive!"]
    end

    LIVE(("🌐\nLive URL\nhttps://\nurisai-api-\nzgwts4p3va-\nas.a.run.app"))

    DEV --> BUILD_FE
    BUILD_FE --> CODE
    CODE -->|"gcloud builds submit"| UPLOAD
    UPLOAD --> DOCKER
    DOCKER --> PUSH
    PUSH --> IMAGE
    IMAGE -->|"gcloud run deploy"| REV
    REV --> TRAFFIC
    TRAFFIC --> LIVE

    style LOCAL fill:#fff8e1,stroke:#f9a825,stroke-width:2px
    style GCP_BUILD fill:#e8f5e9,stroke:#43a047,stroke-width:2px
    style REGISTRY fill:#e8f5e9,stroke:#43a047,stroke-width:2px
    style CLOUDRUN fill:#e8f5e9,stroke:#43a047,stroke-width:2px
    style LIVE fill:#e3f2fd,stroke:#1e88e5,stroke-width:3px
```

---

## 6. Database Schema (ER Diagram)

```mermaid
erDiagram
    regions {
        int region_id PK
        varchar name
        float latitude
        float longitude
        float elevation
        float drainage_capacity
    }

    weather_data {
        int id PK
        int region_id FK
        datetime date
        float rainfall
        float humidity
        float temperature
    }

    flood_events {
        int id PK
        int region_id FK
        datetime date
        int severity
        float water_level
        int duration_hours
    }

    roads {
        int id PK
        int region_id FK
        varchar road_type
        float road_density
        boolean is_main_road
    }

    public_facilities {
        int id PK
        int region_id FK
        varchar name
        varchar type
        boolean is_operational
    }

    risk_scores {
        int id PK
        int region_id FK
        datetime date
        float flood_risk
        float traffic_impact
        float service_access
        float urban_risk_score
    }

    recommendations {
        int id PK
        int region_id FK
        varchar recommendation_type
        text description
        varchar urgency_level
        boolean is_active
    }

    users {
        int id PK
        varchar username
        varchar email
        varchar role
        boolean is_active
    }

    regions ||--o{ weather_data : "has"
    regions ||--o{ flood_events : "has"
    regions ||--o{ roads : "has"
    regions ||--o{ public_facilities : "has"
    regions ||--o{ risk_scores : "has"
    regions ||--o{ recommendations : "has"
```

---

## Cara Render Diagram

Diagram di atas menggunakan **Mermaid syntax** yang otomatis dirender menjadi visual di:

| Platform         | Cara                                                 |
| ---------------- | ---------------------------------------------------- |
| **GitHub**       | Buka file `.md` di repo — otomatis render            |
| **VS Code**      | Install extension "Markdown Preview Mermaid Support" |
| **Notion**       | Paste ke code block, pilih bahasa `mermaid`          |
| **Mermaid Live** | https://mermaid.live — paste dan export PNG/SVG      |
| **draw.io**      | Import via Extras → Edit Diagram                     |

> Untuk presentasi: buka https://mermaid.live, paste tiap diagram, export sebagai PNG beresolusi tinggi, lalu masukkan ke slide PowerPoint.

---

_URIS-AI · Urban Risk Intelligence System · 2026_  
_Live: https://urisai-api-zgwts4p3va-as.a.run.app_  
_GitHub: https://github.com/rathaavle/uris-ai_
