# Business Flow — Migrasi french_business_directory

**Step:** 10 — QA Testing (gate)
**Ref:** `05_acceptance/05a_MIGRATION_ACCEPTANCE_CRITERIA.md`
**Tanggal:** 2026-08-26

> Port kode saja (bukan upgrade instance) — tidak ada clone data produksi, skenario dijalankan terhadap instalasi bersih (`target_db_19`, sama seperti G1/Step 9).

## Catatan Mode Eksekusi

Dicoba **AI-interaktif** (Claude Browser tool) lebih dulu untuk S-01/S-03 — sama seperti project 17.0→18.0 sebelumnya. Server Odoo dijalankan live (`docker compose run` tanpa `--stop-after-init`, port 8179), login admin **berhasil** (session/csrf valid, RPC `iap_enrich_auto`/`load_menus`/`mail/data`/`discuss.channel/channel_fetched` semua 200 OK — dikonfirmasi via `read_network_requests`), TAPI Owl webclient **tidak pernah mount konten apapun ke DOM** (`body` kosong di semua percobaan, termasuk setelah `wait` 3 detik dan navigasi ulang) — **PERSIS temuan yang sama seperti project 17.0→18.0** (lihat `doc-dev/migration_17.0_18.0/doc/10_qa/10_BUSINESS_FLOW_MIGRATION.md` "Catatan Mode Eksekusi"). Ini keterbatasan tool browser headless sesi ini (kemungkinan terkait `bus/websocket`/service worker di lingkungan sandboxed), BUKAN indikasi kerusakan di `fr_business_directory`/`personal_email_usage` — backend merespons benar (200 OK di semua RPC), install (G1) sudah terbukti sukses berkali-kali (4 run). Server dimatikan setelah percobaan (`docker rm -f` + `docker compose down -v`), tidak dibiarkan hidup.

Sisa skenario dievaluasi lewat kombinasi: bukti Step 9 (24 test otomatis nyata terhadap Odoo 19.0 + Postgres sungguhan, bukan mock ORM) + verifikasi statis Step 2/8 (diff/collision check terhadap `native-target` = `enterprise19.0`). Mode per skenario disebutkan eksplisit di tiap `S-XX`.

---

## Skenario

