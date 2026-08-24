# Detail — french_business_directory

**Level:** Detail — varian/edge-case, fitur sekunder.
**Estimasi waktu:** ~5 menit.
**Sumber:** S-05, S-06 di `../10_BUSINESS_FLOW_MIGRATION.md`.

```
1. Buka wizard SIRET untuk nama company yang punya banyak hasil (>1 halaman)
2. Klik "Next" berkali-kali sampai halaman terakhir, klik sekali lagi — harus kembali ke halaman 1 (bukan macet/error)
3. Klik "Prev" dari halaman 1 — harus lompat ke halaman terakhir
4. (Kalau addon OCA departemen Perancis terinstall) pilih hasil, cek field Department/State/Country ikut terisi
5. (Kalau addon itu TIDAK terinstall — kondisi default) pilih hasil, pastikan TIDAK ada error, field itu saja yang kosong
```

## Hasil eksekusi

| Tanggal | Environment | Dijalankan oleh | Hasil | Catatan |
|---|---|---|---|---|
| 2026-08-24 | Docker `odoo:18.0`, test suite otomatis | AI (Claude Code CLI) | Pass (langkah 1-3, 5) / Belum dites (langkah 4) | Langkah 4 butuh addon OCA `l10n_fr_department` (atau setara) terinstall — lihat MF-01, `third-party-source` belum di-connect |
