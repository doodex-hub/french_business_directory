# Main Flow — french_business_directory

**Level:** Main Flow — flow bisnis inti sehari-hari.
**Estimasi waktu:** ~5 menit.
**Sumber:** S-03, S-04 di `../10_BUSINESS_FLOW_MIGRATION.md`.

```
1. Buka Contacts, buat/buka kontak berjenis Company
2. Klik tombol "Business Directory" di header form
3. Tunggu hasil pencarian muncul otomatis (berdasarkan nama kontak)
4. Klik "Select" pada salah satu baris hasil, konfirmasi dialog overwrite
5. Cek field kontak (nama, SIRET, alamat, kota) sudah ter-update sesuai hasil yang dipilih
6. Terpisah: kirim email test ke mailbox yang dipantau server IMAP dari alamat yang SUDAH ada di Contacts
7. Jalankan "Fetch Now" pada server itu
8. Cek Discuss/chatter — pesan dari email itu harus tercatat di thread kontak terkait
```

## Hasil eksekusi

| Tanggal | Environment | Dijalankan oleh | Hasil | Catatan |
|---|---|---|---|---|
| 2026-08-24 | Docker `odoo:18.0`, test suite otomatis | AI (Claude Code CLI) | Pass | Diverifikasi lewat `test_auto_fetch_on_wizard_open`, `test_select_result_overwrites_partner`, `test_process_email_from_known_contact` — bukan klik manual UI langsung, lihat catatan tooling di `10_BUSINESS_FLOW_MIGRATION.md` |
