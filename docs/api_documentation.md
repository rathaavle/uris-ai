# URIS-AI API Documentation

**Version:** 1.0.0  
**Base URL:** `https://api.uris-ai.azure.com` (Production)  
**Base URL:** `https://api-staging.uris-ai.azure.com` (Staging)

## Overview

URIS-AI (Urban Risk Intelligence System for Flood-Aware Mobility and Public Service Optimization) menyediakan REST API untuk mengakses prediksi risiko banjir, analisis dampak lalu lintas, dan rekomendasi tindakan untuk wilayah Jakarta dan Jawa Barat.

**Fitur Utama:**

- Prediksi risiko banjir real-time per wilayah
- Analisis dampak lalu lintas akibat banjir
- Rekomendasi rute aman
- Monitoring aksesibilitas fasilitas publik
- Urban Risk Score terpadu (0-100)

**Requirements:** 6.4

---

## Authentication

Semua endpoint API (kecuali `/health` dan `/`) memerlukan autentikasi menggunakan JWT Bearer token.

### POST /auth/login

Autentikasi pengguna dan dapatkan JWT access token.

**Request Body:**

```json
{
  "username": "string",
  "password": "string"
}
```

**Response 200 OK:**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600,
  "role": "government"
}
```

**Response 401 Unauthorized:**

```json
{
  "detail": "Username atau password salah"
}
```

**Response 403 Forbidden:**

```json
{
  "detail": "Akun pengguna tidak aktif"
}
```

**Example cURL:**

```bash
curl -X POST "https://api.uris-ai.azure.com/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin@bpbd.jakarta.go.id",
    "password": "SecurePassword123!"
  }'
```

**Example Python:**

```python
import requests

response = requests.post(
    "https://api.uris-ai.azure.com/auth/login",
    json={
        "username": "admin@bpbd.jakarta.go.id",
        "password": "SecurePassword123!"
    }
)
token = response.json()["access_token"]
```

---

### POST /auth/logout

Logout pengguna saat ini. Token harus di-invalidate di sisi klien.

**Headers:**

```
Authorization: Bearer <access_token>
```

**Response 200 OK:**

```json
{
  "message": "Berhasil logout"
}
```

**Example cURL:**

```bash
curl -X POST "https://api.uris-ai.azure.com/auth/logout" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

---

## Users

### GET /users/me

Dapatkan informasi profil pengguna yang sedang login.

**Headers:**

```
Authorization: Bearer <access_token>
```

**Response 200 OK:**

```json
{
  "id": 1,
  "username": "admin@bpbd.jakarta.go.id",
  "email": "admin@bpbd.jakarta.go.id",
  "role": "government",
  "created_at": "2024-01-15T08:30:00Z",
  "last_login": "2024-01-20T14:25:30Z",
  "is_active": true
}
```

**Roles:**

- `public` - Masyarakat umum (akses terbatas)
- `facility_manager` - Pengelola fasilitas publik
- `government` - Petugas pemerintah (BPBD, Dinas Perhubungan)

**Example cURL:**

```bash
curl -X GET "https://api.uris-ai.azure.com/users/me" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

---

## Risk Endpoints

### GET /regions/{region_id}/risk

Dapatkan Urban Risk Score terbaru untuk wilayah tertentu.

**Path Parameters:**

- `region_id` (integer, required) - ID wilayah

**Headers:**

```
Authorization: Bearer <access_token>
```

**Response 200 OK:**

```json
{
  "region_id": 3174010,
  "region_name": "Kelurahan Menteng, Jakarta Pusat",
  "flood_risk": 75.5,
  "traffic_impact": 62.3,
  "service_access": 45.8,
  "urban_risk_score": 68.2,
  "risk_category": "TINGGI",
  "calculated_at": "2024-01-20T14:30:00Z"
}
```

**Response 404 Not Found:**

```json
{
  "detail": "Wilayah dengan ID 9999999 tidak ditemukan"
}
```

**Risk Categories:**

- `RENDAH` - Urban Risk Score 0-30
- `SEDANG` - Urban Risk Score 31-60
- `TINGGI` - Urban Risk Score 61-85
- `KRITIS` - Urban Risk Score 86-100

**Example cURL:**

```bash
curl -X GET "https://api.uris-ai.azure.com/regions/3174010/risk" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

**Example Python:**

```python
import requests

headers = {"Authorization": f"Bearer {token}"}
response = requests.get(
    "https://api.uris-ai.azure.com/regions/3174010/risk",
    headers=headers
)
risk_data = response.json()
print(f"Urban Risk Score: {risk_data['urban_risk_score']}")
print(f"Category: {risk_data['risk_category']}")
```

