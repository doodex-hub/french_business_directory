# -*- coding: utf-8 -*-
import email.message
from unittest.mock import MagicMock, patch

from odoo.tests.common import TransactionCase, tagged


def _raw_email(from_addr, message_id, subject='Test', to_addr='support@example.com', body='Hello'):
    msg = email.message.EmailMessage()
    msg['From'] = from_addr
    msg['To'] = to_addr
    msg['Subject'] = subject
    msg['Message-ID'] = message_id
    msg.set_content(body)
    return msg.as_bytes()


def _make_imap_mock(messages):
    """messages: dict of {b'<num>': raw_bytes}. Simulates enough of imaplib's IMAP4 API
    surface for FetchmailServer.fetch_mail() (select/search/fetch/store/close/logout)."""
    mock = MagicMock(name='imap_connection')
    mock.select.return_value = ('OK', [b'1'])
    nums = b' '.join(sorted(messages.keys())) if messages else b''
    mock.search.return_value = ('OK', [nums])

    def _fetch(num, parts):
        return ('OK', [(b'FETCH_LITERAL', messages[num])])

    mock.fetch.side_effect = _fetch
    return mock


@tagged('post_install', '-at_install')
class TestFetchmailServerBase(TransactionCase):

    def setUp(self):
        super().setUp()
        self.partner_model = self.env['ir.model'].search([('model', '=', 'res.partner')], limit=1)
        # fetch_mail() calls self._cr.commit() for every message that isn't skipped
        # (matches Odoo core's own fetch_mail(), which commits per-message too -- see
        # mail/models/fetchmail.py) -- a REAL commit inside Odoo's TransactionCase
        # destroys the test framework's own SAVEPOINT, breaking test isolation for every
        # test that runs after it (confirmed via a real Step 04 Docker run: the first test
        # exercising this path corrupted the DB transaction for the whole test class).
        # No-op the commit for the duration of the test -- a test-only stub, not a change
        # to business code (see CLAUDE_TEMPLATE.md "Boleh: setup/stub ringan di level test").
        commit_patcher = patch.object(self.cr, 'commit')
        commit_patcher.start()
        self.addCleanup(commit_patcher.stop)

    def _make_server(self, mark_read=False, processed_message_ids=''):
        return self.env['fetchmail.server'].create({
            'name': 'Test IMAP Server',
            'server_type': 'imap',
            'server': 'imap.example.com',
            'object_id': self.partner_model.id,
            'mark_read': mark_read,
            'processed_message_ids': processed_message_ids,
        })


class TestFetchmailServerNonImapPassthrough(TestFetchmailServerBase):
    """AC-02-01: server_type != 'imap' must never touch the custom skip logic."""

    def test_pop_server_never_calls_custom_skip_logic(self):
        server = self.env['fetchmail.server'].create({
            'name': 'Test POP Server',
            'server_type': 'pop',
            'server': 'pop.example.com',
        })
        imap_mock = _make_imap_mock({})
        with patch.object(type(self.env['fetchmail.server']), 'connect', return_value=imap_mock), \
             patch.object(type(self.env['res.users']), 'search') as mock_users_search, \
             patch.object(type(self.env['res.partner']), 'search') as mock_partner_search:
            server.fetch_mail()

        mock_users_search.assert_not_called()
        mock_partner_search.assert_not_called()


class TestFetchmailServerFlagHandling(TestFetchmailServerBase):
    """AC-03 — \\Seen flag sequencing vs mark_read."""

    def test_mark_read_true_reapplies_seen_flag(self):
        partner = self.env['res.partner'].create({'name': 'Known Contact', 'email': 'known@example.com'})
        raw = _raw_email('known@example.com', '<msg-mr-true@test>')
        imap_mock = _make_imap_mock({b'1': raw})
        server = self._make_server(mark_read=True)

        with patch.object(type(self.env['fetchmail.server']), 'connect', return_value=imap_mock):
            server.fetch_mail()

        seen_calls = [c for c in imap_mock.store.call_args_list if c.args[1:] == ('+FLAGS', '\\Seen')]
        self.assertTrue(seen_calls, "mark_read=True should re-apply \\Seen after fetch")

    def test_mark_read_false_does_not_reapply_seen_flag(self):
        partner = self.env['res.partner'].create({'name': 'Known Contact', 'email': 'known2@example.com'})
        raw = _raw_email('known2@example.com', '<msg-mr-false@test>')
        imap_mock = _make_imap_mock({b'1': raw})
        server = self._make_server(mark_read=False)

        with patch.object(type(self.env['fetchmail.server']), 'connect', return_value=imap_mock):
            server.fetch_mail()

        seen_calls = [c for c in imap_mock.store.call_args_list if c.args[1:] == ('+FLAGS', '\\Seen')]
        self.assertFalse(seen_calls, "mark_read=False (default) should leave the message Unseen")
        unseen_calls = [c for c in imap_mock.store.call_args_list if c.args[1:] == ('-FLAGS', '\\Seen')]
        self.assertTrue(unseen_calls, "the -FLAGS \\Seen call should always happen right after fetch")


