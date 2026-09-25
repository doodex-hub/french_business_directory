# UAT Checklist — Migrasi french_business_directory (19.0 → 20.0)

**Step:** 11 — UAT Sign-off (final)
**Ref:** `05_acceptance/05a_MIGRATION_ACCEPTANCE_CRITERIA.md`, `10_qa/10_BUSINESS_FLOW_MIGRATION.md`, `FIX_TRACKER.md`
**Tanggal disusun:** 2026-09-25
**Status:** ⏳ Menunggu dijalankan & ditandatangani oleh user (AI hanya menyusun — kolom Actual/Status/Sign-off sengaja kosong)

> Kriteria sukses: user tidak merasakan perbedaan dengan 19.0, **kecuali** perubahan yang sudah disepakati (lihat "Review Item Out-of-Scope / Perubahan yang Disepakati").
> Dokumen ini adalah **skrip test untuk dijalankan sendiri** — bukan laporan hasil AI.

---

## Persiapan Sebelum UAT (Precondition & Data)

- [ ] Server UAT: **http://localhost:8196**, database **`fbd_uat_20`** (Odoo 20.0, kedua modul terinstall, tanpa data demo). Disiapkan AI lewat `docker-env/` — lihat langkah di bagian bawah.
- [ ] Login **Administrator**: `admin` / `admin` (hanya untuk menyetel password user UAT).
- [ ] User UAT non-admin sudah dibuat AI: **"UAT Contacts User"**, login **`uat_contacts`**, hak: *User* internal + *Contact Creation*. **Password belum di-set — setel sendiri:** Settings → Users & Companies → Users → UAT Contacts User → ⚙ → Change Password.
- [ ] Jalankan skenario T-01..T-06 sebagai **UAT Contacts User** (bukan Administrator); T-07 sebagai Administrator (butuh mode developer).
- [ ] Koneksi internet ke `recherche-entreprises.api.gouv.fr` tersedia. API ini gratis dan dibatasi — kalau muncul pesan *"The company directory service … is busy right now …"*, tunggu ±30 detik lalu ulangi; itu **bukan** kegagalan.
- [ ] Database ini hanya untuk UAT (bukan produksi).

## Skenario Test (Test Script)

### T-01: Tombol "Business Directory" pada kontak perusahaan baru

**Data dummy:** nama perusahaan **`LA POSTE`**

| # | Langkah | Expected | Actual | Status |
|---|---|---|---|---|
| 1 | Buka menu **Contacts** → klik **New** | Form kontak baru terbuka | | [ ] Pass [ ] Fail |
| 2 | Lihat di kanan field nama | Ada tombol **🔍 Business Directory** (ikon kaca pembesar, tanpa tanda "-") | | [ ] Pass [ ] Fail |
| 3 | Ketik nama `LA POSTE`, klik **🔍 Business Directory** | Kontak tersimpan otomatis; dialog **"Search For Companies"** terbuka berisi "… Results Found" dan daftar perusahaan | | [ ] Pass [ ] Fail |
| 4 | Klik **Cancel**, lalu klik **🔍 Business Directory** lagi (kontak sekarang sudah tersimpan, belum punya Tax ID) | Tombol tetap ada dan dialog terbuka lagi | | [ ] Pass [ ] Fail |

### T-02: Paginasi hasil pencarian

**Data dummy:** kontak `LA POSTE` dari T-01

| # | Langkah | Expected | Actual | Status |
|---|---|---|---|---|
| 1 | Di dialog "Search For Companies", lihat tombol halaman | Tertulis **"← Prev"**, `1 / 400` (atau angka lain), **"Next →"** | | [ ] Pass [ ] Fail |
| 2 | Klik **Next →** | Halaman menjadi `2 / …`, daftar berganti; judul dialog tetap **"Search For Companies"** | | [ ] Pass [ ] Fail |
| 3 | Klik **← Prev** | Kembali ke halaman `1 / …` | | [ ] Pass [ ] Fail |
| 4 | Di halaman 1, klik **← Prev** lagi | Lompat ke halaman terakhir (mis. `400 / 400`) | | [ ] Pass [ ] Fail |
| 5 | Di halaman terakhir, klik **Next →** | Kembali ke halaman `1 / …` | | [ ] Pass [ ] Fail |