---

### GET /regions/risk

Dapatkan Urban Risk Score terbaru untuk semua wilayah.

**Headers:**

```
Authorization: Bearer <access_token>
```

**Response 200 OK:**

```json
{
  "regions": [
    {
      "region_id": 3174010,
      "region_name": "Kelurahan Menteng, Jakarta Pusat",
      "flood_risk": 75.5,
      "traffic_impact": 62.3,
      "service_access": 45.8,
      "urban_risk_score": 68.2,
      "risk_category": "TINGGI",
      "calculated_at": "2024-01-20T14:30:00Z"
    },
    {
      "region_id": 3174020,
      "region_name": "Kelurahan Gambir, Jakarta Pusat",
      "flood_risk": 45.2,
      "traffic_impact": 38.5,
      "service_access": 25.3,
      "urban_risk_score": 42.1,
      "risk_category": "SEDANG",
      "calculated_at": "2024-01-20T14:30:00Z"
    }
  ],
  "total": 2,
  "updated_at": "2024-01-20T14:30:00Z"
}
```

**Example cURL:**

```bash
curl -X GET "https://api.uris-ai.azure.com/regions/risk" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

**Use Case:** Endpoint ini ideal untuk membuat visualisasi peta choropleth yang menampilkan risiko seluruh wilayah.

---

### GET /regions/{region_id}/risk/trend

Dapatkan tren Urban Risk Score untuk wilayah dalam rentang waktu tertentu.

**Path Parameters:**

- `region_id` (integer, required) - ID wilayah

**Query Parameters:**

- `hours` (integer, optional, default=24) - Rentang waktu dalam jam (1-168)

**Headers:**

```
Authorization: Bearer <access_token>
```

**Response 200 OK:**

```json
{
  "region_id": 3174010,
  "region_name": "Kelurahan Menteng, Jakarta Pusat",
  "hours": 24,
  "trend": [
    {
      "date": "2024-01-19T14:30:00Z",
      "urban_risk_score": 45.2
    },
    {
      "date": "2024-01-19T15:30:00Z",
      "urban_risk_score": 52.8
    },
    {
      "date": "2024-01-19T16:30:00Z",
      "urban_risk_score": 61.5
    },
    {
      "date": "2024-01-20T14:30:00Z",
      "urban_risk_score": 68.2
    }
  ]
}
```

**Response 404 Not Found:**

```json
{
  "detail": "Wilayah dengan ID 9999999 tidak ditemukan"
}
```

**Example cURL:**

```bash
curl -X GET "https://api.uris-ai.azure.com/regions/3174010/risk/trend?hours=48" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

**Example Python:**

```python
import requests
import matplotlib.pyplot as plt
from datetime import datetime

headers = {"Authorization": f"Bearer {token}"}
response = requests.get(
    "https://api.uris-ai.azure.com/regions/3174010/risk/trend?hours=48",
    headers=headers
)
data = response.json()

# Plot trend
dates = [datetime.fromisoformat(p["date"].replace("Z", "+00:00")) for p in data["trend"]]
scores = [p["urban_risk_score"] for p in data["trend"]]

plt.plot(dates, scores)
plt.xlabel("Waktu")
plt.ylabel("Urban Risk Score")
plt.title(f"Tren Risiko - {data['region_name']}")
plt.show()
```

---

## Recommendations

### GET /regions/{region_id}/recommendations

Dapatkan daftar rekomendasi aktif untuk wilayah tertentu.

**Path Parameters:**

- `region_id` (integer, required) - ID wilayah

**Headers:**

```
Authorization: Bearer <access_token>
```

**Response 200 OK:**

```json
{
  "region_id": 3174010,
  "region_name": "Kelurahan Menteng, Jakarta Pusat",
  "recommendations": [
    {
      "id": 1,
      "region_id": 3174010,
      "type": "alert",
      "description": "Potensi banjir tinggi dalam 2 jam ke depan. Hindari perjalanan ke wilayah ini.",
      "urgency": "Segera",
      "created_at": "2024-01-20T14:30:00Z",
      "expires_at": "2024-01-20T16:30:00Z",
      "metadata": {
        "expected_water_level": "50cm",
        "affected_roads": ["Jl. Sudirman", "Jl. Thamrin"]
      }
    },
    {
      "id": 2,
      "region_id": 3174010,
      "type": "route",
      "description": "Gunakan rute alternatif melalui Jl. Gatot Subroto untuk menghindari kemacetan.",
      "urgency": "Waspada",
      "created_at": "2024-01-20T14:30:00Z",
      "expires_at": "2024-01-20T18:00:00Z",
      "metadata": null
    }
  ],
  "total": 2
}
```

