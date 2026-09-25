# Findings — french_business_directory (migrasi 19.0 → 20.0)

**Modul:** french_business_directory (`fr_business_directory`, `personal_email_usage`)
**Migrasi:** 19.0 → 20.0
**Terakhir update:** 2026-09-24

> Skema & aturan: `migration-tool/templates/FINDINGS.md`. ID `MF-NNN` di file ini independen dari
> `MF-NNN` project 18→19 (`doc-dev/migration_18.0_19.0/doc/FINDINGS.md`) — kalau merujuk yang lama,
> ditulis eksplisit "MF-03 (18→19)".
>
> Semua keputusan di bawah yang bertanda "Keputusan AI" diambil sesuai `USAGE_GUIDE.md` "Eksekusi
> Berkelanjutan di CLI" (ada rekomendasi jelas + risiko rendah → AI pilih, dokumentasikan, lanjut).
> Dev tetap bisa mengoreksi kapan saja; entry yang genuinely butuh mata manusia ditandai
> `[PERLU-KEPUTUSAN]` dan diteruskan ke Step 10/11.

---

## Ringkasan

| ID | Judul | Ditemukan di Step | Tag | Prioritas | Status |
|---|---|---|---|---|---|
| MF-01 | `ir.model.access` (model + CSV) dihapus di 20.0, diganti `ir.access` / `ir.access.csv` | Step 1 (pre-scan) / 2 | `[GAP-MIGRASI]` | Tinggi (install-blocking `fr_business_directory`) | Keputusan AI: konversi format native — diterapkan Step 6 |
| MF-02 | `res.partner.company_registry` dihapus dari base 20.0 → SIRET pindah ke JSON `additional_identifiers['FR_SIRET']` (tervalidasi) | Step 1 (pre-scan) / 2 | `[GAP-MIGRASI]` | Kritis (fitur inti "Select") | Keputusan AI: tulis `FR_SIRET` via `additional_identifiers`, validasi native dipertahankan — deviasi edge-case dicatat |
| MF-03 | `base.view_partner_form` 20.0 dirombak: `<field id="company" name="name">` hilang, `is_company` jadi computed dari VAT | Step 1 (pre-scan) / 2 / 6 (G1 #6) | `[GAP-MIGRASI]` + `[PERLU-KEPUTUSAN]` (visibilitas tombol) | Tinggi (install-blocking + UX tombol) | 🟡 **OPEN — WORKAROUND diterapkan** (disetujui dev 2026-09-24): `invisible="parent_id"` → company tanpa VAT tetap dapat tombol (43/43 PASS). Belum dianggap selesai: individu tanpa parent kini juga melihat tombol; konfirmasi visual Step 10 + sign-off Step 11 |
| MF-04 | package `odoo.osv` dihapus total di 20.0 → `from odoo.osv import expression` (tak terpakai) ImportError | Step 1 (pre-scan) / 2 | `[GAP-MIGRASI]` | Tinggi (install-blocking `personal_email_usage`) | Keputusan AI: hapus baris import itu saja |
| MF-05 | `self._cr` / `self._context` masih deprecated (bukan dihapus) di 20.0 | Step 2 | `[DIWARISI-SOURCE]` (informasional) | Rendah | ➖ Dibiarkan — keputusan dev 2026-09-25 (cek ulang di 20→21) |
| MF-06 | Test existing terikat ke `company_registry` + data SIRET dummy yang tidak lolos validasi Luhn 20.0 | Step 2 / 6 (G1 #5) | `[GAP-MIGRASI]` (test) | Sedang | ✅ RESOLVED (G1 #7, 42/42 PASS) |
| RMV-01 | Ikon Font Awesome (`icon="fa-search"`, `icon="fa-arrow-left"`, `<i class="fa fa-arrow-right">`) rusak di 20.0 — FA dihapus, semua ikon jadi ligatur `oi` | Step 10 (Cross-Version Compare) | `REGRESI` | Sedang (visual) | ✅ FIXED + test `test_no_font_awesome_icons_rmv01`, visual identik 19.0 |
| RMV-02 | Select setelah paginasi menimpa partner dengan id = id wizard (bukan kontak asal) — korupsi data | Step 10 (Cross-Version Compare) | `GAP-LAMA` (identik 19.0) | **Kritis** (data) | ✅ FIXED (disetujui dev 2026-09-24): action paginasi membawa context asal; live: kontak asal ter-update, korban utuh |
| RMV-03 | API gouv.fr sering membalas 429 → memicu NameError `_logger` (BSL-008) → dialog "Oops" | Step 10 | `GAP-LAMA` | Sedang (UX) | ✅ FIXED (disetujui dev 2026-09-24): `_logger` + retry 429 (Retry-After, maks 2x, ≤5 dtk) + pesan UserError bahasa Inggris; live: 429 → retry → sukses |
| RMV-05 | Halaman hasil crash (`TypeError`) kalau API mengembalikan `libelle_voie: null` (mis. "CARREFOUR" hal. 2) | Step 10 | `GAP-LAMA` | Sedang | Dicatat, tidak difix |
| RMV-06 | Next pertama memanggil API 2x (create wizard memicu `default_get` + panggilan API lagi) | Step 10 | `GAP-LAMA` | Sedang (memperbesar 429) | ✅ FIXED (disetujui dev 2026-09-24): `default_get` panggil API hanya saat dialog dibuka + `force_save` counter; live: `web_save` tanpa panggilan API |
| RMV-04 | "None" di alamat bila `numero_voie` kosong; judul wizard "Odoo" setelah paginasi | Step 10 | `GAP-LAMA` (kosmetik) | Rendah | Dicatat, tidak difix |
| MF-07 | Aset store branch rilis `19.0` (banner.gif, icon, assets, index.html, fix manifest `images`) tidak ada di `migration/19.0` | Step 1 | `[PERLU-KEPUTUSAN]` (di luar port kode) | Rendah (non-fungsional) | Keputusan DEV 2026-09-24: TIDAK di-port di migrasi ini |

---

## Detail

### MF-01 — `ir.model.access` dihapus di 20.0, diganti `ir.access`
**Ditemukan di:** Step 1 pre-scan, dikonfirmasi Step 2 (2026-09-24)
**Tag:** `[GAP-MIGRASI]`
**Ref:** `DIFF-01`, `01b_BASELINE_SPEC.md` Bagian A §2 (ACL), BSL-022; knowledge `19-to-20.md` baris `ir.access.csv`
**Lokasi:** `fr_business_directory/security/ir.model.access.csv`, `fr_business_directory/__manifest__.py:22`; `personal_email_usage/security/ir.model.access.csv` (dead file, tidak dimuat)
**Deskripsi:** Di 20.0 tidak ada lagi model `ir.model.access` (grep `odoo20/odoo` — nol definisi; `odoo/orm/models.py:3655` memakai `self.env['ir.access']`). `convert_csv_import()` (`odoo20/odoo/tools/convert.py:740`) menurunkan nama model dari nama file (`ir.model.access.csv` → `env['ir.model.access']`) → KeyError saat install. Native menyediakan konverter resmi `odoo20/odoo/upgrade_code/19.4-00-ir-access.py`: header baru `id,name,model_id,group_id/id,operation,domain`, `model_id` berisi NAMA model (bukan xmlid `model_*`), `operation` = subset huruf `crud`, file `security/ir.access.csv`, manifest `data` diganti.
**Dampak:** tanpa konversi, `fr_business_directory` gagal install di 20.0. `personal_email_usage` TIDAK terdampak (baris manifest-nya dikomentari sejak 17.0 — BSL-022).
**Rekomendasi / Keputusan AI:** tulis ulang persis seperti output konverter native: 3 baris, `base.group_user`, `operation=crud`, domain kosong (tidak ada `ir.rule`, jadi tidak ada semantik OR-domain yang berubah). Hapus `ir.model.access.csv` lama dari `fr_business_directory`, ganti entri manifest. Dead file `personal_email_usage/security/ir.model.access.csv` dibiarkan apa adanya (tidak dimuat, konsisten BSL-022 — konverter native juga mengabaikannya karena tidak ada di manifest `data`).

---

### MF-02 — `res.partner.company_registry` dihapus → SIRET di `additional_identifiers['FR_SIRET']`
**Ditemukan di:** Step 1 pre-scan, dikonfirmasi Step 2 (2026-09-24)
**Tag:** `[GAP-MIGRASI]`
**Ref:** `DIFF-02`, BSL-004, BSL-006; MF-02 (18→19) — perubahan KEDUA berturut-turut pada field target SIRET (18: `l10n_fr.siret` → 19: `base.company_registry` → 20: `base.additional_identifiers['FR_SIRET']`)
**Lokasi:** `fr_business_directory/models/siret_wizard.py:260,275` (`siret.wizard.result.select_siret`), `:354,369` (`matching.etablissement.select_siret`)
**Deskripsi:** 20.0 menghapus field `company_registry` (dan `company_registry_label/placeholder`, `same_company_registry_partner_id`) dari `base` — nol match `company_registry` di `odoo20/odoo/addons/base`. Penggantinya: `res.partner.additional_identifiers = fields.Json(copy=False)` (`odoo20/odoo/addons/base/models/res_partner.py:330`) berisi dict `{KEY: value}`; key Perancis `FR_SIRET` (label "SIRET", `category='EN'`, `validation_function=fr_siret.validate` (stdnum, Luhn), `odoo20/odoo/tools/partner_identifiers.py:645`) terdefinisi di BASE (tidak butuh `l10n_fr_account`). `write()` memanggil `_clean_additional_identifiers(vals)` (`res_partner.py:963,1826-1848`): drop key tak dikenal, **raise `ValidationError` untuk nilai tak valid**, normalisasi, dan **deduksi otomatis `FR_SIREN`** (9 digit pertama) dari `FR_SIRET`. `l10n_fr` 20.0 juga menghapus `views/res_partner_views.xml` (relabel `company_registry` → "Siren/Siret"); tampilan SIRET di form partner kini lewat widget identifier native.
**Dampak:** kode 19.0 `partner.write({'company_registry': ...})` → error field tak dikenal → tombol "Select" (fitur inti) gagal total.
**Opsi yang dipertimbangkan:**
1. **(DIPILIH)** Tulis `additional_identifiers` di dalam `write()` yang SAMA: ambil JSON existing, buang key `FR_SIRET`+`FR_SIREN` lama, set `FR_SIRET = self.siret` kalau truthy (kalau falsy — setara 19.0 menulis `''` — key dibiarkan terhapus). Validasi native TETAP berlaku. Risiko: rendah — SIRET dari API gouv.fr adalah SIRET resmi (lolos Luhn); `FR_SIREN` ikut terisi (side effect native baru, konsisten dengan SIRET); identifier lain partner (mis. VAT-derived) TIDAK disentuh (setara 19.0 yang hanya menulis satu kolom).
2. Sama seperti 1 tapi bypass validasi (`with_context(no_vat_validation=True)`) supaya nilai APAPUN diterima seperti Char 19.0. Ditolak: nilai tak valid tersimpan di JSON tervalidasi akan membuat edit identifier berikutnya di UI gagal `_check_additional_identifiers` — deviasi yang lebih buruk & tersembunyi.
3. `_set_additional_identifier('FR_SIRET', v)` sebagai write kedua. Ditolak: dua write terpisah (beda dari 19.0 satu write), meninggalkan `FR_SIREN` basi saat SIRET dikosongkan.
**Deviasi yang tidak terhindarkan (dicatat, bukan disembunyikan):** (a) SIRET tidak valid (bukan Luhn) → `ValidationError` di 20.0, di 19.0 tersimpan apa adanya; (b) `FR_SIREN` terisi otomatis. Keduanya perilaku platform 20.0 atas penyimpanan identifier, bukan perubahan business rule "Select overwrite SIRET".
**Keputusan pemilik modul:** *(Keputusan AI: opsi 1 — bisa dikoreksi dev)*

---

### MF-03 — Form partner 20.0 dirombak: `id="company"` hilang, `is_company` computed dari VAT
**Ditemukan di:** Step 1 pre-scan, dikonfirmasi Step 2 (2026-09-24)
**Tag:** `[GAP-MIGRASI]` (struktur xpath — wajib) + `[PERLU-KEPUTUSAN]` (efek semantik visibilitas tombol)
**Ref:** `DIFF-03`, BSL-001, BSL-025
**Lokasi:** `fr_business_directory/views/partner.xml:10`
**Deskripsi:**
1. `base.view_partner_form` 20.0 (`odoo20/odoo/addons/base/views/res_partner_views.xml:99-135`) hanya punya SATU field nama di header: `<h1><field options="{'line_breaks': False}" widget="text" class="text-break d-block" name="name" default_focus="1" placeholder="Name (company or person)" required="type == 'contact'"/></h1>` — tidak ada lagi `id="company"`/`id="individual"` dan radio `company_type`. xpath `<field id="company" name="name" position="replace">` → install error ("Element ... cannot be located in parent view").
2. `is_company` 20.0 = `fields.Boolean(compute='_compute_is_company', store=True)` (`res_partner.py:366`), `@api.depends('has_vat', 'commercial_partner_id')` → `commercial_partner_id == partner and has_vat` (`:944-955`). Tidak lagi di-set user lewat radio. Action Contacts memberi `context={'default_is_company': True}` (`odoo20/addons/contacts/views/contact_views.xml:59`) — nilai default yang dilindungi saat create, lalu dihitung ulang begitu `vat`/`parent_id` berubah.
3. Kalau replace dilakukan apa adanya (div pengganti ber-`invisible="is_company != True"`), partner non-company di 20.0 akan kehilangan field nama sama sekali (di 19.0 masih ada field `individual` terpisah).
**Keputusan AI (bagian struktur, wajib):** target xpath `//h1/field[@name='name']` (satu-satunya `h1` di view itu), `position="replace"` dengan `div` flex nowrap (style identik 19.0) yang berisi `$0` (field nama native 20.0 apa adanya, SELALU tampil) + tombol "Business Directory" (atribut identik 19.0, `invisible="is_company != True"`). Div TIDAK diberi `invisible` — supaya individu tetap punya field nama (setara 19.0 di mana individu memakai field native).
**Bagian yang butuh mata manusia (`[PERLU-KEPUTUSAN]`):** ekspresi visibilitas tombol dipertahankan identik (`is_company != True`), tapi ARTI `is_company` berubah di platform 20.0 (company = entitas komersial sendiri + punya VAT valid, atau default `True` dari action Contacts sampai VAT/parent berubah). Kemungkinan efek: company tanpa VAT yang dibuat di luar action Contacts, atau yang VAT-nya dikosongkan, tidak lagi melihat tombol. Diverifikasi empiris di Step 9 (test `Form`), dan visual di Step 10. Kalau dev ingin tombol tetap muncul untuk company tanpa VAT, opsi alternatif: `invisible="parent_id"` (tampil untuk semua entitas komersial) — itu PERUBAHAN business rule, butuh persetujuan eksplisit dev.

**Bukti empiris (G1 #6/#7, 2026-09-24, `test_new_partner_form_contacts_context_is_company`):** partner baru lewat context Contacts (`default_is_company=True`), tanpa VAT → `is_company` = **True** di form belum disimpan (tombol tampil) → **False setelah save** (recompute `has_vat=False`) → True setelah VAT diisi → False lagi saat VAT dihapus. Artinya di 20.0: company TANPA VAT kehilangan tombol "Business Directory" begitu disimpan (di 19.0 tombol tetap ada selama user memilih tipe Company). Klik tombol pada record baru tetap jalan (tombol tampil sebelum save; klik men-save lalu membuka wizard).

**ESCALATION — Migrasi 20.0** (tidak memblokir Step 1-9; wajib diputuskan sebelum Step 11):
- Step/Fase: Step 6 G2 / Step 9
- Modul: french_business_directory (`fr_business_directory`)
- Isu: tombol hanya muncul untuk partner yang oleh 20.0 dianggap company (punya VAT & tanpa parent) — company tanpa VAT tidak bisa memakai Business Directory setelah record disimpan.
- Opsi: 1) Pertahankan `invisible="is_company != True"` (implementasi sekarang, port literal) — Risiko: sedang (fitur tidak tersedia untuk company tanpa VAT tersimpan); 2) `invisible="parent_id"` (tampil untuk semua entitas komersial, individu-tanpa-parent juga ikut dapat tombol) — Risiko: rendah teknis, tapi mengubah business rule; 3) `invisible="parent_id or not name"` atau varian lain sesuai kebutuhan bisnis.
- Rekomendasi: konfirmasi visual di Step 10 dulu, lalu dev pilih. AI TIDAK mengubah business rule tanpa persetujuan.
- Perlu keputusan user sebelum Step 11.

