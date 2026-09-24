# Negative — french_business_directory

**Level:** Negative — hal yang TIDAK BOLEH terjadi.
**Estimasi waktu:** ~5 menit. **Pakai database uji, JANGAN produksi** (langkah 1 bisa menimpa kontak lain).

```
1. [RMV-02, bug bawaan 19.0 — status: menunggu keputusan dev]
   a. Dari kontak A, buka Business Directory, klik "Next →" sekali.
   b. Buka satu baris → Select → Ok.
   c. Cek: yang ter-update HARUS kontak A. Saat ini (19.0 dan 20.0) yang ter-update adalah kontak dengan ID sama dengan ID wizard (bisa "My Company" atau kontak acak) → FAIL diketahui.
2. Matikan mode developer. Buka form Incoming Mail Server. Pastikan "Mark Emails as Read" TIDAK tampil.
```

## Hasil eksekusi

| Tanggal | Environment | Dijalankan oleh | Hasil | Catatan |
|---|---|---|---|---|
| 2026-09-24 | docker-env 20.0 + 19.0 (compare) | AI (Playwright MCP) | Langkah 1 FAIL (RMV-02, identik 19.0), langkah 2 Pass | Eskalasi ke dev |