**Response 404 Not Found:**

```json
{
  "detail": "Wilayah dengan ID 9999999 tidak ditemukan"
}
```

**Recommendation Types:**

- `alert` - Peringatan umum
- `route` - Rekomendasi rute alternatif
- `service` - Informasi fasilitas publik alternatif

**Urgency Levels:**

- `Segera` - Tindakan diperlukan dalam 1 jam
- `Waspada` - Tindakan diperlukan dalam 1-6 jam
- `Siaga` - Tindakan diperlukan dalam 6-24 jam

**Example cURL:**

```bash
curl -X GET "https://api.uris-ai.azure.com/regions/3174010/recommendations" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

---

### POST /routes/safe

Temukan rute aman dari titik asal ke tujuan yang menghindari wilayah berisiko tinggi.

**Headers:**

```
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Request Body:**

```json
{
  "origin": {
    "latitude": -6.2088,
    "longitude": 106.8456
  },
  "destination": {
    "latitude": -6.1751,
    "longitude": 106.865
  }
}
```

**Response 200 OK (Safe Route Found):**

```json
{
  "origin": {
    "latitude": -6.2088,
    "longitude": 106.8456
  },
  "destination": {
    "latitude": -6.1751,
    "longitude": 106.865
  },
  "is_safe": true,
  "route_region_ids": [3174010, 3174020, 3174030],
  "avoided_regions": [3174015, 3174025],
  "no_safe_route_reason": null,
  "estimated_recovery_hours": null
}
```

**Response 200 OK (No Safe Route):**

```json
{
  "origin": {
    "latitude": -6.2088,
    "longitude": 106.8456
  },
  "destination": {
    "latitude": -6.1751,
    "longitude": 106.865
  },
  "is_safe": false,
  "route_region_ids": [],
  "avoided_regions": [3174010, 3174015, 3174020, 3174025],
  "no_safe_route_reason": "Semua rute menuju tujuan melewati wilayah dengan risiko Tinggi atau Kritis",
  "estimated_recovery_hours": 6.5
}
```

**Response 422 Unprocessable Entity:**

```json
{
  "detail": "Data permintaan tidak valid",
  "errors": [
    {
      "loc": ["body", "origin", "latitude"],
      "msg": "Input should be less than or equal to 90",
      "type": "less_than_equal"
    }
  ]
}
```

**Example cURL:**

```bash
curl -X POST "https://api.uris-ai.azure.com/routes/safe" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Content-Type: application/json" \
  -d '{
    "origin": {"latitude": -6.2088, "longitude": 106.8456},
    "destination": {"latitude": -6.1751, "longitude": 106.8650}
  }'
```

**Example Python:**

```python
import requests

headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}
payload = {
    "origin": {"latitude": -6.2088, "longitude": 106.8456},
    "destination": {"latitude": -6.1751, "longitude": 106.8650}
}

response = requests.post(
    "https://api.uris-ai.azure.com/routes/safe",
    headers=headers,
    json=payload
)
route = response.json()

if route["is_safe"]:
    print(f"Rute aman ditemukan melalui {len(route['route_region_ids'])} wilayah")
    print(f"Menghindari {len(route['avoided_regions'])} wilayah berisiko tinggi")
else:
    print(f"Tidak ada rute aman: {route['no_safe_route_reason']}")
    print(f"Estimasi pemulihan: {route['estimated_recovery_hours']} jam")
```

---

## Health & System

### GET /

Root endpoint - informasi dasar aplikasi.

**Response 200 OK:**

```json
{
  "name": "URIS-AI",
  "version": "1.0.0",
  "status": "running"
}
```

**Example cURL:**

```bash
curl -X GET "https://api.uris-ai.azure.com/"
```

---

### GET /health

Basic health check - selalu mengembalikan 200 jika aplikasi berjalan.

**Response 200 OK:**

```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2024-01-20T14:30:00Z"
}
```

**Example cURL:**

```bash
curl -X GET "https://api.uris-ai.azure.com/health"
```

---

### GET /health/ready

Readiness check - verifikasi konektivitas ke layanan dependen.

**Response 200 OK:**

```json
{
  "status": "ready",
  "checks": {
    "database": "ok",
    "cache": "ok",
    "monitoring": "ok"
  },
  "timestamp": "2024-01-20T14:30:00Z"
}
```

**Response 503 Service Unavailable:**

