# Diff & Compatibility Analysis — french_business_directory

**Step:** 2 — Diff & Compatibility Analysis
**Versi:** 17.0 → 18.0
**Tanggal:** 2026-08-24
**Ref:** `01_intake/01a_MIGRATION_INTAKE.md`, `migration-tool/knowledge/version-diffs/17-to-18.md`

---

## 0. Knowledge Base Check

| Sumber | Sudah ada entry? | Lokasi |
|---|---|---|
| `version-diffs/17-to-18.md` | Ya | dipakai sebagai referensi utama §1 di bawah |
| `dependency-compat/<nama>/...` | Tidak ada entry untuk `l10n_fr`/`mail`/`fetchmail`/`contacts` | — (dependency modul ini belum pernah dianalisis project migrasi lain) |

## 0b. Gate Community vs Enterprise

- `01a_MIGRATION_INTAKE.md` §2 — **TIDAK ADA** baris bertipe "Native Enterprise" (semua dependency: `base`/`contacts`/`l10n_fr`/`mail`, semua Native Community).
- Lanjut §1 cukup dengan `native-target`/`native-source` (Community) untuk verifikasi utama. `native-target-enterprise`/`native-source-enterprise` tetap dicek untuk MF-01 (`res.country.department`, lihat §2 di bawah) — hasilnya NEGATIF di keempat repo (dicek langsung, lihat `FINDINGS.md` MF-01).

## 0c. Gate Transitive Dependency

- Tidak ada dependency yang akan DIHAPUS dari `depends` (semua 4 dependency: `base`/`contacts`/`l10n_fr`/`mail` tetap ada dan tidak berubah nama di 18.0 — dikonfirmasi §1 di bawah). Gate ini **N/A**.

---

## 1. Perubahan Native (Core/Enterprise)

| ID | File/simbol modul | Simbol native terkait | Status di target | Dampak | Sumber |
|---|---|---|---|---|---|
| DIFF-01 | `fr_business_directory/views/siret_wizard_views.xml:25,26,51` — `mode="tree"` + dua tag `<tree>` | Parser ORM view type Odoo 18.0 | **Dihapus** — `<tree>` tidak lagi valid, wajib `<list>` (`mode="tree"`→`mode="list"`, `<tree>`→`<list>`) | **Critical — install-blocking.** Knowledge base (`17-to-18.md` §1, dry run terverifikasi `odoo:18.0`) mengonfirmasi ini `ParseError: Invalid view type: 'tree'` saat parsing XML, BUKAN sekadar warning — modul gagal install total kalau tidak diperbaiki. Wajib Fase C (view fixes) step 6. | Knowledge base `17-to-18.md` §1 (PR resmi `odoo/odoo#159909`) |
| DIFF-02 | `personal_email_usage/models/mail.py:61` — override `fetch_mail(self)` (tanpa parameter) | `mail/models/fetchmail.py` — `fetch_mail()` core | **Signature berubah**: 17.0 `def fetch_mail(self):` → 18.0 `def fetch_mail(self, raise_exception=True):`. Cron entry point `_fetch_mails()` di 18.0 memanggil `.fetch_mail(raise_exception=False)` (17.0 memanggil polos tanpa argumen). | **Critical — runtime-blocking.** Override modul ini tidak punya parameter `raise_exception` sama sekali — begitu cron jalan di 18.0, `TypeError: fetch_mail() got an unexpected keyword argument 'raise_exception'` untuk SEMUA server (IMAP maupun POP), bukan cuma path IMAP yang di-override. Wajib update signature override jadi `def fetch_mail(self, raise_exception=True):` (kompatibilitas wajib, bukan perubahan business logic) — lihat `FINDINGS.md` MF-07. Behavior internal (log-only, tidak raise) tetap dipertahankan identik untuk path IMAP; `super()` call untuk path non-IMAP wajib teruskan `raise_exception=raise_exception`. | Verifikasi langsung `native-source` vs `native-target` (`fetchmail.py:213-215`) |
| DIFF-03 | `personal_email_usage/models/mail.py:236-238` — panggilan `imap_server.store`, `MailThread.message_process(...)` (logic yang di-copy dari core) | `mail/models/fetchmail.py` IMAP branch (baris 228-254 di `native-source`, 228-257 di `native-target`) | **Tidak berubah** secara struktural — urutan `search(UNSEEN)`→`fetch(RFC822)`→`store(-FLAGS Seen)`→`message_process`→`store(+FLAGS Seen)`→`commit` identik. Satu-satunya beda: exception handling `except Exception:` (17.0, selalu log) → `except Exception as e: if raise_exception: raise ValidationError(...) else: log` (18.0) — **tapi cabang ini sudah TOTAL di-override modul custom** (tidak pernah lewat kode core ini untuk server IMAP), jadi perubahan behavior exception handling core TIDAK relevan langsung — cukup relevan lewat DIFF-02 (signature) di atas. | Rendah (informasional, tidak butuh aksi tambahan di luar DIFF-02) | Verifikasi langsung `native-source`/`native-target` |
| DIFF-04 | `fr_business_directory/views/partner.xml` — `inherit_id="base.view_partner_form"`, `position="replace"` pada `<field id="company" name="name" ...>` | `base/views/res_partner_views.xml` record `view_partner_form` | **Tidak berubah** — byte-identical (`id="company"`, `options="{'line_breaks': False}"`, `widget="text"`, `class="text-break"`, `name="name"`, `default_focus="1"`, `placeholder`, `invisible="not is_company"`, `required="type == 'contact'"`) di `native-source` (baris 189) dan `native-target` (baris 160). Xpath target tetap resolve, `position="replace"` aman 1:1. | Tidak ada — port langsung | Verifikasi langsung `native-source`/`native-target` |
| DIFF-05 | `fr_business_directory/models/partner.py:6` — `social_reason = fields.Char(..., tracking=True)` pada `_inherit = 'res.partner'` | `res.partner` core (`base`) | Tidak berubah — `_inherit`/`tracking=True` mechanism tidak terpengaruh perubahan 17→18 manapun di knowledge base | Tidak ada | Analisis — tidak ada perubahan API tracking field 17→18 di knowledge base |
| DIFF-06 | `l10n_fr` — field `siret` (`res.partner`, `res.company`) dipakai tidak langsung (ditulis via `partner.write({'siret': ...})`) | `l10n_fr/models/res_partner.py`, `res_company.py` | **Tidak berubah** — byte-identical `siret = fields.Char(string='SIRET', size=14)` di kedua versi (hanya beda nomor baris kosmetik, 9→10) | Tidak ada | Verifikasi langsung `native-source`/`native-target` |
| DIFF-07 | `res.country.department` (model eksternal, dipakai `fr_business_directory/models/siret_wizard.py:254,346`) | Tidak ada di native manapun | **Tidak ditemukan** di `native-source`, `native-target`, `native-source-enterprise`, `native-target-enterprise` (pencarian menyeluruh `rg` di seluruh `addons/`, bukan cuma `l10n_fr`) | Lihat `FINDINGS.md` MF-01 — soft-dependency eksternal, ditunda (tidak ada `third-party-*` di-connect), kode sudah defensif (cek `ir.model` dulu) jadi tidak install/runtime-blocking apapun kondisinya | Verifikasi langsung, 4 repo |
| DIFF-08 | `personal_email_usage/views/mail_views.xml` — `xpath expr="//field[@name='attach']"` pada `inherit_id="mail.view_email_server_form"` | `mail/views/fetchmail_views.xml` — field `attach` di form `fetchmail.server` | **Tidak berubah** — field `attach` tetap ada di `native-source` dan `native-target` | Tidak ada — port langsung. Ditemukan sebagai gap saat Step 4 (Spec Completeness Review), sebelumnya belum eksplisit di §1 | Verifikasi langsung `native-source`/`native-target` |

