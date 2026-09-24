#!/usr/bin/env bash
# ==========================================================================
# run-test.sh — wrapper WAJIB untuk SEMUA eksekusi test G2/Step 9 lewat Docker
# ==========================================================================
# Diinstansiasi dari migration-tool/templates/run-test.sh.template (2026-09-24,
# french_business_directory 19.0->20.0). KENAPA FILE INI ADA (jangan hapus):
#
# Argumen `--test-tags /<module>` (diawali garis miring) rawan di-mangle MSYS/Git
# Bash di Windows jadi path Windows SEBELUM sampai ke docker/odoo-bin -> tag filter
# kosong -> "0 failed, 0 error(s) of 0 tests" dengan exit code 0 = FALSE-PASS.
# Wrapper ini memaksa MSYS_NO_PATHCONV=1 dan GAGAL (exit 2) kalau 0 test method
# benar-benar ter-start.
#
# Adaptasi 20.0 terhadap template:
# - Tidak ada image resmi odoo:20.0 -> odoo-bin dijalankan dari source (/odoo20,
#   di-mount read-only, lihat docker-compose.yml), koneksi DB eksplisit.
# - `--without-demo=all` TIDAK dipakai: default 20.0 sudah tanpa demo, dan nilai
#   "all" memicu WARNING "invalid boolean value" di 20.0.
# - `docker compose down -v` dulu: DB yang sudah pernah -i modul yang sama akan
#   diam-diam skip install & test (gotcha 19-to-20.md).
# - Hitungan "Starting" dibatasi ke baris `Starting <Class>.test_*` (20.0 juga
#   mencetak "Starting post tests" yang bukan test method).
#
# USAGE (dari folder docker-env/):
#   ./run-test.sh <service> <db_name> <modules_csv> [extra_tags]
# CONTOH:
#   ./run-test.sh odoo fbd_test_20 fr_business_directory,personal_email_usage
# ==========================================================================
set -euo pipefail

SERVICE="${1:?Usage: run-test.sh <service> <db_name> <modules_csv> [extra_tags]}"
DB_NAME="${2:?Usage: run-test.sh <service> <db_name> <modules_csv> [extra_tags]}"
MODULES="${3:?Usage: run-test.sh <service> <db_name> <modules_csv> [extra_tags]}"
EXTRA_TAGS="${4:-}"

TAGS="$(echo "${MODULES}" | sed 's#^#/#; s#,#,/#g')${EXTRA_TAGS}"
LOGFILE="$(mktemp)"

echo "=== run-test.sh: MSYS_NO_PATHCONV=1 dipaksa otomatis ==="
echo "=== service=${SERVICE} db=${DB_NAME} modules=${MODULES} tags=${TAGS} ==="
echo "=== log lengkap: ${LOGFILE} ==="

docker compose down -v >/dev/null 2>&1 || true
docker compose up -d db >/dev/null 2>&1

# Baris paling penting di file ini — JANGAN hapus prefix MSYS_NO_PATHCONV=1.
set +e
MSYS_NO_PATHCONV=1 docker compose run --rm "${SERVICE}" \
  python3 /odoo20/odoo-bin -d "${DB_NAME}" \
  --db_host=db --db_user=odoo --db_password=odoo --data-dir=/var/lib/odoo \
  --addons-path=/odoo20/addons,/mnt/extra-addons \
  -i "${MODULES}" \
  --test-enable --test-tags "${TAGS}" --stop-after-init 2>&1 | tee "${LOGFILE}" >/dev/null
RUN_EXIT=${PIPESTATUS[0]}
set -e

echo ""
echo "=== Sanity check otomatis ==="
STARTED_COUNT=$(grep -cE "Starting [A-Za-z0-9_]+\.test_" "${LOGFILE}" || true)
SUMMARY_LINE=$(grep -E "[0-9]+ failed, [0-9]+ error\(s\) of [0-9]+ tests" "${LOGFILE}" | tail -1 || true)
echo "Exit code odoo-bin: ${RUN_EXIT}"
echo "Baris 'Starting <Class>.test_*' ditemukan: ${STARTED_COUNT}"
echo "Baris ringkasan resmi Odoo: ${SUMMARY_LINE:-'(tidak ditemukan)'}"
grep -E " (ERROR|CRITICAL) " "${LOGFILE}" | cut -c1-240 || true
grep -E "WARNING" "${LOGFILE}" | cut -c1-240 | sort -u || true

docker compose down >/dev/null 2>&1 || true

if [ "${STARTED_COUNT}" -eq 0 ]; then
  echo "GAGAL — 0 test method ter-start (pola false-pass). Buka ${LOGFILE}."
  exit 2
fi
echo "OK — ${STARTED_COUNT} test method benar-benar ter-eksekusi (bukan false-pass)."
exit "${RUN_EXIT}"
