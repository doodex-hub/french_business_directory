# Smoke Test — french_business_directory

**Level:** Smoke — kalau gagal: STOP, eskalasi ke dev.
**Estimasi waktu:** ~3 menit.

```
1. Login sebagai user internal, buka aplikasi Contacts, klik New.
2. Pastikan di sebelah kanan field nama ada tombol "🔍 Business Directory" (ikon kaca pembesar, TANPA tanda "-" di depannya).
3. Ketik nama perusahaan Perancis (mis. LA POSTE), klik "Business Directory".
4. Pastikan dialog "Search For Companies" terbuka dengan "... Results Found" dan daftar hasil.
   (Kalau muncul "Oops": tunggu 10 detik, tutup, klik tombol lagi — lihat catatan 429 di README.)
```

## Hasil eksekusi

| Tanggal | Environment | Dijalankan oleh | Hasil | Catatan |
|---|---|---|---|---|
| 2026-09-24 | docker-env 20.0 (port 8196) | AI (Playwright MCP) | Pass | Setelah fix RMV-01 |
