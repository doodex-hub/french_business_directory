# Human QA Checklists — french_business_directory (18.0 → 19.0)

**Sumber:** diturunkan dari skenario S-XX di `../10_BUSINESS_FLOW_MIGRATION.md`, dikelompokkan per `Level`. Kalau skenario/level di file itu berubah, regenerate 5 file di folder ini juga.

| File | Isi | Kapan dipakai |
|---|---|---|
| `01_SMOKE.md` | Cron/manual fetch email tidak crash via `_fetch_mail()` DAN `fetch_mail()` (S-02, MF-03) | Re-cek super cepat sebelum deploy/hotfix — **paling penting untuk rilis ini**, karena MF-03 (perubahan arsitektur fetchmail) adalah risiko tertinggi migrasi 18→19 |
| `02_MAIN_FLOW.md` | Wizard SIRET, field `company_registry` bukan lagi `siret` (S-03, DIFF-02), fetch email kontak dikenal (S-04) | QA rutin |
| `03_DETAIL.md` | Paginasi (S-05), auto-fill department (S-06), field Date tidak lagi crash (S-09) | QA menyeluruh sebelum rilis besar |
| `04_NEGATIVE.md` | Tombol company-only (S-01), no auto-create partner (S-07), multi-dialog N/A (S-08) | Direkomendasikan sebelum rilis besar apapun |

**Kombinasi disarankan:**
- Deploy/hotfix kecil → `01_SMOKE.md` saja
- Deploy rutin → `01_SMOKE.md` + `02_MAIN_FLOW.md`
- Rilis besar / sebelum UAT → keempat file

**Beda dari checklist 17.0→18.0:** `01_SMOKE.md` sekarang WAJIB juga cek field label "Siret" (bukan lagi field bernama literal `siret`) di form partner, dan verifikasi scheduled action fetchmail bukan cuma tombol manual — lihat detail di masing-masing file.