---

### MF-04 — `odoo.osv` dihapus total di 20.0
**Ditemukan di:** Step 1 pre-scan (2026-09-24)
**Tag:** `[GAP-MIGRASI]`
**Ref:** `DIFF-04`, BSL-026
**Lokasi:** `personal_email_usage/models/mail.py:11`
**Deskripsi:** `odoo20/odoo/osv/` tidak ada (ls → No such file). `from odoo.osv import expression` → `ModuleNotFoundError` saat import modul → install-blocking. Simbol `expression` tidak dipakai di mana pun di file itu.
**Keputusan AI:** hapus baris import itu SAJA. Import tak terpakai lain (`requests`, `urllib.parse`, `re`, dst — semuanya masih ada di 20.0) dibiarkan (port kode, bukan cleanup).

---

### MF-05 — `self._cr` / `self._context` masih deprecated (belum dihapus) di 20.0
**Ditemukan di:** Step 2 (2026-09-24)
**Tag:** `[DIWARISI-SOURCE]` (informasional)
**Ref:** BSL-027, BSL-030, MF-04 (18→19)
**Lokasi:** `personal_email_usage/models/mail.py:138`; `fr_business_directory/models/siret_wizard.py:24,245,251,329,341`
**Deskripsi:** `odoo20/odoo/orm/models.py:5388-5401` — properti `_cr`/`_uid`/`_context` masih ada dengan `@deprecated("Deprecated since 19.0 ...")`. Tetap berfungsi, hanya `DeprecationWarning`.
**Keputusan:** tidak diubah (bukan wajib kompatibilitas; konsisten keputusan 18→19). Kandidat carry-over ke migrasi 20→21 kalau dihapus di sana.