class TestFetchmailServerSkipLogic(TestFetchmailServerBase):
    """AC-04, AC-05, F-07 — skip filters and the resulting dedup gap."""

    def test_skip_email_from_internal_user_not_marked_processed_F07(self):
        self.env['res.users'].create({
            'name': 'Internal Staff', 'login': 'staff@example.com', 'email': 'staff@example.com',
        })
        raw = _raw_email('staff@example.com', '<msg-internal@test>')
        imap_mock = _make_imap_mock({b'1': raw})
        server = self._make_server(mark_read=False)

        with patch.object(type(self.env['fetchmail.server']), 'connect', return_value=imap_mock):
            server.fetch_mail()

        self.assertNotIn('<msg-internal@test>', server.processed_message_ids or '',
                          "F-07: skipped (internal-user) emails are never recorded as processed")

    def test_skip_email_from_non_contact_not_marked_processed_F07(self):
        raw = _raw_email('stranger@example.com', '<msg-stranger@test>')
        imap_mock = _make_imap_mock({b'1': raw})
        server = self._make_server(mark_read=False)

        with patch.object(type(self.env['fetchmail.server']), 'connect', return_value=imap_mock):
            server.fetch_mail()

        self.assertNotIn('<msg-stranger@test>', server.processed_message_ids or '',
                          "F-07: skipped (non-contact) emails are never recorded as processed")

    def test_known_contact_email_is_recorded_as_processed(self):
        self.env['res.partner'].create({'name': 'Known Contact', 'email': 'contact@example.com'})
        raw = _raw_email('contact@example.com', '<msg-contact@test>')
        imap_mock = _make_imap_mock({b'1': raw})
        server = self._make_server(mark_read=False)

        with patch.object(type(self.env['fetchmail.server']), 'connect', return_value=imap_mock):
            server.fetch_mail()

        self.assertIn('<msg-contact@test>', server.processed_message_ids or '')

    def test_already_processed_message_is_not_reprocessed(self):
        self.env['res.partner'].create({'name': 'Known Contact', 'email': 'contact2@example.com'})
        raw = _raw_email('contact2@example.com', '<msg-dup@test>')
        imap_mock = _make_imap_mock({b'1': raw})
        server = self._make_server(mark_read=False, processed_message_ids='<msg-dup@test>')

        with patch.object(type(self.env['fetchmail.server']), 'connect', return_value=imap_mock), \
             patch.object(type(self.env['mail.thread']), 'message_process') as mock_process:
            server.fetch_mail()

        mock_process.assert_not_called()


class TestFetchmailServerLogging(TestFetchmailServerBase):
    """F-08 — the 'succeeded' count in the summary log is wrong."""

    def test_succeeded_count_in_log_is_wrong_F08(self):
        """Mocks the module's _logger directly (instead of assertLogs) so the assertion
        doesn't depend on Odoo's ambient logger-level/propagation configuration -- only on
        the actual arguments passed to _logger.info()."""
        self.env['res.partner'].create({'name': 'Known Contact', 'email': 'ok@example.com'})
        raw_ok = _raw_email('ok@example.com', '<msg-ok@test>')
        raw_fail = _raw_email('ok@example.com', '<msg-fail@test>')
        imap_mock = _make_imap_mock({b'1': raw_ok, b'2': raw_fail})
        server = self._make_server(mark_read=False)

        with patch.object(type(self.env['fetchmail.server']), 'connect', return_value=imap_mock), \
             patch.object(type(self.env['mail.thread']), 'message_process',
                           side_effect=[42, Exception('simulated failure')]), \
             patch('odoo.addons.personal_email_usage.models.mail._logger') as mock_logger:
            server.fetch_mail()

        summary_calls = [c for c in mock_logger.info.call_args_list if 'succeeded' in c.args[0]]
        self.assertTrue(summary_calls, "expected a summary log call")
        # args: (fmt, count, server_type, name, (count - failed), failed, skipped)
        # count=1 (only the successful message increments it), failed=1 -> buggy formula
        # logs (count - failed) = 0 "succeeded", even though 1 message actually succeeded.
        logged_succeeded = summary_calls[0].args[4]
        self.assertEqual(logged_succeeded, 0,
                          "F-08: log currently reports (count - failed) = 0 instead of the "
                          "real count = 1; update this assertion once F-08 is fixed")
