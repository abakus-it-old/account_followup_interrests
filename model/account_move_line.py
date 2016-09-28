from openerp import models, fields, api
from datetime import datetime
import time
from openerp.tools.translate import _
import logging
_logger = logging.getLogger(__name__)

class account_move_line(models.Model):
    _inherit = ['account.move.line']

    payments_interests = fields.Float(compute="_compute_payments_interests", string="Due interests")
    payments_allowances = fields.Float(compute="_compute_payments_allowances", string="Due allowances")
    late_days = fields.Integer(compute="_compute_late_days", string="Late Days")

    @api.multi
    def _compute_late_days(self):
        for line in self:
            d1 = datetime.strptime(line.date_maturity, '%Y-%m-%d')
            d2 = datetime.strptime(time.strftime('%Y-%m-%d'), '%Y-%m-%d')
            daysDiff = float(str((d2-d1).days))
            line.late_days = daysDiff

    @api.multi
    def _compute_payments_interests(self):
        followup = self.env['account_followup.followup'].search([['company_id', '=', self.env.user.company_id.id]])
        if len(followup) <= 0:
            return
        if len(followup) > 1:
            followup = followup[0]

        for line in self:
            # check if date exceeded and we have to compute interests
            check = False
            for f_line in followup.followup_line_ids:
                if f_line.delay < line.late_days and f_line.compute_interests:
                    check = True
            if check and not line.full_reconcile_id and not line.blocked and line.date_maturity:
                balance = abs(line.debit - line.credit)
                if line.late_days > 0:
                    pc = float(followup.late_interest_percentage) / 100
                    pc_per_day = float(pc / 365)
                    interrests = float(balance * pc_per_day * line.late_days)
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
            # check if date exceeded and we have to compute interests
            check = False
            for f_line in followup.followup_line_ids:
                if f_line.delay < line.late_days and f_line.compute_allowance:
                    check = True
            if check and not line.full_reconcile_id and not line.blocked:
                if line.late_days > 0:
                    balance = line.debit - line.credit
                    line.payments_allowances = followup.late_allowance