---

### MF-06 — Penyesuaian test existing untuk 20.0
**Ditemukan di:** Step 2 (2026-09-24)
**Tag:** `[GAP-MIGRASI]` (test)
**Ref:** MF-02, MF-03, `fr_business_directory/tests/test_siret_wizard.py`
**Lokasi:** `test_siret_wizard.py:19,53-56,123-136`
**Deskripsi:** `test_select_result_overwrites_partner` meng-assert `self.partner.company_registry` (field tak ada di 20.0). Data dummy `_siege()['siret'] = '12345678900012'` belum tentu lolos `fr_siret.validate` (Luhn) → `select_siret` akan `ValidationError` di 20.0. Fixture `setUp` membuat partner dengan `'is_company': True` (field computed 20.0 — native test 20.0 sendiri masih memakai pola ini, `odoo20/odoo/addons/base/tests/test_res_partner.py:813`).
**Keputusan AI:** assertion → `self.partner._get_additional_identifier('FR_SIRET')`; data dummy siret diganti SIRET yang valid Luhn (hanya kalau yang lama terbukti tidak valid di G1); intent test tidak berubah. Ditambah test baru untuk mengunci deviasi MF-02 (SIRET tak valid → `ValidationError`, `FR_SIREN` terdeduksi, identifier lain tidak tersentuh) dan MF-03 (struktur view + nilai `is_company` pada partner baru via `Form`).

