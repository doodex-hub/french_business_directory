# Main Flow — french_business_directory (18.0 → 19.0)

**Level:** Main Flow — flow bisnis inti sehari-hari.
**Estimasi waktu:** ~5 menit.
**Sumber:** S-03, S-04 di `../10_BUSINESS_FLOW_MIGRATION.md`.

```
1. Buka Contacts, buat/buka kontak berjenis Company
2. Klik tombol "Business Directory" di header form
3. Tunggu hasil pencarian muncul otomatis (berdasarkan nama kontak)
4. Klik "Select" pada salah satu baris hasil, konfirmasi dialog overwrite
5. Cek field kontak (nama, alamat, kota) sudah ter-update sesuai hasil yang dipilih. Field SIRET sekarang
   tampil dengan LABEL "Siret" tapi TEKNISNYA adalah field core `company_registry` (bukan lagi field
   dedicated `siret` seperti di 18.0) — cek nilainya benar, nama field internal tidak relevan bagi user
6. Terpisah: kirim email test ke mailbox yang dipantau server IMAP dari alamat yang SUDAH ada di Contacts
7. Jalankan "Fetch Now" pada server itu (atau scheduled action — lihat `01_SMOKE.md`)
8. Cek Discuss/chatter — pesan dari email itu harus tercatat di thread kontak terkait
```

## Hasil eksekusi

| Tanggal | Environment | Dijalankan oleh | Hasil | Catatan |
|---|---|---|---|---|
| 2026-08-26 | Docker `odoo:19.0`, test suite otomatis (24 test, terhadap DB+ORM sungguhan) | AI (Claude Code CLI) | Pass | Diverifikasi lewat `test_auto_fetch_on_wizard_open`, `test_select_result_overwrites_partner` (assertion langsung `company_registry`), `test_process_email_from_known_contact` — bukan klik manual UI langsung (Owl webclient tidak mount di browser tool sesi ini, lihat catatan tooling di `10_BUSINESS_FLOW_MIGRATION.md`) |
