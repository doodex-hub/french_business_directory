# -*- coding: utf-8 -*-
from unittest.mock import patch

from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestMessageNewOverride(TransactionCase):
    """AC-06 — mail.thread.message_new() override on res.partner."""

    def test_message_new_returns_existing_partner_for_known_sender(self):
        partner = self.env['res.partner'].create({'name': 'Known Contact', 'email': 'known@example.com'})
        result = self.env['res.partner'].message_new({'email_from': 'Known Contact <known@example.com>'})
        self.assertEqual(result.id, partner.id)

    def test_message_new_returns_false_for_unknown_sender(self):
        result = self.env['res.partner'].message_new({'email_from': 'nobody@example.com'})
        self.assertFalse(result)

    def test_message_new_delegates_to_super_for_non_partner_models(self):
        """For any mail.thread model other than res.partner, the res.partner-specific
        short-circuit must not run at all — verified by asserting res.partner.search is
        never called when message_new is invoked on the abstract mail.thread model
        itself (self._name == 'mail.thread' != 'res.partner').

        Calling message_new() on the ABSTRACT mail.thread model makes core's default
        implementation try to self.create() on a model with no table at all, which fails
        at the SQL level (confirmed via a real Step 04 Docker run:
        'relation "mail_thread" does not exist') -- a plain try/except catches the Python
        exception but NOT the resulting aborted Postgres transaction, which then breaks
        every subsequent test. self.cr.savepoint() is Odoo's own primitive for containing
        exactly this kind of DB-level failure without poisoning the outer test transaction.
        """
        with patch.object(type(self.env['res.partner']), 'search') as mock_search:
            try:
                with self.env.cr.savepoint():
                    self.env['mail.thread'].message_new({'email_from': 'someone@example.com'})
            except Exception:
                pass

        mock_search.assert_not_called()