---

### MF-07 — Aset store branch rilis `19.0` tidak di-port
**Ditemukan di:** Step 1 / conditioning (2026-09-24)
**Tag:** `[PERLU-KEPUTUSAN]` (di luar port kode)
**Ref:** `CLAUDE.md` open item conditioning, `01a_MIGRATION_INTAKE.md` Ringkasan #1
**Lokasi:** `origin/19.0` — 13 commit tidak ada di `migration/19.0` (`00f78e7` "cleaning" … `bebaf14`), 137 file berbeda di `static/description/**` kedua addon (banner.png → banner.gif ~23MB, icon.png baru, folder `assets/` baru, `index.html` ditulis ulang) + fix key `images` manifest; `origin/19.0` juga TIDAK punya folder `tests/` `personal_email_usage` (MF-04 18→19).
**Keputusan pemilik modul:** ✅ **Dev 2026-09-24: TIDAK di-port** — baseline = `migration/19.0` HEAD apa adanya. Kalau aset store dibutuhkan di rilis 20.0, itu kerja terpisah (merge/cherry-pick oleh dev, di luar migrasi ini).

---

## Pendalaman MF-02 & MF-03 (2026-09-24, atas pertanyaan dev "blocker atau bukan?")

### MF-02 — BUKAN blocker (risiko praktis ~nol)
- Validator yang dipakai 20.0 = `stdnum.fr.siret.validate` (stdnum 1.19 di image test): cek 14 digit + Luhn + SIREN valid, **dengan pengecualian resmi La Poste** (`356000000…` pakai aturan jumlah-digit kelipatan 5, kantor pusat `35600000000048`). Diuji langsung: `33417522101010`, `73282932000074`, `35600000000048`, `35600000049837` VALID; `12345678900012` (dummy test lama) INVALID. Artinya aturan validasi = aturan INSEE sendiri — SIRET yang datang dari `recherche-entreprises.api.gouv.fr` (sumber resmi) lolos.
- Jalur level result hanya membuat baris kalau `siege.siret` terisi (BSL-028), jadi nilai kosong/aneh tidak sampai ke Select di jalur itu.
- SIRET yang tersimpan TETAP tampil di form partner walau negara partner kosong/bukan FR: `_compute_available_additional_identifiers_metadata` menyertakan key apa pun yang sudah tersimpan (`odoo20/.../res_partner.py:1641-1642`). Penting karena `select_siret` tidak mengisi `country_id` (model `res.country.department` tidak ada, BSL-006).
- Belum terverifikasi: perilaku API untuk perusahaan "non-diffusible" — dicek dengan API live di Step 10.

