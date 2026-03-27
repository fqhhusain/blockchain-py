# Dokumentasi Simulasi Blockchain - 3 Node Network

Dokumen ini berisi penjelasan arsitektur, keputusan desain, dan bukti pengujian dari sistem simulasi Blockchain yang telah dibangun. Sistem ini menggunakan arsitektur *multi-node* berbasis Flask API, menggunakan konsep kriptografi untuk mengamankan transaksi, serta mengimplementasikan *mining reward* dan konsensus jaringan.

---

## 1. Persiapan Kriptografi dan Dompet (Wallet)
Sebelum melakukan transaksi, pengguna harus membuat identitas kriptografi yang terdiri dari *Private Key* (untuk menandatangani transaksi) dan *Public Key* (untuk verifikasi).

### A. Generate Wallet
Pengujian dimulai dengan memanggil *endpoint* `/wallet/new` untuk membuat pasangan kunci (*keypair*) ECDSA SECP256K1 yang baru.
![image alt](https://github.com/fqhhusain/blockchain-py/blob/fb691b1023516327319c902bfc6da18fc5617642/img/Validasi_chain1.jpeg)

*Gambar 1: Hasil generate wallet yang memberikan Address, Private Key, dan Public Key.*

### B. Membuat Digital Signature (Tanda Tangan Digital)
Untuk memastikan keamanan, setiap transaksi harus ditandatangani menggunakan *Private Key* melalui script Python sebelum dikirim ke jaringan.
![Sign Private Key](<C:/Users/Acer/Downloads/sign privatekey utk signature.jpeg>)
*Gambar 2: Proses eksekusi script `sign_tx.py` di terminal untuk menghasilkan signature berbentuk Hexadecimal.*

---

## 2. Penambahan Transaksi & Validasi Digital Signature
Sistem harus mampu menerima transaksi yang sah dan menolak transaksi yang berusaha memalsukan tanda tangan digital.

### A. Tambah Transaksi Valid
Transaksi dikirim dengan menyertakan *signature* yang benar. Sistem memvalidasinya dan memasukkan transaksi tersebut ke dalam *pending pool* (mempool).
![New Transaction](<C:/Users/Acer/Downloads/new transaction.jpeg>)
*Gambar 3: Transaksi berhasil divalidasi dan masuk ke pending pool (Status 201 Created).*

### B. Penolakan Transaksi (Signature Palsu)
Jika seseorang mencoba mengubah *amount* atau menggunakan *signature* palsu, sistem akan langsung memblokir transaksi tersebut.
![Invalid Signature](<C:/Users/Acer/Downloads/invalid signature.jpeg>)
*Gambar 4: Sistem menolak transaksi dan mengembalikan error `INVALID_TRANSACTION_SIGNATURE` (Status 400 Bad Request).*

### C. Endpoint Khusus Verifikasi
Node juga menyediakan endpoint `/transactions/verify` untuk mengecek keabsahan sebuah *signature* tanpa harus menyimpannya ke mempool.
![Verify Signature Only](<C:/Users/Acer/Downloads/2.3 signature invalid only.jpeg>)
*Gambar 5: Hasil pengecekan signature mengembalikan nilai `valid: false` jika tidak cocok.*

---

## 3. Proses Mining & Reward Miner
Setelah transaksi terkumpul, node akan melakukan *Proof of Work* untuk menambang blok baru. 

### A. Mine Block (Menambang Blok)
Node 1 (Miner Alice) mengeksekusi *endpoint* `/mine`. Blok baru berhasil dicetak dengan membawa transaksi dari *user* serta transaksi sistem (*coinbase*) yang memberikan hadiah kepada *miner*.
![Mine Block 1](<C:/Users/Acer/Downloads/mine block 1.jpeg>)
*Gambar 6: Proses mining sukses. Terdapat transaksi dari 'NETWORK' kepada 'Alice' sebagai reward penambangan.*

### B. Memeriksa Rantai Blok (Chain) dan Validitas
Setelah ditambang, kita dapat memeriksa keseluruhan rantai blok dan memvalidasi integritas strukturnya.
![Lihat Chain](<C:/Users/Acer/Downloads/liat chain node 1.jpeg>)
*Gambar 7: Tampilan lengkap struktur Chain di Node 1 (Panjang chain: 2).*

![Validasi Chain](<C:/Users/Acer/Downloads/validasi chain 1.jpeg>)
*Gambar 8: Hasil validasi membuktikan bahwa hash dan tautan antar blok valid.*

### C. Pengecekan Saldo (*Balance*)
Karena Node 1 (Alice) berhasil menambang, ia menerima *reward* koin, sedangkan Bob menerima koin dari transaksi user.
![Cek Balance Alice](<C:/Users/Acer/Downloads/cek balance alice.jpeg>)
*Gambar 9: Saldo Alice bertambah 10 koin sebagai Mining Reward.*

![Cek Balance Bob](<C:/Users/Acer/Downloads/cek balance bob.jpeg>)
*Gambar 10: Saldo Bob bertambah 50 koin dari transaksi yang dikirim pengirim.*

---

## 4. Sinkronisasi Antar-Node (Nakamoto Consensus)
Karena blockchain adalah sistem terdesentralisasi, Node 2 dan Node 3 yang tertinggal harus bisa menyinkronkan data *ledger* mereka agar sama dengan Node 1.

### A. Pendaftaran Peer Jaringan
Node 1 telah mengenali node lainnya (port 5001 dan 5002) di dalam jaringan P2P-nya.
![List Peer Node 1](<C:/Users/Acer/Downloads/list peer node 1 (sudah register pas script se....jpeg>)
*Gambar 11: Node 1 berhasil mendata peer yang ada di jaringan.*

### B. Resolve Consensus (Sinkronisasi Rantai)
Node 2 dan Node 3 menjalankan algoritma konsensus untuk memeriksa rantai tetangganya. Karena Node 1 memiliki rantai yang lebih panjang (baru saja menambang), Node 2 dan Node 3 mengganti rantai lama mereka dengan rantai dari Node 1.
![Resolve Consensus Node 2](<C:/Users/Acer/Downloads/resolve consensus node 2 stlh transaksi.jpeg>)
*Gambar 12: Node 2 berhasil menyinkronkan data (Chain replaced).*

![Resolve Consensus Node 3](<C:/Users/Acer/Downloads/resolve consensus node 3 stlh transaksi.jpeg>)
*Gambar 13: Node 3 berhasil menyinkronkan data (Chain replaced).*

---
**Kesimpulan:**
Seluruh persyaratan spesifikasi sistem — mulai dari Digital Signature, Sistem Reward untuk Miner, Jaringan 3 Node, hingga Sinkronisasi menggunakan algoritma konsensus — telah diimplementasikan dan diuji coba dengan sukses.
