# Main Flow — french_business_directory

**Level:** Main Flow — blocker go-live kalau gagal.
**Estimasi waktu:** ~8 menit.

```
1. Buka kembali kontak perusahaan yang SUDAH disimpan dan TIDAK punya Tax ID (VAT).
2. Pastikan tombol "Business Directory" masih tampil, klik → wizard terbuka.
3. Klik "Next →": nomor halaman naik (1 → 2), daftar berganti.
4. Klik "← Prev": kembali ke halaman 1. Klik "← Prev" lagi di halaman 1: lompat ke halaman terakhir. Klik "Next →" di halaman terakhir: kembali ke halaman 1.
5. TUTUP wizard (Cancel), klik "Business Directory" lagi (wizard BARU, JANGAN paginasi).
6. Klik salah satu baris hasil → daftar etablissement terbuka → klik "Select" → konfirmasi "Are you sure want to overwrite the Data?" → Ok.
7. Di form kontak: nama, alamat, kode pos, kota terisi dari hasil, dan field SIRET + SIREN tampil terisi.
```

## Hasil eksekusi

| Tanggal | Environment | Dijalankan oleh | Hasil | Catatan |
|---|---|---|---|---|
| 2026-09-24 | docker-env 20.0 | AI (Playwright MCP) | Pass | Langkah 5 sengaja tanpa paginasi — lihat 04_NEGATIVE (RMV-02) |