### MF-03 — BUKAN blocker untuk Step 10, TAPI regresi fungsional yang wajib diputuskan sebelum go-live
- Untuk partner tanpa parent, `is_company != True` di 20.0 **ekuivalen dengan "tidak punya VAT valid"** (`is_company = commercial_partner_id == partner and has_vat`, dan partner tanpa parent adalah commercial partner-nya sendiri). Jadi port literal = "tombol hanya muncul kalau partner SUDAH punya VAT".
- 20.0 tidak punya lagi pilihan Individual/Company di form (radio `company_type` hilang). Aturan 19.0 "tombol untuk kontak yang user tandai Company" tidak bisa direpresentasikan apa adanya.
- Yang tetap jalan: form baru dari aplikasi Contacts (`default_is_company=True`) → tombol tampil sebelum save → klik (web client menyimpan dulu lalu menjalankan aksi) → wizard terbuka. Perlu dikonfirmasi live di Step 10.
- Yang rusak dibanding 19.0: (a) company tanpa VAT yang sudah tersimpan tidak bisa membuka wizard lagi (mis. wizard ditutup tanpa Select, atau ingin refresh data); (b) partner yang dibuat dari jalur lain tanpa `default_is_company` tidak pernah melihat tombol; (c) "Select" mengisi SIRET, bukan VAT → setelah Select pun tombol tetap hilang.
- Native 20.0 sendiri memperlakukan "partner tanpa parent" setara company di beberapa logic (`_handle_first_contact_creation`: "for a company (or root)", `res_partner.py:914-920`; `commercial_partner_id`).
- Opsi: (1) pertahankan literal (status sekarang); (2) `invisible="parent_id"` — tombol untuk semua entitas tanpa parent (efek samping: individu pribadi tanpa parent juga melihat tombol, tidak berbahaya — wizard hanya mencari & menimpa atas konfirmasi); (3) varian lain sesuai kebutuhan bisnis. **Rekomendasi AI: opsi 2** (paling dekat dengan niat 19.0 di platform 20.0). Menunggu keputusan dev — AI tidak mengubah tanpa persetujuan.

