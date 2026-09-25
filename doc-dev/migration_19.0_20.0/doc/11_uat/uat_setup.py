# UAT setup (Step 11, 2026-09-25) — dijalankan lewat `odoo-bin shell` (stdin) pada DB `fbd_uat_20`.
# Membuat user UAT non-admin (internal user + Contact Creation). Password SENGAJA tidak di-set:
# dev/user menyetelnya sendiri lewat Settings → Users (lihat 11_UAT_CHECKLIST.md "Persiapan").
Users = env['res.users'].with_context(no_reset_password=True)
user = Users.search([('login', '=', 'uat_contacts')], limit=1)
groups = [env.ref('base.group_user').id, env.ref('base.group_partner_manager').id]
if not user:
    user = Users.create({
        'name': 'UAT Contacts User',
        'login': 'uat_contacts',
        'group_ids': [(6, 0, groups)],
    })
else:
    user.write({'group_ids': [(4, g) for g in groups]})
env.cr.commit()
print(f"UAT READY user_id={user.id} login={user.login} groups={user.group_ids.mapped('name')}")
