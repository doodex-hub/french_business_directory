from unittest.mock import patch, MagicMock

from odoo.tests.common import TransactionCase, tagged


def _raw_email(from_addr, message_id='<test-1@example.com>', body='hello'):
    return (
        f"From: {from_addr}\r\n"
        f"To: test@example.com\r\n"
        f"Subject: test\r\n"
        f"Message-ID: {message_id}\r\n"
        f"\r\n{body}\r\n"
    ).encode('utf-8')


def _mock_imap(unseen_nums, raw_by_num):
    conn = MagicMock()
    conn.select.return_value = None
    conn.search.return_value = ('OK', [b' '.join(n.encode() for n in unseen_nums)])
    conn.fetch.side_effect = lambda num, spec: ('OK', [(b'dummy', raw_by_num[num.decode() if isinstance(num, bytes) else num])])
    return conn


@tagged('post_install', '-at_install')
class TestFetchmailOverride(TransactionCase):

    def setUp(self):
        super().setUp()
        self.internal_user = self.env['res.users'].create({
            'name': 'Internal User',
            'login': 'internal@example.com',
            'email': 'internal@example.com',
        })
        self.known_partner = self.env['res.partner'].create({
            'name': 'Known Contact',
            'email': 'known@example.com',
        })
        model_res_partner = self.env['ir.model']._get('res.partner')
        self.imap_server = self.env['fetchmail.server'].create({
            'name': 'Test IMAP',
            'server_type': 'imap',
            'server': 'imap.example.com',
            'port': 993,
            'is_ssl': True,
            'user': 'box@example.com',
            'password': 'x',
            'state': 'draft',
            'object_id': model_res_partner.id,
        })

    def test_fetch_mail_accepts_no_args(self):
        """AC-08-03 / DIFF-01 — signature compat with 19.0 core cron (_fetch_mails calls fetch_mail() with no arguments;
        18.0 required a `raise_exception` kwarg, 19.0 removed it again — see MF-01)."""
        result = self.env['fetchmail.server'].fetch_mail()
        self.assertTrue(result)

    def test_skip_email_from_internal_user(self):
        """AC-09-01 — email from an internal user is skipped, not routed to message_process."""
        conn = _mock_imap(['1'], {'1': _raw_email('internal@example.com')})
        with patch.object(type(self.imap_server), 'connect', return_value=conn), \
             patch.object(type(self.env['mail.thread']), 'message_process') as mock_process, \
             patch.object(self.env.cr, 'commit'):
            self.imap_server.fetch_mail()
        mock_process.assert_not_called()

    def test_skip_email_from_non_contact(self):
        """AC-09-02 — email from an address that is neither an internal user nor a known partner is skipped."""
        conn = _mock_imap(['1'], {'1': _raw_email('stranger@example.com')})
        with patch.object(type(self.imap_server), 'connect', return_value=conn), \
             patch.object(type(self.env['mail.thread']), 'message_process') as mock_process, \
             patch.object(self.env.cr, 'commit'):
            self.imap_server.fetch_mail()
        mock_process.assert_not_called()

    def test_process_email_from_known_contact(self):
        """AC-09-03 / AC-08-01 — email from a known partner IS routed to message_process."""
        conn = _mock_imap(['1'], {'1': _raw_email('known@example.com')})
        with patch.object(type(self.imap_server), 'connect', return_value=conn), \
             patch.object(type(self.env['mail.thread']), 'message_process', return_value=999) as mock_process, \
             patch.object(self.env.cr, 'commit'):
            self.imap_server.fetch_mail()
        mock_process.assert_called_once()
        self.assertEqual(mock_process.call_args[0][0], 'res.partner')

    def test_skipped_email_never_marked_processed_preserved_bug(self):
        """AC-11-01 [PRESERVE-BUG] BSL-020/MF-05 — skipped emails never enter processed_message_ids,
        so the same email is picked up again by the next (UNSEEN) search."""
        conn = _mock_imap(['1'], {'1': _raw_email('internal@example.com', message_id='<repeat@example.com>')})
        with patch.object(type(self.imap_server), 'connect', return_value=conn), \
             patch.object(type(self.env['mail.thread']), 'message_process') as mock_process, \
             patch.object(self.env.cr, 'commit'):
            self.imap_server.fetch_mail()
        self.assertFalse(self.imap_server.processed_message_ids)
        mock_process.assert_not_called()

    def test_processed_email_recorded_in_processed_ids(self):
        """Control case for AC-11-01 — a successfully processed email IS recorded (only the skip path leaks)."""
        conn = _mock_imap(['1'], {'1': _raw_email('known@example.com', message_id='<ok@example.com>')})
        with patch.object(type(self.imap_server), 'connect', return_value=conn), \
             patch.object(type(self.env['mail.thread']), 'message_process', return_value=999), \
             patch.object(self.env.cr, 'commit'):
            self.imap_server.fetch_mail()
        self.assertIn('<ok@example.com>', self.imap_server.processed_message_ids)

    def test_message_new_returns_existing_partner(self):
        """AC-10-01 — message_new() on res.partner returns the existing partner matched by email, not a new one."""
        partner_count_before = self.env['res.partner'].search_count([])
        result = self.env['res.partner'].message_new({'email_from': 'known@example.com'})
        self.assertEqual(result, self.known_partner)
        self.assertEqual(self.env['res.partner'].search_count([]), partner_count_before)

    def test_message_new_returns_false_for_unknown_sender(self):
        """AC-10-02 — message_new() on res.partner returns False (no new partner created) if sender is unknown."""
        partner_count_before = self.env['res.partner'].search_count([])
        outcome = self.env['res.partner'].message_new({'email_from': 'nobody@example.com'})
        self.assertFalse(outcome)
        self.assertEqual(self.env['res.partner'].search_count([]), partner_count_before)
