# Smoke Test — french_business_directory (18.0 → 19.0)

**Level:** Smoke — kalau ini gagal: STOP, jangan lanjut deploy, eskalasi ke dev.
**Estimasi waktu:** ~5 menit (lebih lama dari checklist 17→18 karena MF-03).
**Sumber:** S-02 di `../10_BUSINESS_FLOW_MIGRATION.md`.

```
1. Buka Settings > Technical > Automation > Scheduled Actions
2. Cari action "Mail: Fetchmail Service" (ir_cron_mail_gateway_action) — cek "Active" dan "Next Execution Date"
3. Klik "Run Manually" pada scheduled action itu (BUKAN cuma tombol "Fetch Now" di form server — action ini yang
   MEWAKILI jalur cron sungguhan yang dipakai produksi, ini yang paling penting diverifikasi untuk migrasi ini)
4. Amati: tidak boleh muncul error/traceback di layar maupun di log server (docker logs / /var/log/odoo)
5. Buka Settings > Technical > Email > Incoming Mail Servers, buka server yang dikonfigurasi
6. Klik tombol "Fetch Now" di form server (jalur manual, berbeda entry point dari langkah 3)
7. Amati: tidak boleh muncul error/traceback juga di jalur ini
```

**Kenapa DUA langkah (3 dan 6), bukan cuma satu seperti checklist 17→18:** migrasi 18→19 memindahkan override modul dari `fetch_mail()` (dipanggil tombol manual) ke `_fetch_mail()` (dipanggil scheduled action/cron) — lihat `FINDINGS.md` MF-03. Kedua jalur HARUS dites terpisah untuk memastikan tidak ada regresi di salah satunya.

## Hasil eksekusi

| Tanggal | Environment | Dijalankan oleh | Hasil | Catatan |
|---|---|---|---|---|
| 2026-08-26 | Docker `odoo:19.0`, test otomatis (bukan klik UI — lihat catatan tooling di `10_BUSINESS_FLOW_MIGRATION.md`) | AI (Claude Code CLI) | Pass | `_fetch_mail()` (jalur 3, cron) return `None`, tidak error. `.fetch_mail()` (jalur 6, manual, via 5 test IMAP lain) juga terkonfirmasi memanggil override kita dengan benar. **Verifikasi via klik UI sungguhan (langkah di atas) BELUM dilakukan** — direkomendasikan dev jalankan manual sekali sebelum go-live produksi, terutama langkah 3 (scheduled action, jalur cron sesungguhnya). |
