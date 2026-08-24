# Human QA Checklists — french_business_directory

**Sumber:** diturunkan dari skenario S-XX di `../10_BUSINESS_FLOW_MIGRATION.md`, dikelompokkan per `Level`. Kalau skenario/level di file itu berubah, regenerate 4 file di folder ini juga.

| File | Isi | Kapan dipakai |
|---|---|---|
| `01_SMOKE.md` | Cron fetch email tidak crash (S-02) | Re-cek super cepat sebelum deploy/hotfix |
| `02_MAIN_FLOW.md` | Wizard SIRET (S-03), fetch email kontak dikenal (S-04) | QA rutin |
| `03_DETAIL.md` | Paginasi (S-05), auto-fill department (S-06) | QA menyeluruh sebelum rilis besar |
| `04_NEGATIVE.md` | Tombol company-only (S-01), no auto-create partner (S-07), multi-dialog N/A (S-08) | Direkomendasikan sebelum rilis besar apapun |

**Kombinasi disarankan:**
- Deploy/hotfix kecil → `01_SMOKE.md` saja
- Deploy rutin → `01_SMOKE.md` + `02_MAIN_FLOW.md`
- Rilis besar / sebelum UAT → keempat file