### MF-03 — Keputusan dev 2026-09-24: WORKAROUND diterapkan, finding TETAP OPEN
- **Keputusan dev:** "Company tanpa VAT yang sudah tersimpan tidak bisa membuka wizard lagi" dinilai bisa jadi blocker → terapkan opsi 2 sebagai **workaround**, bukan fix final.
- **Diterapkan:** `fr_business_directory/views/partner.xml` — tombol `invisible="is_company != True"` → `invisible="parent_id"`.
- **Bukti:** `test_button_visibility_workaround_mf03` (company tanpa VAT tersimpan: `is_company=False`, `parent_id` kosong → tombol tampil & wizard terbuka; kontak anak → tombol tersembunyi); `test_partner_form_arch_has_name_and_button` assert `invisible="parent_id"`. Run `run-test.sh`: 0 failed, 0 error of 43.
- **Kenapa belum selesai (sisa gap yang diketahui):** (1) individu pribadi tanpa parent juga melihat tombol (di 19.0 tidak) — efek samping tidak berbahaya, tapi berbeda dari 19.0; (2) belum ada konfirmasi visual di browser (Step 10); (3) belum ada sign-off bisnis bahwa aturan baru ini yang diinginkan (Step 11). Kalau nanti ada aturan yang lebih tepat (mis. berdasarkan identifier company/SIRET), itu yang menutup finding ini.
- **Status:** 🟡 OPEN — workaround aktif.

---

## Cross-Version Compare (Step 10, 2026-09-24) — RMV-01..04

Environment: 20.0 `docker-env/` port 8196 vs 19.0 worktree `migration/19.0` @ `35c4e25` + `odoo:19.0` port 8197 (dibongkar setelah selesai). API gouv.fr live. Detail skenario: `10_qa/10_BUSINESS_FLOW_MIGRATION.md`.

### RMV-01 — Ikon Font Awesome rusak di 20.0 — `REGRESI` ✅ FIXED
- **Bukti:** 19.0 "🔍 Business Directory", "← Prev", "Next →" (`10_qa/evidence/cvc19-*.png`); 20.0 sebelum fix "-🔍 Business Directory", "-- Prev", "Next" tanpa panah (`evidence/s01-new-contact.png`, `s02-wizard-open.png`).
- **Root cause:** `odoo19/addons/web/static/src/views/view_button/view_button.js` `iconFromString()` mengenali prefix `fa-` → `fa fa-fw`; 20.0 (`odoo20/.../view_button.js:24-29`) SELALU `o_button_icon oi` + `data-icon=<nama>` (ligatur). CSS Font Awesome tidak lagi di-bundle (`web/static/src/libs/fontawesome/` tinggal ttf). Native 20.0: 0 view dengan `icon="fa-…"`.
- **Kenapa lolos Step 2/8/9:** tidak ada error/warning apa pun, arch tetap valid — hanya kelihatan di mata.
- **Fix:** `partner.xml` `icon="search"`; `siret_wizard_views.xml` `icon="arrow_back"` + `<i class="oi" data-icon="arrow_forward"/>` (`arrow_left/right` di font ini = caret kecil). Test `test_no_font_awesome_icons_rmv01`. `run-test.sh`: 0 failed, 0 error of 44. Visual ulang identik 19.0 (`evidence/s08-*.png`).