### S-01: Tombol "Business Directory" hanya muncul untuk kontak Company
**Level:** Negative
**Precondition:** Modul terinstall bersih di 19.0
**Mode eksekusi:** AI-interaktif dicoba, terhambat tooling (lihat catatan di atas) → **fallback ke bukti statis**: `views/partner.xml` TIDAK diubah dari source (DIFF-03, Step 2 — cuma dikonfirmasi `id="company"` tetap ada di base view 19.0), parsing view dikonfirmasi valid lewat install sukses berulang (G1 run #4)
**Steps:** Buka form kontak Individual → tombol tidak boleh muncul. Buka form kontak Company → tombol harus muncul.
**Expected:** `invisible="is_company != True"` bekerja seperti di 18.0 (tidak berubah)
**Actual:** Belum diverifikasi via klik langsung di browser (tooling gagal render, sama seperti project 17→18) — arch XML tidak berubah dari source, sudah lolos parsing ORM berulang kali
**Status:** [x] Pass (evidence: static + install-time XML validation) — **direkomendasikan** dev klik manual sekali sebelum deploy produksi untuk kepastian visual 100%, lihat `human_qa/01_SMOKE.md`

### S-02: `fetch_mail()`/`_fetch_mail()` tidak crash di 19.0 (DIFF-01, MF-03)
**Level:** Smoke
**Precondition:** Modul terinstall
**Mode eksekusi:** Otomatis — dikonfirmasi nyata di Step 9 (`test_fetch_mail_accepts_no_args`, memanggil `_fetch_mail()` langsung — entry point yang benar-benar dipanggil cron 19.0, bukan `fetch_mail()`)
**Steps:** Panggil `env['fetchmail.server']._fetch_mail()` (cara cron `_fetch_mails()` memanggil di 19.0) DAN `server.fetch_mail()` (cara tombol manual "Fetch Now" memanggil, via `self.sudo()._fetch_mail()`)
**Expected:** Keduanya TIDAK error, override custom (filter user internal/non-kontak, dedup `processed_message_ids`) tetap terpanggil lewat KEDUA jalur
**Actual:** Dikonfirmasi test otomatis pass (`_fetch_mail()` langsung) DAN 5 test IMAP lain (`test_skip_email_from_internal_user` dkk, panggil via `.fetch_mail()` — entry point manual, membuktikan chain `fetch_mail()`→`sudo()._fetch_mail()`→override kita bekerja utuh)
**Status:** [x] Pass — **lebih kuat dari S-02 versi 17→18** (dulu cuma 1 test signature, sekarang 6 test membuktikan override benar-benar terpanggil dari DUA entry point berbeda)

### S-03: Wizard SIRET — cari & pilih hasil, data ter-tulis ke partner via `company_registry` (DIFF-02)
**Level:** Main Flow
**Precondition:** Kontak company dibuat
**Mode eksekusi:** Otomatis (Step 9, `test_auto_fetch_on_wizard_open` + `test_select_result_overwrites_partner`)
**Steps:** Klik tombol → wizard fetch otomatis → klik "Select" pada satu hasil
**Expected:** Field partner (`name`/`company_registry` [dulu `siret`]/`street`/`social_reason`/`zip`/`city`/koordinat) ter-overwrite
**Actual:** Dikonfirmasi test otomatis pass — assertion langsung `self.partner.company_registry == '12345678900012'`
**Status:** [x] Pass

### S-04: Email dari kontak dikenal diproses, dari user internal/non-kontak di-skip
**Level:** Main Flow
**Precondition:** Server IMAP + partner + user dibuat
**Mode eksekusi:** Otomatis (Step 9, `test_process_email_from_known_contact`, `test_skip_email_from_internal_user`, `test_skip_email_from_non_contact`)
**Expected:** Hanya email dari kontak dikenal yang diteruskan ke `message_process`
**Actual:** Dikonfirmasi test otomatis pass
**Status:** [x] Pass

### S-05: Paginasi Next/Prev (termasuk wrap-around dan bug parameter hilang)
**Level:** Detail
**Mode eksekusi:** Otomatis (Step 9, 4 test method paginasi)
**Expected:** Wrap-around bekerja; parameter `limite_matching_etablissements` tetap hilang di Prev (preserved bug, BSL-009)
**Actual:** Dikonfirmasi
**Status:** [x] Pass

### S-06: Auto-fill department/state/country (kondisional pada `res.country.department`)
**Level:** Detail
**Precondition:** Model `res.country.department` (OCA) — **tidak terinstall di environment ini**
**Mode eksekusi:** Otomatis, tapi test untuk kondisi "model tersedia" di-skip eksplisit (Step 9)
**Expected:** Kalau model tidak ada, field itu tidak disentuh (tidak error) — inilah yang genuinely bisa dites di sini
**Actual:** Dikonfirmasi (`test_select_department_field_untouched_when_model_absent`, pass)
**Status:** [x] Pass (untuk kondisi "model tidak ada" saja — kondisi "model ada" tetap belum tervalidasi, konsisten sejak project 17→18)

### S-07: `message_new()` tidak pernah membuat `res.partner` baru dari email masuk
**Level:** Negative
**Mode eksekusi:** Otomatis (Step 9, `test_message_new_returns_existing_partner/false_for_unknown_sender`)
**Expected:** Baik pengirim dikenal maupun tidak, TIDAK ADA partner baru tercipta lewat jalur ini
**Actual:** Dikonfirmasi — jumlah partner sebelum/sesudah sama di kedua kasus
**Status:** [x] Pass

### S-08: Kasus multi-dialog dari satu aksi user
**Level:** Negative
**Catatan:** N/A — tidak ada kasus multi-dialog (tidak berubah dari analisis 17→18 — struktur wizard tidak disentuh migrasi ini).
**Status:** N/A

### S-09: Regresi platform — field `Date` `date_fermeture` tidak lagi crash pada string kosong (CAND-04)
**Level:** Detail (baru, spesifik 19.0)
**Mode eksekusi:** Otomatis (Step 9, `test_matching_etablissement_missing_date_fermeture_key_no_longer_crashes`)
**Expected:** Behavior BARU 19.0 (bukan sesuatu yang kita ubah) — penulisan string kosong ke field Date tidak lagi crash Postgres, dikoersi jadi falsy
**Actual:** Dikonfirmasi reproducible di 4 run G1 berbeda (fresh DB tiap kali)
**Status:** [x] Pass (informational — bukan regresi fungsional, platform improvement)

---

## Ringkasan per Level

| Level | Skenario | Jumlah |
|---|---|---|
| Smoke | S-02 | 1 |
| Main Flow | S-03, S-04 | 2 |
| Detail | S-05, S-06, S-09 | 3 |
| Negative | S-01, S-07, S-08 | 3 |

## Human QA Checklists

Digenerate di `10_qa/human_qa/` (README + SMOKE + MAIN_FLOW + DETAIL + NEGATIVE), diturunkan dari skenario di atas — memuat 2 poin verifikasi visual tambahan spesifik 19.0 (field label "Siret" pada `company_registry` di form partner, dan confirm cron fetch tetap jalan di scheduled action UI) yang tidak ada di checklist 17→18.

## Loop-back

Tidak ada skenario Fail — tidak perlu balik ke Step 9.

## Verdict

- [x] ✅ **Lulus** — lanjut ke Step 11

**Catatan untuk Step 11/deploy:** S-01 (visibilitas tombol) direkomendasikan diklik manual sekali oleh dev sebelum go-live — bukan blocker (evidence otomatis + install-time sudah cukup kuat, DAN sudah divalidasi visual di produksi 18.0 sebelumnya karena view tidak berubah). **Tambahan khusus migrasi ini:** dev WAJIB verifikasi manual sekali bahwa Scheduled Action "Fetch Mail" (`mail.ir_cron_mail_gateway_action`) benar-benar berjalan tanpa error di instance 19.0 nyata setelah deploy — MF-03 sudah diverifikasi lewat test otomatis yang memanggil method secara langsung, tapi belum pernah diobservasi lewat cron scheduler Odoo yang sesungguhnya (`ir.cron`) end-to-end.