### T-03: Pilih data perusahaan → kontak terisi (termasuk setelah pindah halaman)

**Data dummy:** kontak `LA POSTE`; buat juga kontak pembanding **`KONTAK PEMBANDING`** (Contacts → New → nama itu → Save) dan catat alamatnya (kosong)

| # | Langkah | Expected | Actual | Status |
|---|---|---|---|---|
| 1 | Buka `LA POSTE` → **🔍 Business Directory** → klik **Next →** sekali | Halaman `2 / …` | | [ ] Pass [ ] Fail |
| 2 | Klik salah satu baris perusahaan | Dialog daftar lokasi (etablissement) terbuka: kolom Siret, Core Business, Address, Date Creation, Status | | [ ] Pass [ ] Fail |
| 3 | Lihat kolom Status | Lokasi aktif tampil badge **hijau "en activité"**; yang tutup badge **merah "fermé le …"** | | [ ] Pass [ ] Fail |
| 4 | Klik **Select** di satu baris | Muncul konfirmasi **"Are you sure want to overwrite the Data?"** | | [ ] Pass [ ] Fail |
| 5 | Klik **Ok**, tutup dialog, buka kontak `LA POSTE` | Nama, alamat (Street), kode pos, kota terisi dari baris yang dipilih; field **SIRET** dan **SIREN** terisi | | [ ] Pass [ ] Fail |
| 6 | Buka `KONTAK PEMBANDING` | **Tidak berubah** (alamat tetap kosong) | | [ ] Pass [ ] Fail |
| 7 | Cek kontak perusahaan sendiri (nama perusahaan di pojok kanan atas / Settings → Companies) | **Tidak berubah** | | [ ] Pass [ ] Fail |

### T-04: Tampilan alamat hasil pencarian

**Data dummy:** nama kontak **`CARREFOUR`**

| # | Langkah | Expected | Actual | Status |
|---|---|---|---|---|
| 1 | Contacts → New → nama `CARREFOUR` → **🔍 Business Directory** → **Next →** | Halaman `2 / …` terbuka **tanpa** dialog "Oops"/error teknis | | [ ] Pass [ ] Fail |
| 2 | Perhatikan kolom **Street** | Tidak ada teks **"None"** di depan nama jalan (mis. tampil "DES ERABLES", bukan "None DES ERABLES") | | [ ] Pass [ ] Fail |

### T-05: Siapa yang mendapat tombol

**Data dummy:** perusahaan **`PT UJI DENGAN VAT`** (Tax ID: `FR23334175221`), karyawan **`Budi Karyawan`** (Company: `PT UJI DENGAN VAT`), individu **`Marie Dupont`** (tanpa company)

| # | Langkah | Expected | Actual | Status |
|---|---|---|---|---|
| 1 | Buat `PT UJI DENGAN VAT` dengan Tax ID `FR23334175221`, Save | Tombol **Business Directory** tampil | | [ ] Pass [ ] Fail |
| 2 | Buat `Budi Karyawan`, isi field Company (ikon gedung) = `PT UJI DENGAN VAT`, Save | Tombol **tidak** tampil | | [ ] Pass [ ] Fail |
| 3 | Buat `Marie Dupont` tanpa Company, Save | Tombol **tampil** (perubahan yang disepakati — lihat bawah) | | [ ] Pass [ ] Fail |

### T-06: Tutup dialog tanpa memilih

| # | Langkah | Expected | Actual | Status |
|---|---|---|---|---|
| 1 | Buka `LA POSTE` → Business Directory → klik **Cancel** | Dialog tertutup; data kontak tidak berubah | | [ ] Pass [ ] Fail |

### T-07: Incoming Mail Server — pilihan "Mark Emails as Read" (Administrator)

| # | Langkah | Expected | Actual | Status |
|---|---|---|---|---|
| 1 | Login Administrator → Settings → aktifkan **Developer mode** | Mode developer aktif | | [ ] Pass [ ] Fail |
| 2 | Settings → Technical → Incoming Mail Servers → **New** → tab **Advanced** | Ada checkbox **Mark Emails as Read** setelah "Keep Attachments", default **tidak** dicentang | | [ ] Pass [ ] Fail |
| 3 | Matikan Developer mode, buka lagi form yang sama | Checkbox **Mark Emails as Read** tidak tampil | | [ ] Pass [ ] Fail |

