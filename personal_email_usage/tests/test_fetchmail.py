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
        """AC-08-03 / MF-03 — signature/entry-point compat with 19.0 core cron, which calls
        `_fetch_mail(batch_limit=...)` directly (not `fetch_mail()` — see MF-03). Our override moved
        from `fetch_mail()` to `_fetch_mail()` accordingly. `_fetch_mail()` returns `None` on success
        (an `Exception` instance on failure), unlike 18.0's `fetch_mail()` which always returned `True`.

        Core `_fetch_mail()` calls `ir.cron._commit_progress()` unconditionally (even for an empty
        recordset, before iterating any server) which does `self.env.cr.commit()` — forbidden inside
        a TransactionCase test. This is a real commit in production cron usage (expected), only
        needs mocking here because we're calling `_fetch_mail()` directly instead of via the cron."""
        with patch.object(self.env.cr, 'commit'):
            result = self.env['fetchmail.server']._fetch_mail()
        self.assertIsNone(result)

    def test_skip_email_from_internal_user(self):
        """AC-09-01 — email from an internal user is skipped, not routed to message_process."""
        conn = _mock_imap(['1'], {'1': _raw_email('internal@example.com')})
        with patch.object(type(self.imap_server), '_connect__', return_value=conn), \
             patch.object(type(self.env['mail.thread']), 'message_process') as mock_process, \
             patch.object(self.env.cr, 'commit'):
            self.imap_server.fetch_mail()
        mock_process.assert_not_called()

    def test_skip_email_from_non_contact(self):
        """AC-09-02 — email from an address that is neither an internal user nor a known partner is skipped."""
        conn = _mock_imap(['1'], {'1': _raw_email('stranger@example.com')})
        with patch.object(type(self.imap_server), '_connect__', return_value=conn), \
             patch.object(type(self.env['mail.thread']), 'message_process') as mock_process, \
             patch.object(self.env.cr, 'commit'):
            self.imap_server.fetch_mail()
        mock_process.assert_not_called()

    def test_process_email_from_known_contact(self):
        """AC-09-03 / AC-08-01 — email from a known partner IS routed to message_process."""
        conn = _mock_imap(['1'], {'1': _raw_email('known@example.com')})
        with patch.object(type(self.imap_server), '_connect__', return_value=conn), \
             patch.object(type(self.env['mail.thread']), 'message_process', return_value=999) as mock_process, \
             patch.object(self.env.cr, 'commit'):
            self.imap_server.fetch_mail()
        mock_process.assert_called_once()
        self.assertEqual(mock_process.call_args[0][0], 'res.partner')

    def test_skipped_email_never_marked_processed_preserved_bug(self):
        """AC-11-01 [PRESERVE-BUG] BSL-020/MF-05 — skipped emails never enter processed_message_ids,
        so the same email is picked up again by the next (UNSEEN) search."""
        conn = _mock_imap(['1'], {'1': _raw_email('internal@example.com', message_id='<repeat@example.com>')})
        with patch.object(type(self.imap_server), '_connect__', return_value=conn), \
             patch.object(type(self.env['mail.thread']), 'message_process') as mock_process, \
             patch.object(self.env.cr, 'commit'):
            self.imap_server.fetch_mail()
        self.assertFalse(self.imap_server.processed_message_ids)
        mock_process.assert_not_called()

    def test_processed_email_recorded_in_processed_ids(self):
        """Control case for AC-11-01 — a successfully processed email IS recorded (only the skip path leaks)."""
        conn = _mock_imap(['1'], {'1': _raw_email('known@example.com', message_id='<ok@example.com>')})
        with patch.object(type(self.imap_server), '_connect__', return_value=conn), \
             patch.object(type(self.env['mail.thread']), 'message_process', return_value=999), \
             patch.object(self.env.cr, 'commit'):
            self.imap_server.fetch_mail()
        self.assertIn('<ok@example.com>', self.imap_server.processed_message_ids)

    def test_mark_read_true_reapplies_seen_flag(self):
        """AC-03-01 [TC-FLAG-01] BSL-020 — mark_read=True re-applies \\Seen after fetch."""
        server_mr_true = self.env['fetchmail.server'].create({
            'name': 'Test IMAP mark_read=True',
            'server_type': 'imap',
            'server': 'imap.example.com',
            'port': 993,
            'is_ssl': True,
            'user': 'box2@example.com',
            'password': 'x',
            'state': 'draft',
            'object_id': self.imap_server.object_id.id,
            'mark_read': True,
        })
        conn = _mock_imap(['1'], {'1': _raw_email('known@example.com', message_id='<mr-true@example.com>')})
        with patch.object(type(server_mr_true), '_connect__', return_value=conn), \
             patch.object(type(self.env['mail.thread']), 'message_process', return_value=999), \
             patch.object(self.env.cr, 'commit'):
            server_mr_true.fetch_mail()
        seen_calls = [c for c in conn.store.call_args_list if c.args[1:] == ('+FLAGS', '\\Seen')]
        self.assertTrue(seen_calls, "mark_read=True should re-apply \\Seen after fetch")

    def test_mark_read_false_does_not_reapply_seen_flag(self):
        """AC-03-02 [TC-FLAG-01] BSL-020 — mark_read=False (default) leaves the message Unseen."""
        conn = _mock_imap(['1'], {'1': _raw_email('known@example.com', message_id='<mr-false@example.com>')})
        with patch.object(type(self.imap_server), '_connect__', return_value=conn), \
             patch.object(type(self.env['mail.thread']), 'message_process', return_value=999), \
             patch.object(self.env.cr, 'commit'):
            self.imap_server.fetch_mail()
        seen_calls = [c for c in conn.store.call_args_list if c.args[1:] == ('+FLAGS', '\\Seen')]
        self.assertFalse(seen_calls, "mark_read=False (default) should leave the message Unseen")
        unseen_calls = [c for c in conn.store.call_args_list if c.args[1:] == ('-FLAGS', '\\Seen')]
        self.assertTrue(unseen_calls, "the -FLAGS \\Seen call should always happen right after fetch")

    def test_duplicate_message_id_skipped_on_repeat_fetch(self):
        """S-10 (05_EMAIL_GAPS.md, project 17→18) — a message-id already in processed_message_ids is
        skipped on a later fetch, not reprocessed, even if it still shows up in the UNSEEN search
        (mark_read=False leaves it unread so a later cron run would otherwise see it again)."""
        conn1 = _mock_imap(['1'], {'1': _raw_email('known@example.com', message_id='<dup@example.com>')})
        with patch.object(type(self.imap_server), '_connect__', return_value=conn1), \
             patch.object(type(self.env['mail.thread']), 'message_process', return_value=999) as mock_process, \
             patch.object(self.env.cr, 'commit'):
            self.imap_server.fetch_mail()
        self.assertEqual(mock_process.call_count, 1)
        self.assertIn('<dup@example.com>', self.imap_server.processed_message_ids)

        conn2 = _mock_imap(['1'], {'1': _raw_email('known@example.com', message_id='<dup@example.com>')})
        with patch.object(type(self.imap_server), '_connect__', return_value=conn2), \
             patch.object(type(self.env['mail.thread']), 'message_process', return_value=999) as mock_process2, \
             patch.object(self.env.cr, 'commit'):
            self.imap_server.fetch_mail()
        mock_process2.assert_not_called()

    def test_message_process_exception_does_not_abort_batch(self):
        """S-11 (05_EMAIL_GAPS.md, project 17→18) — one email raising in message_process() doesn't stop
        the batch; the next email in the same fetch is still processed, and the failing message-id is
        NOT recorded as processed (so it will be retried on the next cron run)."""
        conn = _mock_imap(['1', '2'], {
            '1': _raw_email('known@example.com', message_id='<fail@example.com>'),
            '2': _raw_email('known@example.com', message_id='<ok@example.com>'),
        })
        with patch.object(type(self.imap_server), '_connect__', return_value=conn), \
             patch.object(type(self.env['mail.thread']), 'message_process', side_effect=[Exception('boom'), 999]) as mock_process, \
             patch.object(self.env.cr, 'commit'):
            self.imap_server.fetch_mail()
        self.assertEqual(mock_process.call_count, 2)
        self.assertNotIn('<fail@example.com>', self.imap_server.processed_message_ids)
        self.assertIn('<ok@example.com>', self.imap_server.processed_message_ids)

    def test_one_server_connect_failure_does_not_block_other_servers(self):
        """S-12 (05_EMAIL_GAPS.md, project 17→18) — a _connect__() failure on one IMAP server doesn't
        stop other IMAP servers in the same batch (the loop is per-server, wrapped in its own
        try/except). Calls _fetch_mail() directly (not fetch_mail()) — fetch_mail() is 19.0 core's
        public wrapper and requires ensure_one(), so it cannot run on a 2-record recordset; see MF-03."""
        server_b = self.env['fetchmail.server'].create({
            'name': 'Test IMAP B',
            'server_type': 'imap',
            'server': 'imap2.example.com',
            'port': 993,
            'is_ssl': True,
            'user': 'box3@example.com',
            'password': 'x',
            'state': 'draft',
            'object_id': self.imap_server.object_id.id,
        })
        conn_b = _mock_imap(['1'], {'1': _raw_email('known@example.com', message_id='<serverb@example.com>')})
        with patch.object(type(self.imap_server), '_connect__', side_effect=[Exception('auth failed'), conn_b]), \
             patch.object(type(self.env['mail.thread']), 'message_process', return_value=999) as mock_process, \
             patch.object(self.env.cr, 'commit'):
            (self.imap_server + server_b)._fetch_mail()
        mock_process.assert_called_once()

    def test_attach_and_original_flags_forwarded_to_message_process(self):
        """S-14 (05_EMAIL_GAPS.md, project 17→18) — server.attach controls strip_attachments passed to
        message_process (strip_attachments = not server.attach)."""
        self.imap_server.attach = False
        conn = _mock_imap(['1'], {'1': _raw_email('known@example.com', message_id='<flags1@example.com>')})
        with patch.object(type(self.imap_server), '_connect__', return_value=conn), \
             patch.object(type(self.env['mail.thread']), 'message_process', return_value=999) as mock_process, \
             patch.object(self.env.cr, 'commit'):
            self.imap_server.fetch_mail()
        self.assertTrue(mock_process.call_args.kwargs['strip_attachments'])

        self.imap_server.attach = True
        conn2 = _mock_imap(['1'], {'1': _raw_email('known@example.com', message_id='<flags2@example.com>')})
        with patch.object(type(self.imap_server), '_connect__', return_value=conn2), \
             patch.object(type(self.env['mail.thread']), 'message_process', return_value=999) as mock_process2, \
             patch.object(self.env.cr, 'commit'):
            self.imap_server.fetch_mail()
        self.assertFalse(mock_process2.call_args.kwargs['strip_attachments'])

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
