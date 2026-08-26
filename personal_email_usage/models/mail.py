from odoo import fields, models, api, tools, _
from odoo.exceptions import UserError
from odoo.exceptions import ValidationError
import requests
import urllib.parse
import logging
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta
from odoo.fields import Datetime
import re
from odoo.osv import expression
import traceback
from markupsafe import Markup
import email

_logger = logging.getLogger(__name__)


class MailThread(models.AbstractModel):
    _inherit = 'mail.thread'

    @api.model
    def message_new(self, msg_dict, custom_values=None):
        """Override to check for existing contact before creating new record"""
        if self._name == 'res.partner':
            email_from = msg_dict.get('email_from')
            original_email_from = email_from  # Store original email_from
            extracted_email = tools.email_split(email_from)[0] if tools.email_split(email_from) else False

            if extracted_email:
                # Check for existing partner
                existing_partner = self.env['res.partner'].search([
                    ('email', '=ilike', extracted_email)
                ], limit=1)

                if existing_partner:
                    _logger.info('Found existing partner: %s', existing_partner.name)
                    return existing_partner
                else:
                    _logger.info('No existing partner found for email: %s. Skipping creation.', extracted_email)
                    return False

        return super().message_new(msg_dict, custom_values=custom_values)


class FetchmailServer(models.Model):
    """Incoming IMAP mail server account"""

    _inherit = 'fetchmail.server'
    _description = 'Incoming Mail Server'

    processed_message_ids = fields.Text(string='Processed Message IDs',
                                        help='Store processed message IDs to prevent duplicates')

    mark_read = fields.Boolean(
        string='Mark Emails as Read',
        default=False,
        help='If checked, fetched emails will be marked as read in the email server'
    )

    def fetch_mail(self):
        """Override fetch_mail to add message ID tracking and contact filtering. No `raise_exception` param since 19.0 core cron calls fetch_mail() with no arguments (18.0 required it, 19.0 removed it again)."""
        for server in self.filtered(lambda s: s.server_type == 'imap'):
            processed_ids = set(filter(None, (server.processed_message_ids or '').split(',')))
            count, failed, skipped = 0, 0, 0
            imap_server = None

            try:
                imap_server = server.connect()
                imap_server.select()
                result, data = imap_server.search(None, '(UNSEEN)')

                for num in data[0].split():
                    result, data = imap_server.fetch(num, '(RFC822)')
                    imap_server.store(num, '-FLAGS', '\\Seen')
                    if server.mark_read:
                        imap_server.store(num, '+FLAGS', '\\Seen')
                    email_message = email.message_from_bytes(data[0][1])
                    from_email = email.utils.parseaddr(email_message.get('from'))[1]
                    message_id = email_message.get('Message-ID', '')

                    # Skip if already processed
                    if message_id in processed_ids:
                        _logger.info('Skipping already processed message: %s', message_id)
                        continue

                    # Check if sender is a user
                    user = self.env['res.users'].search([
                        ('login', '=ilike', from_email),
                        ('share', '=', False),
                    ], limit=1)

                    if user:
                        skipped += 1
                        _logger.info('Skipped email from user: %s', from_email)
                        continue

                    elif not user:
                        # Check if sender exists in contacts
                        partner = self.env['res.partner'].search([
                            ('email', '=ilike', from_email),
                        ], limit=1)

                        if not partner:
                            skipped += 1
                            _logger.info('Skipped email from non-contact: %s', from_email)
                            continue

                    try:
                        res_id = self.env['mail.thread'].with_context(
                            fetchmail_cron_running=True,
                            default_fetchmail_server_id=server.id
                        ).message_process(
                            server.object_id.model,
                            data[0][1],
                            save_original=server.original,
                            strip_attachments=(not server.attach)
                        )

                        if res_id:
                            processed_ids.add(message_id)
                            count += 1
                        else:
                            failed += 1

                    except Exception:
                        _logger.info('Failed to process mail from %s server %s.',
                                     server.server_type, server.name, exc_info=True)
                        failed += 1

                    self._cr.commit()

                # Update processed message IDs
                server.write({
                    'processed_message_ids': ','.join(processed_ids)
                })

                _logger.info(
                    "Fetched %d email(s) on %s server %s; %d succeeded, %d failed, %d skipped.",
                    count, server.server_type, server.name, (count - failed), failed, skipped
                )

            except Exception:
                _logger.info("General failure when trying to fetch mail from %s server %s.",
                             server.server_type, server.name, exc_info=True)
            finally:
                if imap_server:
                    try:
                        imap_server.close()
                        imap_server.logout()
                    except Exception:
                        _logger.warning('Failed to properly finish imap connection: %s.',
                                        server.name, exc_info=True)

        # Process remaining servers (non-IMAP) using original method
        return super(FetchmailServer, self.filtered(lambda s: s.server_type != 'imap')).fetch_mail()