### T-XX: Item yang TIDAK Bisa Dites Lewat Tampilan Biasa (Informasi, Bukan Kegagalan)

- **SIRET tidak valid dari API** → pesan *"The company directory returned an invalid SIRET (…). The contact was not updated."* — API resmi selalu mengirim SIRET valid, jadi tidak bisa dipicu; dibuktikan test otomatis (MF-02, `test_select_invalid_siret_raises_validation_error`).
- **API sibuk terus-menerus** → pesan *"…is busy right now…"* — tidak bisa dipicu sesuka hati; dibuktikan test otomatis (RMV-03). Kalau kebetulan muncul saat UAT, justru itu bukti perilakunya.
- **Filter email masuk** (lewati email dari user internal / bukan kontak, cegah duplikat, Mark as Read) — butuh server IMAP sungguhan; dibuktikan 14 test otomatis `personal_email_usage` (Step 9).
- **Isi departemen/provinsi otomatis** — hanya aktif kalau modul tambahan `res.country.department` terinstall (tidak ada di environment manapun, sama seperti 19.0).

## Sign-off per Kelompok Fitur

| # | Kelompok fitur | Skenario tercakup | Status | Catatan |
|---|---|---|---|---|
| 1 | Business Directory — tombol & wizard | T-01, T-02, T-05, T-06 | [ ] Pass [ ] Fail | |
| 2 | Business Directory — Select mengisi kontak | T-03, T-04 | [ ] Pass [ ] Fail | |
| 3 | Personal Email Usage — konfigurasi server | T-07 | [ ] Pass [ ] Fail | |

## Review Item Out-of-Scope / Perubahan yang Disepakati

Stakeholder mengonfirmasi sadar & menerima (detail: `FINDINGS.md`, `FIX_TRACKER.md`):

- [ ] **Tombol untuk semua kontak tanpa parent** (termasuk individu seperti `Marie Dupont`) — Odoo 20 tidak lagi punya pilihan Person/Company (MF-03, opsi A).
- [ ] **SIRET disimpan di identifier Odoo 20** (field SIRET/SIREN di form), divalidasi; SIRET tidak valid ditolak dengan pesan modul (MF-02, opsi B).
- [ ] **Perbaikan bug bawaan 19.0** yang disetujui: Select setelah Next/Prev kini mengisi kontak yang benar (RMV-02); API sibuk tidak lagi menampilkan error teknis (RMV-03); API tidak dipanggil ganda (RMV-06); halaman tertentu tidak lagi crash (RMV-05); tidak ada "None" di alamat & judul dialog tetap (RMV-04).
- [ ] **Tidak di-port:** aset halaman toko Odoo dari branch rilis 19.0 (MF-07).
- [ ] **Dibiarkan:** peringatan deprecation `self._cr`/`self._context` di log (MF-05).

## Prasyarat Sebelum Go-Live Produksi

- [ ] Port kode saja (tanpa data produksi) — **tidak ada rehearsal upgrade data**; kalau nanti modul dipasang di database yang sudah punya data 19.0, upgrade data (termasuk `company_registry` → identifier SIRET) dilakukan oleh script upgrade Odoo, bukan modul ini — rehearsal wajib saat itu.
- [ ] Backup database produksi sebelum install/upgrade.
- [ ] README modul direview (tidak menyebut versi lama — sudah dicek di Step 6 A6).
- [ ] `git push` branch `migration/20.0` (manual oleh dev).

## Sign-off

| Role | Nama | Tanggal | Tanda tangan |
|---|---|---|---|
| PM | | | |
| FA | | | |
| User | | | |

> Kosong sampai skenario di atas dijalankan sendiri. Setelah sign-off lengkap, AI menulis `doc/MIGRATION_CLOSED.md` (SHA HEAD `migration/20.0` saat itu).

## Penutupan Migrasi

- [ ] `doc/MIGRATION_CLOSED.md` ditulis dengan SHA + tanggal + branch target.
