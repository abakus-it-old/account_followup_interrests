from openerp import models, fields, api
from datetime import datetime
import time
from openerp.tools.translate import _
import logging
_logger = logging.getLogger(__name__)
    
class account_followup(models.Model):
    _inherit = ['account_followup.followup']

    late_interest_percentage = fields.Integer(string="Late interest (%)")
    late_allowance = fields.Float(string="Late allowance")

class account_move_line(models.Model):
    _inherit = ['account.move.line']

    payments_interests = fields.Float(compute="_compute_payments_interests", string="Due interests")
    payments_allowances = fields.Float(compute="_compute_payments_allowances", string="Due allowances")

    @api.multi
    def _compute_payments_interests(self):
        followup = self.env['account_followup.followup'].search([['company_id', '=', self.env.user.company_id.id]])
        if len(followup) <= 0:
            return
        if len(followup) > 1:
            followup = followup[0]

        for line in self:
            if not line.full_reconcile_id and not line.blocked and line.date_maturity:
                balance = abs(line.debit - line.credit)
                d1 = datetime.strptime(line.date_maturity, '%Y-%m-%d')
                d2 = datetime.strptime(time.strftime('%Y-%m-%d'), '%Y-%m-%d')
                if d1 < d2:
                    daysDiff = float(str((d2-d1).days))
                    pc = float(followup.late_interest_percentage) / 100
                    pc_per_day = float(pc / 365)
                    interrests = float(balance * pc_per_day * daysDiff)
                    if interrests < 0:
                        interrests = interrests * (-1)
                    line.payments_interests = interrests

    @api.multi
    def _compute_payments_allowances(self):
        followup = self.env['account_followup.followup'].search([['company_id', '=', self.env.user.company_id.id]])
        if len(followup) <= 0:
            return
        if len(followup) > 1:
            followup = followup[0]

        for line in self:
            if not line.full_reconcile_id and not line.blocked:
                d1 = datetime.strptime(line.date_maturity, '%Y-%m-%d')
                d2 = datetime.strptime(time.strftime('%Y-%m-%d'), '%Y-%m-%d')
                if d1 < d2:
                    balance = line.debit - line.credit
                    line.payments_allowances = followup.late_allowance

class partnerWithInterest(models.Model):
    _inherit = ['res.partner']

    payments_sum_of_interests = fields.Float(compute="_compute_payments_sum_of_interests", string="Sum of due interests")
    payments_sum_of_allowances = fields.Float(compute="_compute_payments_sum_of_allowances", string="Sum of due allowances")
    payments_sum_due = fields.Float(compute="_compute_payments_sum_due", string="Total amount due")

    @api.multi
    def _compute_payments_sum_of_interests(self):
        for partner in self:
            if len(partner.unreconciled_aml_ids) > 0:
                interests = 0
                for line in partner.unreconciled_aml_ids:
                    interests = interests + line.payments_interests
                partner.payments_sum_of_interests = interests

    @api.multi
    def _compute_payments_sum_of_allowances(self):
        for partner in self:
            if len(partner.unreconciled_aml_ids) > 0:
                allowances = 0
                for line in self.unreconciled_aml_ids:
                    allowances = allowances + line.payments_allowances
                partner.payments_sum_of_allowances = allowances

    @api.multi
    def _compute_payments_sum_due(self):
        for partner in self:
            partner.payments_sum_due = partner.payment_amount_due + partner.payments_sum_of_interests + partner.payments_sum_of_allowances