## 2. Kompatibilitas Dependency (OCA/Third-Party)

| Dependency | Versi target tersedia? | Sumber cek | Risiko |
|---|---|---|---|
| Addon eksternal penyedia `res.country.department` (kemungkinan OCA `l10n_fr_department`) | Tidak dicek — `third-party-source`/`third-party-target` belum di-connect (ditunda, lihat `FINDINGS.md` MF-01) | — | Rendah untuk instalasi (kode sudah defensif) — TAPI kalau memang dipakai di produksi, fitur auto-fill department/state/country tidak tervalidasi kompatibel 18.0 sampai dicek |

## 3. Temuan Baru — Ditulis ke Migration Records

- [x] Temuan general (version-diff): DIFF-02 (`fetch_mail()` signature `raise_exception`) — pola ini relevan untuk MODUL LAIN manapun yang override `fetch_mail()`/`_inherit fetchmail.server`, bukan spesifik modul ini. Dicatat sebagai kandidat kategori `version-diff` di `migration-tool/migration-records/french_business_directory_17.0_18.0/SUMMARY.md`.
- [ ] Temuan per-dependency: tidak ada (dependency `l10n_fr`/`base`/`contacts`/`mail` semua stabil, tidak ada finding baru yang perlu di-generalisasi ke `dependency-compat/`)
- Promosi ke `knowledge/` HANYA lewat sesi curation terpisah — belum dilakukan di step ini.

## 4. Ringkasan Risiko

| Item | Level risiko | Catatan |
|---|---|---|
| DIFF-01 — `<tree>`→`<list>` di `siret_wizard_views.xml` | **Tinggi (install-blocking kalau tidak diperbaiki)** | Wajib Fase C, step 6 — mekanis, tidak mengubah business logic |
| DIFF-02 — signature `fetch_mail(raise_exception=True)` | **Tinggi (runtime-blocking di cron)** | Wajib Fase A/B (compat fix), step 6 — kompatibilitas wajib, bukan perubahan business logic, behavior IMAP path tetap log-only dipertahankan |
| DIFF-04, DIFF-05, DIFF-06 | Rendah | Port 1:1, tidak ada perubahan diperlukan |
| DIFF-07 / MF-01 (OCA `res.country.department`) | Rendah-Sedang (belum tervalidasi) | Ditunda ke Step 9/10 kalau relevan |

**Kesimpulan Step 2:** modul ini TIDAK punya Owl/JS/controller/kanban/chatter custom (dikonfirmasi `01a_MIGRATION_INTAKE.md` §2b) — sebagian besar item breaking change di knowledge base (Owl rewrite, asset manifest, `<div class="oe_chatter">`, dll) **N/A**. Dua item genuinely applicable (DIFF-01, DIFF-02) sudah teridentifikasi konkret dengan lokasi pasti — Step 3 (Migration Spec) bisa langsung fokus ke dua fix ini plus port mekanis biasa (copy source → target, sesuaikan `__manifest__.py` version number).
