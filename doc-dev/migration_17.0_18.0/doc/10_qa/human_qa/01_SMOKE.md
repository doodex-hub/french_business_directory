# Smoke Test — french_business_directory

**Level:** Smoke — kalau ini gagal: STOP, jangan lanjut deploy, eskalasi ke dev.
**Estimasi waktu:** ~3 menit.
**Sumber:** S-02 di `../10_BUSINESS_FLOW_MIGRATION.md`.

```
1. Buka Settings > Technical > Automation > Scheduled Actions (atau Discuss > Fetchmail settings)
2. Buka server email masuk (fetchmail.server) yang dikonfigurasi
3. Klik tombol "Fetch Now"
4. Amati: tidak boleh muncul error/traceback di layar maupun di log server
```

## Hasil eksekusi

| Tanggal | Environment | Dijalankan oleh | Hasil | Catatan |
|---|---|---|---|---|
| 2026-08-24 | Docker `odoo:18.0`, `odoo shell` | AI (Claude Code CLI) | Pass | `fetch_mail(raise_exception=False)` return `True`, tidak ada exception (setara panggilan cron) |