### RMV-02 — Select setelah paginasi menimpa partner yang SALAH — `GAP-LAMA` 🔴 ESCALATION
- **Bukti live (kedua versi):** wizard dibuka dari partner id 6 → Next → buka baris → Select → Ok ⇒ yang ditulis partner **id = id wizard**. 20.0: wizard 1 → partner 1 ("My Company", perusahaan sendiri: nama, alamat, SIRET tertimpa). 19.0: wizard 1 → partner 1; wizard 2 → partner 2 (OdooBot). Tanpa paginasi → partner 6 benar (S-07).
- **Mekanisme:** `fetch_next_page()`/`fetch_previous_page()` mengembalikan `ir.actions.act_window` TANPA `context`; web client me-reload dialog wizard dengan `active_id` = `res_id` wizard itu sendiri. `select_siret()` membaca `self._context.get('active_id')` → id wizard → `res.partner.browse(id_wizard)`.
- **Dampak produksi:** id wizard terus naik → kontak ACAK yang kebetulan ber-id sama ditimpa diam-diam (nama, alamat, SIRET, koordinat); kalau id tidak ada → Select tanpa efek. Tidak ada error.
- **Kenapa tidak ketahuan sebelumnya:** test Step 9 memanggil `select_siret()` dengan `active_id` eksplisit (tidak lewat reload dialog); UAT 18→19 menerima evidence AI tanpa klik manual.
- **ESCALATION — Migrasi 20.0** — Step 10 — `fr_business_directory`:
  - Opsi 1) Port apa adanya (known issue) — Risiko: **tinggi** (korupsi data kontak di produksi).
  - Opsi 2) Fix minimal: 4 `return` action paginasi membawa context asal (`'context': self.env.context`) — Risiko: rendah; mengubah bug bawaan (butuh persetujuan).
  - Opsi 3) Simpan `partner_id` di `siret.wizard`, jangan bergantung `active_id` — Risiko: rendah-sedang, perubahan lebih besar.
  - **Rekomendasi AI: Opsi 2.** Perlu keputusan dev sebelum Step 11.

### RMV-03 — 429 dari API memicu NameError (BSL-008) — `GAP-LAMA` 🟡
- **Bukti:** ±4 dari ±12 panggilan API selama Step 10 dibalas `429 Too Many Requests` (curl host juga: `429 200 200`). Tiap 429 → `requests.RequestException` → `_logger.error(...)` → `NameError` → dialog "Oops"; transaksi di-rollback (data aman).
- **Status:** bug bawaan yang wajib dipertahankan (BSL-008, AC-07-01). Dicatat karena pemicunya di dunia nyata SERING. Keputusan dev: pertahankan, atau fix ringan (`import logging` + `_logger`).

### RMV-04 — Kosmetik bawaan — `GAP-LAMA`
- "None FRM DE VALSERY": `str(siege.get('numero_voie', ''))` saat nilai `None` — sama di 19.0.
- Judul dialog wizard jadi "Odoo" setelah paginasi (action tanpa `name`) — sama di 19.0.
- Tidak difix.

### RMV-05 — Halaman hasil crash kalau API mengembalikan `libelle_voie: null` — `GAP-LAMA`
- **Bukti:** 2026-09-24, saat menyiapkan demo RMV-02 — pencarian "CARREFOUR" halaman 2 → `TypeError: can only concatenate str (not "NoneType") to str` → dialog "Oops".
- **Penyebab:** `str(siege.get('numero_voie', '')) + " " + siege.get('libelle_voie', '')` di `_fetch_siret_data()` — `.get()` mengembalikan `None` (key ADA dengan nilai null), bukan default `''`. Baris identik di 19.0 → bawaan, bukan regresi.
- **Dampak:** halaman tertentu tidak bisa dibuka untuk nama perusahaan tertentu (tergantung data API). Data aman (rollback).
- **Status:** dicatat, tidak difix (port apa adanya) — kandidat perbaikan pasca-migrasi bersama RMV-02/RMV-03.

### Demo repro RMV-02 (untuk cek manual dev)
- Skrip: `10_qa/rmv02_demo_setup.py` (idempoten; menyiapkan kontak asal "LA POSTE" dan "KONTAK KORBAN - JANGAN BERUBAH", lalu menyetel sequence `siret.wizard` supaya wizard berikutnya = id korban).
- Diverifikasi AI 2026-09-24 di DB `fbd_demo_rmv02`: setelah Next → Select, kontak korban (id 7) tertimpa (`4 QUAI DU POINT DU JOUR`, SIRET `35600054700014`), kontak asal (id 6) tidak berubah. Data sudah di-reset untuk dev.
- Catatan: kalau langkah apa pun memunculkan "Oops" (429), sequence wizard sudah terpakai walau transaksi rollback → jalankan ulang skrip reset sebelum mencoba lagi.

### RMV-06 — Next pertama memanggil API 2x (create wizard memicu `default_get` lagi) — `GAP-LAMA`
- **Bukti (2026-09-24, `odoo-bin shell`, `requests.get` di-mock untuk menghitung panggilan):** buka wizard = 1 panggilan (`page=1`); **simpan wizard (web client selalu `create` dulu sebelum tombol pertama) = 1 panggilan LAGI ke `page=1`**; `fetch_next_page` = 1 panggilan (`page=2`). Jadi klik Next pertama = 2 panggilan beruntun, satu sia-sia.
- **Penyebab:** `SiretWizard.default_get()` memanggil API setiap kali `active_id` ada di context — termasuk saat ORM `create()` mengisi default untuk field yang tidak dikirim. Hasil panggilan kedua juga membuat record `siret.wizard.result` yatim (tidak dipakai).
- **Dampak:** menambah beban ke API yang ber-rate-limit (7/detik, bisa diturunkan saat padat) → memperbesar peluang 429 (RMV-03). Perilaku ORM sama di 19.0 → bawaan.
- **Status:** dicatat; kandidat perbaikan bersama RMV-02/RMV-03.

