# Demo data untuk cek visual manual dev (2026-09-25): MF-03 (visibilitas tombol), RMV-04 (kosmetik),
# RMV-05 (crash null). Dijalankan lewat `odoo-bin shell` (stdin), idempoten (dicari lewat `ref`).
Partner = env['res.partner']


def upsert(ref, vals):
    rec = Partner.search([('ref', '=', ref)], limit=1)
    if rec:
        rec.write(vals)
    else:
        rec = Partner.create(dict(vals, ref=ref))
    return rec


demo1 = upsert('DEMO-MF03-1', {'name': 'DEMO 1 - PERUSAHAAN TANPA VAT', 'vat': False, 'parent_id': False})
demo2 = upsert('DEMO-MF03-2', {'name': 'DEMO 2 - PERUSAHAAN DENGAN VAT', 'vat': 'FR23334175221', 'parent_id': False})
demo3 = upsert('DEMO-MF03-3', {'name': 'DEMO 3 - Karyawan (kontak anak)', 'vat': False, 'parent_id': demo2.id})
demo4 = upsert('DEMO-MF03-4', {'name': 'DEMO 4 - Individu tanpa perusahaan', 'vat': False, 'parent_id': False})
demo5 = upsert('DEMO-RMV05', {'name': 'CARREFOUR', 'vat': False, 'parent_id': False})
env.cr.commit()
for rec in (demo1, demo2, demo3, demo4, demo5):
    print(f"DEMO id={rec.id} is_company={rec.is_company} parent={rec.parent_id.name or '-'} name={rec.name}")
