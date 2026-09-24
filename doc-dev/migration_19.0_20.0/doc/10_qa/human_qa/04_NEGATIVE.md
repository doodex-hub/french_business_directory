# Negative — french_business_directory

**Level:** Negative — hal yang TIDAK BOLEH terjadi.
**Estimasi waktu:** ~5 menit. **Pakai database uji, JANGAN produksi** (langkah 1 bisa menimpa kontak lain).

```
1. [RMV-02 — bug bawaan 19.0, DIPERBAIKI 2026-09-24]
   a. Dari kontak A, buka Business Directory, klik "Next →" sekali.
   b. Buka satu baris → Select → Ok.
   c. Cek: yang ter-update HARUS kontak A; kontak lain (mis. "My Company") TIDAK boleh berubah. (Sebelum perbaikan, yang tertimpa adalah kontak ber-ID sama dengan ID wizard.) Data demo siap-pakai: `../rmv02_demo_setup.py`.
2. Matikan mode developer. Buka form Incoming Mail Server. Pastikan "Mark Emails as Read" TIDAK tampil.
```

## Hasil eksekusi

| Tanggal | Environment | Dijalankan oleh | Hasil | Catatan |
|---|---|---|---|---|
| 2026-09-24 | docker-env 20.0 + 19.0 (compare) | AI (Playwright MCP) | Langkah 1 FAIL (RMV-02, identik 19.0), langkah 2 Pass | Eskalasi ke dev |
| 2026-09-24 10:11 | docker-env 20.0 (setelah paket perbaikan) | AI (Playwright MCP) | Langkah 1 Pass (kontak asal ter-update, korban utuh), langkah 2 Pass | RMV-02 fixed |
