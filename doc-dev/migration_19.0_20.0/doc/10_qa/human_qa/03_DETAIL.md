# Detail — french_business_directory

**Level:** Detail.
**Estimasi waktu:** ~5 menit.

```
1. Di wizard, buka satu baris hasil. Pastikan kolom Siret, Core Business, Address, Date Creation, Status tampil; status aktif = badge hijau "en activité".
2. Pastikan tombol paginasi wizard menampilkan panah "← Prev" dan "Next →" (bukan "--" atau tanpa panah).
3. Aktifkan mode developer. Settings → Technical → Incoming Mail Servers → New → tab Advanced.
4. Pastikan urutan: "Keep Attachments", "Mark Emails as Read" (tidak dicentang), "Keep Original".
```

Diketahui (bawaan 19.0, bukan kegagalan): alamat bisa tampil "None ..." kalau nomor jalan kosong; judul wizard berubah jadi "Odoo" setelah paginasi (RMV-04).

## Hasil eksekusi

| Tanggal | Environment | Dijalankan oleh | Hasil | Catatan |
|---|---|---|---|---|
| 2026-09-24 | docker-env 20.0 | AI (Playwright MCP) | Pass | |
