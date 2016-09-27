# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from openerp import models, fields, api, tools
from datetime import datetime
from hashlib import md5
from openerp.tools.misc import formatLang
from openerp.tools.translate import _
import time
from openerp.tools.safe_eval import safe_eval
from openerp.tools import append_content_to_html, DEFAULT_SERVER_DATE_FORMAT
import math
import logging
_logger = logging.getLogger(__name__)


class report_account_followup_report(models.AbstractModel):
    _inherit = "account.followup.report"

    @api.model
    def get_lines(self, context_id, line_id=None, public=False):
        # Get date format for the lang
        lang_code = context_id.partner_id.lang or self.env.user.lang or 'en_US'
        lang_ids = self.env['res.lang'].search([('code', '=', lang_code)], limit=1)
        date_format = lang_ids.date_format or DEFAULT_SERVER_DATE_FORMAT

        def formatLangDate(date):
            date_dt = datetime.strptime(date, DEFAULT_SERVER_DATE_FORMAT)
            return date_dt.strftime(date_format)

        lines = []
        res = {}
        today = datetime.today().strftime('%Y-%m-%d')
        line_num = 0
        for l in context_id.partner_id.unreconciled_aml_ids:
            if public and l.blocked:
                continue
            currency = l.currency_id or l.company_id.currency_id
            if currency not in res:
                res[currency] = []
            res[currency].append(l)
        for currency, aml_recs in res.items():
            total = 0
            total_issued = 0
            total_interest = 0
            total_allowance = 0
            total_all = 0
            aml_recs = sorted(aml_recs, key=lambda aml: aml.blocked)
            for aml in aml_recs:
                amount = aml.currency_id and aml.amount_residual_currency or aml.amount_residual
                date_due = formatLangDate(aml.date_maturity or aml.date)
                total += not aml.blocked and amount or 0
                total_interest += not aml.blocked and aml.payments_interests or 0
                total_allowance += not aml.blocked and aml.payments_allowances or 0
                is_overdue = today > aml.date_maturity if aml.date_maturity else today > aml.date
                is_payment = aml.payment_id
                if is_overdue or is_payment:
                    total_issued += not aml.blocked and amount or 0
                if is_overdue:
                    date_due = (date_due, 'color: red;')
                if is_payment:
                    date_due = ''
                late_days = aml.late_days > 0 and aml.late_days or 0
                allowances = formatLang(self.env, aml.payments_allowances, currency_obj=currency)
                interests = formatLang(self.env, aml.payments_interests, currency_obj=currency)
                total_due = formatLang(self.env, float(amount + aml.payments_interests + aml.payments_allowances), currency_obj=currency)
                amount = formatLang(self.env, amount, currency_obj=currency)
                
                line_num += 1
                lines.append({
                    'id': aml.id,
                    'name': aml.move_id.name,
                    'action': aml.get_model_id_and_name(),
                    'move_id': aml.move_id.id,
                    'type': is_payment and 'payment' or 'unreconciled_aml',
                    'footnotes': {},
                    'unfoldable': False,
                    'columns': [formatLangDate(aml.date), date_due, late_days] + (not public and [aml.expected_pay_date and (aml.expected_pay_date, aml.internal_note) or ('', ''), aml.blocked] or []) + [amount, interests, allowances, total_due],
                    'blocked': aml.blocked,
                })
            total_all = total + total_interest + total_allowance
            if total_issued > 0:
                total_issued = formatLang(self.env, total_issued, currency_obj=currency)
                line_num += 1
                lines.append({
                    'id': line_num,
                    'name': '',
                    'type': 'total',
                    'footnotes': {},
                    'unfoldable': False,
                    'level': 0,
                    'columns': (not public and ['', ''] or []) + ['', '', '', '', '', _('Total Overdue')] + [total_issued],
                })
            total = formatLang(self.env, total, currency_obj=currency)
            line_num += 1
            lines.append({
                'id': line_num,
                'name': '',
                'type': 'total',
                'footnotes': {},
                'unfoldable': False,
                'level': 0,
                'columns': (not public and ['', ''] or []) + ['', '', '', '', '', total >= 0 and _('Total Due') or ''] + [total],
            })
            if total_interest > 0:
                total_interest = formatLang(self.env, total_interest, currency_obj=currency)
                line_num += 1
                lines.append({
                    'id': line_num,
                    'name': '',
                    'type': 'total',
                    'footnotes': {},
                    'unfoldable': False,
                    'level': 0,
                    'columns': (not public and ['', ''] or []) + ['', '', '', '', '', _('Interests Total')] + [total_interest],
                })
            if total_allowance > 0:
                total_allowance = formatLang(self.env, total_allowance, currency_obj=currency)
                line_num += 1
                lines.append({
                    'id': line_num,
                    'name': '',
                    'type': 'total',
                    'footnotes': {},
                    'unfoldable': False,
                    'level': 0,
                    'columns': (not public and ['', ''] or []) + ['', '', '', '', '', _('Allowance Total')] + [total_allowance],
                })
            total_all = formatLang(self.env, total_all, currency_obj=currency)
            line_num += 1
            lines.append({
                'id': line_num,
                'name': '',
                'type': 'total',
                'footnotes': {},
                'unfoldable': False,
                'level': 0,
                'columns': (not public and ['', ''] or []) + ['', '', '', '', '', total >= 0 and _('Total') or ''] + [total_all],
            })
        return lines

class account_report_context_followup(models.TransientModel):
    _inherit = "account.report.context.followup"

    def get_columns_names(self):
        if self.env.context.get('public'):
            return [_(' Date '), _(' Due Date '), _('Overdue days'), _('Amount'), _('Allowances'), _('Interests'), _(' Total Due ')]
        return [_(' Date '), _(' Due Date '), _('Overdue days'), _(' Expected Date '), _(' Excluded '), _('Amount'), _('Allowance'), _('Interests'), _(' Total Due ')]

    @api.multi
    def get_columns_types(self):
        if self.env.context.get('public'):
            return ['date', 'date', 'number', 'number', 'number', 'number', 'text', 'number']
        return ['date', 'date', 'number', 'date', 'checkbox', 'number', 'number', 'number', 'number']
