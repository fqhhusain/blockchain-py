# Blockchain Python

<p align="center">
  Flask-based educational blockchain with ECDSA digital signatures, mining rewards, and 3-node consensus simulation.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11%2B-blue" alt="Python">
  <img src="https://img.shields.io/badge/Flask-3.0-black" alt="Flask">
  <img src="https://img.shields.io/badge/Crypto-ECDSA%20SECP256K1-green" alt="Crypto">
  <img src="https://img.shields.io/badge/Tests-129%20passed-brightgreen" alt="Tests">
</p>

## Table of Contents
- [Blockchain Python](#blockchain-python)
  - [Table of Contents](#table-of-contents)
  - [About The Project](#about-the-project)
  - [Architecture](#architecture)
  ## About The Project

## About The Project

Proyek ini adalah implementasi sistem **Blockchain** sederhana yang dibangun menggunakan **Python** dan **Flask** untuk tujuan edukasi. Proyek ini mendemonstrasikan secara langsung bagaimana mekanisme inti di balik mata uang kripto (seperti Bitcoin) beroperasi di tingkat kode. 

Melalui proyek ini, pengguna dapat memahami siklus hidup sebuah transaksi dari hulu ke hilir, mulai dari pembuatan dompet hingga pencatatan permanen di dalam blok.

**Sorotan Fitur Utama:**
* **Keamanan Kriptografi (ECDSA SECP256K1):** Pembuatan sepasang kunci (Public/Private Key) dan validasi tanda tangan digital untuk memastikan setiap transaksi hanya dapat dilakukan oleh pemilik sah.
* **Sistem Penambangan (Proof-of-Work):** Simulasi proses *mining* di mana komputer harus memecahkan teka-teki kriptografi (mencari nilai *Hash* dengan target tertentu) untuk menambahkan blok baru, lengkap dengan pemberian *Mining Reward* (Coinbase).
* **Simulasi Jaringan Terdesentralisasi:** Mendukung operasional pada 3 *node* (server) yang berbeda, lengkap dengan algoritma konsensus untuk mengatasi konflik dan memastikan semua *node* memiliki salinan buku besar (*ledger*) yang sama dan valid.
* **Penyimpanan Persisten:** Rantai blok dan antrean transaksi disimpan secara otomatis menggunakan format JSON agar data tidak hilang saat server dimatikan.

Proyek ini sangat cocok dijadikan bahan pembelajaran bagi siapa saja yang ingin mendalami arsitektur dasar dan keamanan sistem desentralisasi.

**Anggota Kelompok:**

| Nama | NRP |
| :--- | :--- |
| Evand Khan | 5006231003 |
| Amoes Noland | 5027231028 |
| Muhammad Faqih Husain | 5027231023 |

**Anggota Kelompok:**

| Nama | NRP |
| :--- | :--- |
| Evand Khan | 5006231003 |
| Amoes Noland | 5027231028 |
| Muhammad Faqih Husain | 5027231023 |

## Architecture

## Table of Contents

- [Blockchain Python](#blockchain-python)
  - [Table of Contents](#table-of-contents)
  - [About The Project](#about-the-project)
  - [Architecture](#architecture)
  - [Built With](#built-with)
  - [Features](#features)
  - [Getting Started](#getting-started)
    - [Prerequisites](#prerequisites)
    - [Installation](#installation)
    - [Run 3 Nodes (Recommended)](#run-3-nodes-recommended)
    - [Run Manually](#run-manually)
    - [Opsi Persistensi](#opsi-persistensi)
    - [Postman Collection](#postman-collection)
    - [Quick Demo Script (Optional)](#quick-demo-script-optional)
  - [API Overview](#api-overview)
  - [Testing](#testing)
  - [Assignment Coverage](#assignment-coverage)
  - [Project Structure](#project-structure)
  - [Known Limitations](#known-limitations)
  - [Documentation](#documentation)

## About The Project

This project implements a simplified blockchain network in Python for academic use.

Main goals:
- Secure transactions using ECDSA signatures.
- Reward miners with coinbase transactions.
- Simulate at least 3 nodes with peer registration and consensus.
- Expose blockchain operations via Flask API and test with Postman.

## Architecture

![Blockchain Architecture](img/blockchain_architecture.svg)

High-level flow:
- Each node runs its own Flask app and local blockchain state.
- Transactions are validated before entering pending pool.
- Valid transactions are broadcast to peers so pending pools stay in sync.
- Mining seals pending transactions into a new block and adds miner reward.
- Nodes synchronize using longest valid chain (Nakamoto-style consensus).

## Built With

- Python 3.11+
- Flask 3.0
- cryptography (ECDSA SECP256K1 + SHA-256)
- requests
- pytest + pytest-cov

## Features

- Digital signature verification per transaction.
- Sender ownership enforcement: sender address must match submitted public key.
- Proof-of-Work mining with configurable difficulty.
- Automatic miner reward transaction (coinbase).
- Multi-node consensus (`/nodes/register`, `/nodes/resolve`).
- Pending transaction propagation (`/transactions/new` broadcast to peers).
- Duplicate pending transaction rejection (prevents rebroadcast loops).
- Wallet keypair generation endpoint.
- Unit, functional, and integration tests.

## Getting Started

### Prerequisites

- Python 3.11+
- pip

### Installation

```bash
python -m pip install -r requirements.txt
```

### Run 3 Nodes (Recommended)

```bash
bash run_nodes.sh
```

This script starts nodes on ports 5000, 5001, 5002 and auto-registers peers.

Optional: enable persistent storage per node (JSON files):

```bash
BC_PERSIST=1 BC_DATA_DIR=.data bash run_nodes.sh
```

### Run Manually

```bash
# Terminal 1
cd src && python app.py --port 5000

# Terminal 2
cd src && python app.py --port 5001

# Terminal 3
cd src && python app.py --port 5002
```

### Opsi Persistensi 

Secara default state blockchain disimpan in-memory. Untuk menyimpan chain dan pending pool per node ke file JSON:

```bash
BC_PERSIST=1 BC_DATA_DIR=.data bash run_nodes.sh
```

Catatan perilaku konsensus saat persistensi aktif:
- Ketika node mengadopsi chain peer yang lebih panjang (`/nodes/resolve`), state lokal diganti.
- Pending pool lokal di-reset, lalu state baru langsung disimpan ke file node terkait.

### Postman Collection

Import:
- `src/postman_collection.json`

### Quick Demo Script (Optional)

Run a human-readable end-to-end demo flow:

```bash
bash demo.sh
```

Customize parameters easily:

```bash
RECEIVER=Bob AMOUNT=7.5 MINER_ADDRESS=Alice bash demo.sh
```

Auto-start nodes inside demo (instead of running `run_nodes.sh` first):

```bash
AUTO_START_NODES=1 WAIT_AFTER_START=4 bash demo.sh
```

## API Overview

| Method | Endpoint | Description |
|---|---|---|
| GET | `/wallet/new` | Generate ECDSA key pair |
| POST | `/transactions/new` | Submit signed transaction |
| POST | `/transactions/verify` | Verify signature without enqueue |
| POST | `/mine` | Mine block and issue reward |
| GET | `/chain` | Get full blockchain |
| GET | `/chain/validate` | Validate current chain |
| GET | `/balance/<address>` | Get confirmed balance |
| GET | `/nodes` | List known peers |
| POST | `/nodes/register` | Register peers |
| GET | `/nodes/resolve` | Run consensus |

## Testing

Run all tests:

```bash
pytest -q
```

Latest local result:
- 129 passed

Test layers:
- Unit tests: core business logic.
- Functional tests: Flask endpoint behavior.
- Integration tests: 3-node sync and consensus scenarios.

## Assignment Coverage

Required tasks and status:

1. Add digital signature: Completed.
2. Add mining reward: Completed.
3. Build at least 3 nodes: Completed.
4. Use Flask API + Postman simulation: Completed.

Required outputs and status:

1. Source code project: Completed.
2. Markdown documentation: Completed.
3. Test evidence in markdown (transaction, mining, reward, signature validation, node sync): Completed in `DOKUMENTASI.md`.

## Project Structure

```text
blockchain-py/
├── README.md
├── DOKUMENTASI.md
├── requirements.txt
├── run_nodes.sh
├── img/
│   └── blockchain_architecture.svg
└── src/
        ├── app.py
        ├── config.py
        ├── core/
        ├── network/
        ├── routes/
        ├── tests/
        └── postman_collection.json
```

## Known Limitations

- Default mode uses in-memory blockchain state: node restart resets local chain and pending pool.
- No authentication/authorization layer for API endpoints.
- Educational consensus model: focuses on longest valid chain, not production networking hardening.
- Local/demo environment assumptions (localhost peers, no TLS, no identity management).

## Documentation

- Full technical walkthrough and step-by-step Postman validation:
    - `DOKUMENTASI.md`
