# Dokumentasi Blockchain Python — Flask API + 3 Node Network

> **Tugas:** Implementasi Blockchain dengan Digital Signature, Mining Reward, 3 Node, dan Flask API  
> **Stack:** Python 3.11 · Flask 3.0 · ECDSA (SECP256K1) · Proof-of-Work

---

## Daftar Isi

1. [Arsitektur Sistem](#1-arsitektur-sistem)
2. [Struktur Direktori](#2-struktur-direktori)
3. [Cara Menjalankan](#3-cara-menjalankan)
4. [Endpoint API](#4-endpoint-api)
5. [Pengujian dengan Postman](#5-pengujian-dengan-postman)
   - [5.1 Generate Wallet & Penambahan Transaksi](#51-generate-wallet--penambahan-transaksi)
   - [5.2 Proses Mining](#52-proses-mining)
   - [5.3 Reward Miner](#53-reward-miner)
   - [5.4 Validasi Digital Signature](#54-validasi-digital-signature)
   - [5.5 Sinkronisasi Antar-Node](#55-sinkronisasi-antar-node)
6. [Penjelasan Fitur](#6-penjelasan-fitur)
7. [Alur Kerja Lengkap](#7-alur-kerja-lengkap)

---

## 1. Arsitektur Sistem

![Blockchain Architecture](img/blockchain_architecture.svg)

### Komponen Utama

| Layer | File | Fungsi |
|-------|------|--------|
| **Core** | `core/wallet.py` | ECDSA keygen, sign, verify |
| **Core** | `core/transaction.py` | Model transaksi + validasi signature |
| **Core** | `core/block.py` | Model block + Proof-of-Work |
| **Core** | `core/blockchain.py` | Manajemen chain, pool, mining |
| **Network** | `network/node.py` | Registry peer per node |
| **Network** | `network/consensus.py` | Nakamoto consensus |
| **Network** | `network/network_utils.py` | HTTP broadcast antar node |
| **Routes** | `routes/transactions.py` | `POST /transactions/new` |
| **Routes** | `routes/mine.py` | `POST /mine` |
| **Routes** | `routes/chain.py` | `GET /chain`, `GET /chain/validate` |
| **Routes** | `routes/nodes.py` | `POST /nodes/register`, `GET /nodes/resolve` |
| **Routes** | `routes/wallet.py` | `GET /wallet/new`, `POST /transactions/verify` |

---

## 2. Struktur Direktori

```
blockchain-py/
├── demo.sh                   ← demo end-to-end flow
├── sign_tx.py                ← helper signing script untuk Postman demo
├── requirements.txt          ← flask, cryptography, requests
├── run_nodes.sh              ← spawn 3 node sekaligus (port 5000, 5001, 5002)
├── README.md
├── DOKUMENTASI.md            ← file ini
└── src/
    ├── config.py             ← DIFFICULTY=3, MINING_REWARD=10, DEFAULT_PORT=5000
    ├── app.py                ← Flask factory + blueprint registration
    ├── conftest.py           ← helper import path untuk pytest
    │
    ├── core/
    │   ├── wallet.py         ← generate_keys(), sign(), verify()
    │   ├── transaction.py    ← Transaction + sign_transaction() + is_valid()
    │   ├── block.py          ← Block + calculate_hash() + mine_block()
    │   └── blockchain.py     ← Blockchain + add_transaction() + mine_pending_transactions()
    │
    ├── network/
    │   ├── node.py           ← Node (peer registry, node_id)
    │   ├── consensus.py      ← resolve_conflicts() — longest chain rule
    │   └── network_utils.py  ← fetch_chain(), broadcast_transaction(), broadcast_new_block()
    │
    ├── routes/
    │   ├── transactions.py   ← POST /transactions/new
    │   ├── mine.py           ← POST /mine
    │   ├── chain.py          ← GET /chain, GET /chain/validate, GET /balance/<address>
    │   ├── nodes.py          ← GET /nodes, POST /nodes/register, GET /nodes/resolve
    │   └── wallet.py         ← GET /wallet/new, POST /transactions/verify
    │
    ├── postman_collection.json
    │
    └── tests/
        ├── unit/             ← test_wallet, test_transaction, test_block, test_blockchain
        ├── functional/       ← test_api_transactions, test_api_mine, test_api_chain, test_api_nodes
        └── integration/      ← test_multi_node (3 node end-to-end)
```

---

## 3. Cara Menjalankan

### Prasyarat

```bash
python -m pip install -r requirements.txt
```

### Opsi A — Jalankan 3 Node Sekaligus (Direkomendasikan)

```bash
bash run_nodes.sh
```

Script ini akan:
1. Menjalankan 3 proses Flask di port 5000, 5001, 5002
2. Secara otomatis mendaftarkan peer antar node (full mesh)
3. Menampilkan URL semua node

### Opsi B — Jalankan Manual (Tiap Terminal)

```bash
# Terminal 1
cd src && python app.py --port 5000

# Terminal 2
cd src && python app.py --port 5001

# Terminal 3
cd src && python app.py --port 5002
```

### Opsi Persistensi (Opsional)

Secara default state blockchain disimpan in-memory. Untuk menyimpan chain dan pending pool per node ke file JSON:

```bash
BC_PERSIST=1 BC_DATA_DIR=.data bash run_nodes.sh
```

Catatan perilaku konsensus saat persistensi aktif:
- Ketika node mengadopsi chain peer yang lebih panjang (`/nodes/resolve`), state lokal diganti.
- Pending pool lokal di-reset, lalu state baru langsung disimpan ke file node terkait.

### Import Postman Collection

1. Buka Postman → klik **Import**
2. Pilih file `src/postman_collection.json`
3. Collection **"Blockchain Python — 3 Node Network"** akan muncul
4. Variabel environment `node1`, `node2`, `node3` sudah dikonfigurasi

---

## 4. Endpoint API

| Method | Endpoint | Deskripsi |
|--------|----------|-----------|
| `GET` | `/wallet/new` | Generate ECDSA key pair baru |
| `POST` | `/transactions/new` | Tambah transaksi bertandatangan ke pool |
| `POST` | `/transactions/verify` | Verifikasi signature tanpa menambah ke pool |
| `POST` | `/mine` | Mine block + reward otomatis ke miner |
| `GET` | `/chain` | Tampilkan seluruh blockchain |
| `GET` | `/chain/validate` | Validasi integritas chain |
| `GET` | `/balance/<address>` | Saldo terkonfirmasi suatu address |
| `GET` | `/nodes` | Daftar peer yang dikenal node ini |
| `POST` | `/nodes/register` | Daftarkan peer baru |
| `GET` | `/nodes/resolve` | Jalankan Nakamoto consensus |

---

## 5. Pengujian dengan Postman

> **Setup:** Jalankan `bash run_nodes.sh` terlebih dahulu. Import `postman_collection.json` ke Postman.

---

### 5.1 Generate Wallet & Penambahan Transaksi

#### Langkah 1 — Generate Wallet Alice

**Request:**
```
GET http://localhost:5000/wallet/new
```

**Response `200 OK`:**
```json
{
  "private_key": "-----BEGIN PRIVATE KEY-----\nMIGHAgEAMBMGByqGSM49AgEGCCqGSM49AwEHBG0wawIBAQQgK2xN\npvBqMF8X...3lZQDNIBzg==\n-----END PRIVATE KEY-----\n",
  "public_key": "-----BEGIN PUBLIC KEY-----\nMFYwEAYHKoZIzj0CAQYFK4EEAAoDQgAExY3kPqM8sVW7N2f4hLkI\ncYw5A3t...Qp==\n-----END PUBLIC KEY-----\n",
  "address": "MFYwEAYHKoZIzj0CAQYFK4EEAAoDQgAE"
}
```

> 💡 **Simpan** nilai `private_key`, `public_key`, dan `address`. Ketiganya dibutuhkan untuk langkah selanjutnya.

---

#### Langkah 2 — Buat Signature (Script Python)

Karena Postman tidak bisa menghitung ECDSA signature secara native, gunakan script helper berikut di terminal:

```python
# sign_tx.py — jalankan: python sign_tx.py
import json, binascii
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec

PRIVATE_KEY_PEM = """-----BEGIN PRIVATE KEY-----
MIGHAgEAMBMGByqGSM49AgEGCCqGSM49AwEHBG0wawIBAQQgK2xN...
-----END PRIVATE KEY-----
"""

tx = {"sender": "MFYwEAYHKoZIzj0CAQYFK4EEAAoDQgAE", "receiver": "Bob", "amount": 50}
message = json.dumps(tx, sort_keys=True).encode("utf-8")

private_key = serialization.load_pem_private_key(
    PRIVATE_KEY_PEM.encode(), password=None, backend=default_backend()
)
sig_bytes = private_key.sign(message, ec.ECDSA(hashes.SHA256()))
print("signature:", binascii.hexlify(sig_bytes).decode())
```

**Output contoh:**
```
signature: 3046022100d4c7f8a9b2e1f03056c7d8a91b2e3f408c4a5b6c7d8e9f0a1b2c3d4e5f6022100a1b2c3d4e5f6789...
```

---

#### Langkah 3 — Kirim Transaksi Valid

**Request:**
```
POST http://localhost:5000/transactions/new
Content-Type: application/json
```

**Body:**
```json
{
  "sender": "MFYwEAYHKoZIzj0CAQYFK4EEAAoDQgAE",
  "receiver": "Bob",
  "amount": 50,
  "public_key": "-----BEGIN PUBLIC KEY-----\nMFYwEAYHKoZIzj0CAQYFK4EEAAoDQgAExY3kPqM8sVW7N2f4hLkI...\n-----END PUBLIC KEY-----\n",
  "signature": "3046022100d4c7f8a9b2e1f03056c7d8a91b2e3f408c4a5b6c7d8e9f0a1b2c3d4e5f602..."
}
```

**Response `201 Created`:**
```json
{
  "message": "Transaction added to the pending pool",
  "pending_count": 1
}
```

---

### 5.2 Proses Mining

#### Mine Block di Node 1

**Request:**
```
POST http://localhost:5000/mine
Content-Type: application/json
```

**Body:**
```json
{
  "miner_address": "Alice"
}
```

**Response `200 OK`:**
```json
{
  "message": "Block mined successfully",
  "miner": "Alice",
  "chain_length": 2,
  "block": {
    "index": 1,
    "previous_hash": "000a7f4b1c2e3d8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2",
    "hash": "000e3f7d9a1c2b3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7",
    "nonce": 4821,
    "timestamp": "2026-03-25 17:01:33.482910",
    "transactions": [
      {
        "sender": "MFYwEAYHKoZIzj0CAQYFK4EEAAoDQgAE",
        "receiver": "Bob",
        "amount": 50.0,
        "signature": "3046022100d4c7...",
        "public_key": "-----BEGIN PUBLIC KEY-----\n..."
      },
      {
        "sender": "NETWORK",
        "receiver": "Alice",
        "amount": 10.0,
        "signature": null,
        "public_key": null
      }
    ]
  }
}
```

**Penjelasan hasil:**
- `hash` dimulai dengan `000` → Proof-of-Work difficulty=3 terpenuhi ✅
- `nonce: 4821` → butuh 4821 iterasi untuk menemukan hash yang valid
- Transaksi terakhir `sender: "NETWORK"` → ini adalah **coinbase reward** untuk Alice

---

#### Lihat Chain Setelah Mining

**Request:**
```
GET http://localhost:5000/chain
```

**Response `200 OK`:**
```json
{
  "chain": [
    {
      "index": 0,
      "transactions": [],
      "previous_hash": "0",
      "timestamp": "2026-03-25 17:00:00.000000",
      "nonce": 0,
      "hash": "000genesis1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7"
    },
    {
      "index": 1,
      "transactions": [
        {
          "sender": "MFYwEAYHKoZIzj0CAQYFK4EEAAoDQgAE",
          "receiver": "Bob",
          "amount": 50.0,
          "signature": "3046022100d4c7...",
          "public_key": "-----BEGIN PUBLIC KEY-----\n..."
        },
        {
          "sender": "NETWORK",
          "receiver": "Alice",
          "amount": 10.0,
          "signature": null,
          "public_key": null
        }
      ],
      "previous_hash": "000genesis1a2b3c4d...",
      "timestamp": "2026-03-25 17:01:33.482910",
      "nonce": 4821,
      "hash": "000e3f7d9a1c2b3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7"
    }
  ],
  "length": 2
}
```

---

### 5.3 Reward Miner

Setelah mining, cek saldo Alice untuk membuktikan reward diterima:

**Request:**
```
GET http://localhost:5000/balance/Alice
```

**Response `200 OK`:**
```json
{
  "address": "Alice",
  "balance": 10.0
}
```

**Cek saldo Bob** (menerima 50 koin dari transaksi):

**Request:**
```
GET http://localhost:5000/balance/Bob
```

**Response `200 OK`:**
```json
{
  "address": "Bob",
  "balance": 50.0
}
```

> ✅ **Bukti reward:** Alice mendapat **10.0 koin** (sesuai `MINING_REWARD = 10.0` di `config.py`) sebagai reward karena berhasil mine block. Transaksi reward ini berasal dari `sender: "NETWORK"` (coinbase) dan tidak membutuhkan signature.

---

### 5.4 Validasi Digital Signature

#### Test A — Signature Valid

**Request:**
```
POST http://localhost:5000/transactions/verify
Content-Type: application/json
```

**Body:**
```json
{
  "sender": "MFYwEAYHKoZIzj0CAQYFK4EEAAoDQgAE",
  "receiver": "Bob",
  "amount": 50,
  "public_key": "-----BEGIN PUBLIC KEY-----\nMFYwEAYHKoZIzj0CAQYFK4EEAAoDQgAExY3kPqM8sVW7N2f4hLkI...\n-----END PUBLIC KEY-----\n",
  "signature": "3046022100d4c7f8a9b2e1f03056c7d8a91b2e3f408c4a5b6c7d8e9f0a..."
}
```

**Response `200 OK`:**
```json
{
  "valid": true,
  "message": "Signature is VALID — transaction is authentic.",
  "transaction": {
    "sender": "MFYwEAYHKoZIzj0CAQYFK4EEAAoDQgAE",
    "receiver": "Bob",
    "amount": 50.0
  }
}
```

---

#### Test B — Signature Palsu (Ditolak)

**Request:**
```
POST http://localhost:5000/transactions/new
Content-Type: application/json
```

**Body** (menggunakan signature palsu `000000...`):
```json
{
  "sender": "Alice",
  "receiver": "Bob",
  "amount": 50,
  "public_key": "-----BEGIN PUBLIC KEY-----\nMFYwEAYHKoZIzj0CAQYFK4EEAAoDQgAE...\n-----END PUBLIC KEY-----\n",
  "signature": "000000000000000000000000000000000000000000000000000000"
}
```

**Response `400 Bad Request`:**
```json
{
  "error": "Invalid signature – transaction rejected"
}
```

---

#### Test C — Validasi Isi Chain (Semua Signature)

**Request:**
```
GET http://localhost:5000/chain/validate
```

**Response `200 OK`:**
```json
{
  "valid": true,
  "length": 2
}
```

**Cara kerja validasi (`blockchain.is_chain_valid()`):**
1. Untuk setiap block (mulai index 1): hitung ulang hash dan bandingkan dengan `block.hash` yang tersimpan
2. Periksa `block.previous_hash == prev_block.hash`
3. Untuk setiap transaksi di block: panggil `tx.is_valid()` → verifikasi ECDSA signature via `wallet.verify()`
4. Transaksi coinbase (`sender == "NETWORK"`) dikecualikan dari pengecekan signature

---

### 5.5 Sinkronisasi Antar-Node

#### Catatan Penting: Sinkronisasi Pending Transaction

Selain sinkronisasi chain (longest-chain consensus), sistem ini juga menyinkronkan **pending transaction pool**.
Ketika Node menerima `POST /transactions/new` dan transaksi valid, Node akan broadcast transaksi yang sama ke peer melalui `network_utils.broadcast_transaction()`.

Artinya, skenario berikut sekarang didukung dengan benar:

1. Submit transaksi ke Node 1 (`:5000`)
2. Mine di Node 2 (`:5001`)
3. Transaksi dari Node 1 tetap bisa ikut termining di Node 2 karena sudah dipropagasikan ke peer

Ini lebih mendekati perilaku jaringan blockchain nyata, di mana node penerima transaksi dan node miner sering berbeda.

#### Skenario: Mine di Node 1, Sync ke Node 2 dan 3

**Langkah 1 — Pastikan Peer Terdaftar**

Cek peer Node 2:
```
GET http://localhost:5001/nodes
```

**Response:**
```json
{
  "node_id": "b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7",
  "peers": ["localhost:5000", "localhost:5002"]
}
```

Jika peer belum terdaftar (tidak menjalankan `run_nodes.sh`), daftarkan manual:

```
POST http://localhost:5001/nodes/register
```
```json
{ "nodes": ["localhost:5000", "localhost:5002"] }
```

**Response `201 Created`:**
```json
{
  "message": "2 peer(s) registered",
  "peers": ["localhost:5000", "localhost:5002"]
}
```

---

**Langkah 2 — Mine Beberapa Block di Node 1**

Mine block pertama:
```
POST http://localhost:5000/mine   →  { "miner_address": "Alice" }
```

Mine block kedua (tambah transaksi dulu, lalu mine):
```
POST http://localhost:5000/transactions/new  →  { transaksi valid }
POST http://localhost:5000/mine   →  { "miner_address": "Alice" }
```

Sekarang Node 1 punya chain length = 3, Node 2 & 3 masih = 1 (genesis).

---

#### Skenario Tambahan (Lintas-Node): Submit di Node 1, Mine di Node 2

**Langkah A — Submit transaksi ke Node 1**

```
POST http://localhost:5000/transactions/new
```

Jika valid, Node 1 menambahkan transaksi ke pending pool lokal dan langsung broadcast ke peer (`:5001`, `:5002`).

**Langkah B — Mine di Node 2**

```
POST http://localhost:5001/mine   →  { "miner_address": "Miner-Node2" }
```

Karena pending transaction sudah dipropagasikan, Node 2 dapat memasukkan transaksi tersebut ke block yang ditambang (bersama coinbase reward untuk `Miner-Node2`).

**Langkah C — Verifikasi hasil**

1. Cek `GET /chain` di Node 2, pastikan transaksi user muncul dalam block terbaru.
2. Cek `GET /nodes/resolve` di Node 1 dan Node 3 (jika belum auto-sync), lalu bandingkan hash block terakhir ketiga node.

**Bukti screenshot untuk laporan:**

1. Request/response `POST /transactions/new` di Node 1 (status `201`, `pending_count` bertambah).
2. Request/response `POST /mine` di Node 2 yang menampilkan block berisi transaksi user + reward.
3. Response `GET /chain` di Node 2 yang memperlihatkan transaksi user sudah masuk ke chain.

> ✅ Dengan alur ini, sinkronisasi yang dibuktikan bukan hanya chain setelah mining, tetapi juga propagasi transaksi sebelum mining.

---

**Langkah 3 — Cek Chain Node 2 Sebelum Sync**

```
GET http://localhost:5001/chain
```

```json
{
  "chain": [{ "index": 0, ... }],
  "length": 1
}
```

---

**Langkah 4 — Jalankan Consensus di Node 2**

```
GET http://localhost:5001/nodes/resolve
```

**Response `200 OK` — Chain diganti:**
```json
{
  "message": "Chain replaced – adopted a longer chain from a peer",
  "replaced": true,
  "chain": {
    "chain": [
      { "index": 0, "transactions": [], "hash": "000genesis...", ... },
      { "index": 1, "transactions": [...], "hash": "000e3f7d...", ... },
      { "index": 2, "transactions": [...], "hash": "000a1b2c...", ... }
    ],
    "length": 3
  }
}
```

---

**Langkah 5 — Jalankan Consensus di Node 3**

```
GET http://localhost:5002/nodes/resolve
```

**Response:**
```json
{
  "message": "Chain replaced – adopted a longer chain from a peer",
  "replaced": true,
  "chain": { "length": 3, "chain": [...] }
}
```

---

**Langkah 6 — Verifikasi Ketiga Node Punya Chain Sama**

| Node | `GET /chain` → `length` | Hash block terakhir |
|------|-------------------------|---------------------|
| Node 1 (`:5000`) | **3** | `000a1b2c3d4e...` |
| Node 2 (`:5001`) | **3** | `000a1b2c3d4e...` |
| Node 3 (`:5002`) | **3** | `000a1b2c3d4e...` |

> ✅ **Sinkronisasi berhasil** — ketiga node memiliki chain yang identik setelah consensus.

---

**Catatan tentang Auto-Broadcast:**
Sistem melakukan dua jenis broadcast otomatis:

1. Saat transaksi baru valid (`POST /transactions/new`): broadcast payload transaksi ke peer agar pending pool antar-node konsisten.
2. Saat mining berhasil (`POST /mine`): trigger `GET /nodes/resolve` pada peer agar chain cepat tersinkron.

Loop rebroadcast berhenti secara natural karena transaksi duplikat akan ditolak di pending pool (tidak ditambahkan ulang), sehingga node yang menerima duplikat tidak melakukan broadcast lanjutan.

Artinya, pada flow normal, node peer biasanya sudah sinkron baik di level pending transaction maupun chain tanpa langkah manual tambahan (kecuali node baru bergabung atau ada peer sementara offline).

---

## 6. Penjelasan Fitur

### Digital Signature (ECDSA SECP256K1)

File: `core/wallet.py`

Algoritma yang digunakan adalah **ECDSA** (Elliptic Curve Digital Signature Algorithm) dengan kurva **SECP256K1** — kurva yang sama digunakan oleh Bitcoin.

```python
# Generate key pair
private_pem, public_pem = generate_keys()

# Sign transaksi
signature_hex = sign(private_pem, {"sender": "...", "receiver": "...", "amount": 50})

# Verify
is_valid = verify(public_pem, {"sender": "...", "receiver": "...", "amount": 50}, signature_hex)
```

Setiap transaksi di `POST /transactions/new` diverifikasi sebelum masuk ke pool. Transaksi dengan signature tidak valid langsung ditolak dengan `400 Bad Request`.

---

### Mining Reward (Coinbase Transaction)

File: `core/blockchain.py`, `core/transaction.py`

Ketika `mine_pending_transactions(miner_address)` dipanggil:

```python
# Satu transaksi reward otomatis ditambahkan ke block
reward_tx = Transaction.create_reward_transaction(miner_address)
transactions_to_include = list(self.pending_transactions) + [reward_tx]
```

Transaksi coinbase ini tidak membutuhkan signature karena diterbitkan oleh jaringan itu sendiri. Nilai reward diambil dari `config.MINING_REWARD` (bisa diubah via env `BC_REWARD`).

---

### Proof-of-Work

File: `core/block.py`

```python
def mine_block(self, difficulty: int):
    target = "0" * difficulty  # e.g., "000"
    while self.hash[:difficulty] != target:
        self.nonce += 1
        self.hash = self.calculate_hash()
```

Dengan `DIFFICULTY = 3`, hash block harus dimulai dengan tiga angka nol (`000...`). Ubah nilai di `config.py` untuk menyesuaikan kecepatan mining.

---

### Nakamoto Consensus (Longest Chain Wins)

File: `network/consensus.py`

```python
def resolve_conflicts(blockchain, peers):
    max_length = len(blockchain.chain)
    new_chain = None

    for peer in peers:
        data = fetch_chain(peer)          # GET /chain dari peer
        if data is None:
            continue

        peer_length = data.get("length", 0)
        if peer_length <= max_length:
            continue

        candidate = Blockchain.from_dict(data)
        if candidate.is_chain_valid():
            max_length = peer_length
            new_chain = candidate.chain

    if new_chain is not None:
        blockchain.replace_chain(new_chain)
        return True

    return False
```

Implementasi nyata memakai `replace_chain()` (bukan assignment langsung ke `blockchain.chain`) agar penggantian chain konsisten dengan manajemen pending pool dan penyimpanan state.

---

## 7. Alur Kerja Lengkap

```
1. bash run_nodes.sh
      ↓ 3 node aktif (5000, 5001, 5002), peer terdaftar

2. GET /wallet/new  (Node 1)
      ↓ dapat private_key, public_key, address

3. Sign transaksi dengan private_key (script Python)
      ↓ dapat signature hex

4. POST /transactions/new  (Node 1)
      → server verifikasi signature
      → jika valid: masuk pending pool
  → broadcast transaksi ke Node 2 & 3
      → jika invalid: 400 rejected

5. POST /mine  { miner_address: "Alice" }  (Node 1 atau node peer lain)
      → bundle pending_transactions + coinbase reward
      → PoW: cari nonce sampai hash[:3] == "000"
      → block ditambahkan ke chain
      → broadcast ke Node 2 & 3: GET /nodes/resolve

6. GET /balance/Alice  (Node 1)
      → balance = 10.0  (reward)

7. GET /nodes/resolve  (Node 2 & 3)
      → bandingkan chain dengan peer
      → adopsi chain Node 1 (lebih panjang)
      → ketiga node sinkron

8. GET /chain/validate  (semua node)
      → valid: true
```