```json
{
  "status": "not_ready",
  "checks": {
    "database": "error",
    "cache": "ok",
    "monitoring": "ok"
  },
  "timestamp": "2024-01-20T14:30:00Z"
}
```

**Use Case:** Kubernetes/Azure menggunakan endpoint ini untuk menentukan apakah pod/instance siap menerima traffic.

---

### GET /health/live

Liveness check - konfirmasi proses aplikasi masih hidup.

**Response 200 OK:**

```json
{
  "status": "alive",
  "timestamp": "2024-01-20T14:30:00Z"
}
```

**Use Case:** Kubernetes/Azure menggunakan endpoint ini untuk menentukan apakah pod/instance perlu di-restart.

---

## Error Responses

Semua error mengikuti format standar:

**400 Bad Request:**

```json
{
  "detail": "Parameter tidak valid"
}
```

**401 Unauthorized:**

```json
{
  "detail": "Token tidak valid atau telah kadaluarsa"
}
```

**403 Forbidden:**

```json
{
  "detail": "Akses tidak diizinkan untuk peran Anda"
}
```

**404 Not Found:**

```json
{
  "detail": "Resource tidak ditemukan"
}
```

**422 Unprocessable Entity:**

```json
{
  "detail": "Data permintaan tidak valid",
  "errors": [
    {
      "loc": ["body", "field_name"],
      "msg": "Error message",
      "type": "error_type"
    }
  ]
}
```

**500 Internal Server Error:**

```json
{
  "detail": "Terjadi kesalahan internal pada server"
}
```

**503 Service Unavailable:**

```json
{
  "detail": "Layanan sementara tidak tersedia"
}
```

---

## Rate Limiting

API menerapkan rate limiting untuk mencegah penyalahgunaan:

- **Per Minute:** 60 requests per IP address
- **Per Hour:** 1000 requests per IP address

Jika limit terlampaui, API akan mengembalikan:

**429 Too Many Requests:**

```json
{
  "detail": "Terlalu banyak permintaan. Coba lagi dalam beberapa saat."
}
```

**Headers:**

```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1705761600
```

---

## OpenAPI Specification

Dokumentasi interaktif tersedia di:

- **Swagger UI:** `https://api.uris-ai.azure.com/docs`
- **ReDoc:** `https://api.uris-ai.azure.com/redoc`
- **OpenAPI JSON:** `https://api.uris-ai.azure.com/openapi.json`

---

## SDK & Client Libraries

### Python Client Example

```python
import requests
from typing import Optional

class URISAIClient:
    def __init__(self, base_url: str, username: str, password: str):
        self.base_url = base_url
        self.token: Optional[str] = None
        self.login(username, password)

    def login(self, username: str, password: str):
        response = requests.post(
            f"{self.base_url}/auth/login",
            json={"username": username, "password": password}
        )
        response.raise_for_status()
        self.token = response.json()["access_token"]

    def _headers(self):
        return {"Authorization": f"Bearer {self.token}"}

    def get_region_risk(self, region_id: int):
        response = requests.get(
            f"{self.base_url}/regions/{region_id}/risk",
            headers=self._headers()
        )
        response.raise_for_status()
        return response.json()

    def get_all_risks(self):
        response = requests.get(
            f"{self.base_url}/regions/risk",
            headers=self._headers()
        )
        response.raise_for_status()
        return response.json()

    def find_safe_route(self, origin_lat: float, origin_lon: float,
                       dest_lat: float, dest_lon: float):
        response = requests.post(
            f"{self.base_url}/routes/safe",
            headers=self._headers(),
            json={
                "origin": {"latitude": origin_lat, "longitude": origin_lon},
                "destination": {"latitude": dest_lat, "longitude": dest_lon}
            }
        )
        response.raise_for_status()
        return response.json()

# Usage
client = URISAIClient(
    base_url="https://api.uris-ai.azure.com",
    username="admin@bpbd.jakarta.go.id",
    password="SecurePassword123!"
)

# Get risk for specific region
risk = client.get_region_risk(3174010)
print(f"Urban Risk Score: {risk['urban_risk_score']}")

# Find safe route
route = client.find_safe_route(
    origin_lat=-6.2088, origin_lon=106.8456,
    dest_lat=-6.1751, dest_lon=106.8650
)
print(f"Safe route found: {route['is_safe']}")
```

---

## Support

Untuk pertanyaan atau masalah terkait API:

- **Email:** api-support@uris-ai.go.id
- **Documentation:** https://docs.uris-ai.go.id
- **Status Page:** https://status.uris-ai.go.id

---

**Last Updated:** 2024-01-20  
**API Version:** 1.0.0
