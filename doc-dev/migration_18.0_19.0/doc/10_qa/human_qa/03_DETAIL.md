# Detail — french_business_directory (18.0 → 19.0)

**Level:** Detail — varian/edge-case, fitur sekunder.
**Estimasi waktu:** ~5 menit.
**Sumber:** S-05, S-06, S-09 di `../10_BUSINESS_FLOW_MIGRATION.md`.

```
1. Buka wizard SIRET untuk nama company yang punya banyak hasil (>1 halaman)
2. Klik "Next" berkali-kali sampai halaman terakhir, klik sekali lagi — harus kembali ke halaman 1 (bukan macet/error)
3. Klik "Prev" dari halaman 1 — harus lompat ke halaman terakhir
4. (Kalau addon OCA departemen Perancis terinstall) pilih hasil, cek field Department/State/Country ikut terisi
5. (Kalau addon itu TIDAK terinstall — kondisi default) pilih hasil, pastikan TIDAK ada error, field itu saja yang kosong
6. Cari perusahaan yang salah satu etablissement-nya TIDAK punya tanggal penutupan (date_fermeture) sama
   sekali di data API — pilih/lihat detail etablissement itu, pastikan TIDAK ada error (di 18.0 kasus ini
   bisa crash, di 19.0 seharusnya tidak lagi — lihat CAND-04)
```

## Hasil eksekusi

| Tanggal | Environment | Dijalankan oleh | Hasil | Catatan |
|---|---|---|---|---|
| 2026-08-26 | Docker `odoo:19.0`, test suite otomatis | AI (Claude Code CLI) | Pass (langkah 1-3, 5-6) / Belum dites (langkah 4) | Langkah 4 butuh addon OCA `l10n_fr_department` (atau setara) terinstall — belum di-connect, sama seperti project 17→18. Langkah 6: dikonfirmasi `test_matching_etablissement_missing_date_fermeture_key_no_longer_crashes`, reproducible di 4 run G1 berbeda |