### Klarifikasi sumber error "Oops" (atas pertanyaan dev 2026-09-24)
- **Pemicu = API (eksternal):** 429 muncul juga dari `curl` host (di luar Odoo & addon) dan dari fetch server lain ke halaman dokumentasi API (`Retry-After: 4`); dokumentasi resmi (data.gouv.fr, DINUM): gratis, tanpa key, batas 7 panggilan/detik yang boleh diturunkan saat server padat.
- **Dialog "Oops" = bug addon kita:** traceback menunjuk `fr_business_directory/models/siret_wizard.py:145` `NameError: name '_logger' is not defined` di blok `except requests.RequestException`. Tanpa bug ini, 429 hanya di-log dan wizard tampil tanpa hasil (tanpa traceback). Kode ini identik 16.0–20.0.
- **Addon ikut memperbesar peluang 429:** RMV-06.

---

## Paket perbaikan pasca-Step 10 — RMV-02, RMV-03, RMV-06 (disetujui dev 2026-09-24)

**Keputusan dev (chat 2026-09-24):** "YA catat, dan perbaiki, tentu pesan yang muncul default pakai bahasa inggris". Ini **deviasi yang disengaja dari perilaku 19.0** (bug bawaan diperbaiki atas izin eksplisit, pengecualian dari aturan "jangan perbaiki bug 19.0" di `CLAUDE.md`). Baseline `01b_BASELINE_SPEC.md` tetap mendokumentasikan perilaku 19.0 apa adanya (BSL-008, dll.) — perubahan tercatat di sini dan di AC.

| Finding | Perubahan (`fr_business_directory/`) | Bukti |
|---|---|---|
| RMV-03 | `models/siret_wizard.py`: `import logging` + `_logger` (menutup BSL-008 `NameError`); helper `_get_directory_response()` — pada HTTP 429 coba ulang maks. 2x, menunggu `Retry-After` (dibatasi 5 detik); `RequestException` → `_logger.error` + `UserError` berbahasa Inggris: 429 → *"The company directory service (recherche-entreprises.api.gouv.fr) is busy right now. Please wait a moment and try again."*, lainnya → *"… could not be reached. Please try again later."* (lewat `_()`, bisa diterjemahkan). Hasil API tanpa nama/SIRET kini di-log warning dan di-skip (niat kode asli). | Test: `test_429_is_retried_then_succeeds`, `test_retry_after_is_capped`, `test_429_persisting_shows_english_busy_message`, `test_connection_error_shows_english_unreachable_message`, `test_429_on_next_page_keeps_wizard_state`, `test_malformed_result_is_logged_and_skipped` (menggantikan test `[PRESERVE-BUG]` NameError). Live 2026-09-24 10:10: log `Directory API rate limited (429), retrying in 4.0s` → halaman 2 tampil, tanpa "Oops". |
| RMV-06 | `default_get()` memanggil API hanya kalau `result_ids` diminta (saat dialog dibuka); `views/siret_wizard_views.xml`: `force_save="1"` pada `result_count`, `page_number`, `total_pages` supaya nilainya ikut terkirim saat wizard disimpan (web client 20.0 `record.js` `_getChanges` tidak mengirim field read-only tanpa `force_save`). | Test: `test_open_calls_api_once_and_save_does_not_call_it_again`, `test_wizard_view_sends_readonly_counters`. Live: `web_save` selesai ±7 ms tanpa panggilan API; `total_pages=400` tersimpan; 25 hasil (tanpa record yatim). |
| RMV-02 | 4 `return` action paginasi (`fetch_next_page`/`fetch_previous_page`) menambahkan `'context': dict(self.env.context)` — `active_id` = kontak asal ikut ke dialog yang di-reload. | Test: `test_pagination_actions_keep_active_id`, `test_select_after_pagination_writes_original_partner`. Live (data demo `rmv02_demo_setup.py`): Next → Select → kontak asal id 6 ter-update (`4 QUAI DU POINT DU JOUR`, SIRET `35600054700014`), kontak korban id 7 & "My Company" utuh (`10_qa/evidence/s09-rmv02-fixed-asal.png`). |

**Regresi:** `run-test.sh` → **0 failed, 0 error of 53 tests** (44 sebelumnya + 9 baru).
**Tidak termasuk paket ini (tetap GAP-LAMA, belum diputuskan):** RMV-04 (kosmetik "None"/judul "Odoo"), RMV-05 (`TypeError` saat `libelle_voie` null → masih bisa memunculkan "Oops" untuk nama perusahaan tertentu).
