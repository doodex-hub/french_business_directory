# Negative — french_business_directory (18.0 → 19.0)

**Level:** Negative — hal yang HARUS ditolak/tidak boleh muncul. Direkomendasikan dijalankan minimal sekali sebelum rilis besar.
**Estimasi waktu:** ~5 menit.
**Sumber:** S-01, S-07, S-08 di `../10_BUSINESS_FLOW_MIGRATION.md`.

```
1. Buka kontak berjenis Individual (bukan Company) — tombol "Business Directory" TIDAK BOLEH tampil
2. Kirim email test dari alamat yang BUKAN kontak terdaftar dan BUKAN user internal, ke mailbox yang dipantau
3. Jalankan "Fetch Now" (dan/atau scheduled action) — cek TIDAK ADA res.partner baru dibuat dari email itu
4. Kirim email dari alamat user internal Odoo sendiri ke mailbox yang sama, fetch lagi — cek email itu di-skip (tidak diproses jadi pesan/lead)
5. Konfirmasi tidak ada dua dialog/wizard Odoo yang terbuka bersamaan dari satu aksi manapun di modul ini
```

## Hasil eksekusi

| Tanggal | Environment | Dijalankan oleh | Hasil | Catatan |
|---|---|---|---|---|
| 2026-08-26 | Docker `odoo:19.0`, test suite otomatis + review kode | AI (Claude Code CLI) | Pass | Langkah 1: evidence statis (view XML tidak berubah dari 18.0) + install sukses berulang, direkomendasikan klik manual sekali oleh dev sebelum go-live. Langkah 2-4: `test_message_new_returns_false_for_unknown_sender`, `test_skip_email_from_internal_user` — dikonfirmasi terpanggil lewat entry point `_fetch_mail()`/`fetch_mail()` yang benar pasca-fix MF-03. Langkah 5: N/A dikonfirmasi (lihat S-08) |
