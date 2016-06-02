from openerp import models, fields, api
import datetime
from datetime import date
import time
import logging
_logger = logging.getLogger(__name__)
    
class account_followup(models.Model):
    _inherit = ['account_followup.followup']

    monthly_late_interest_percentage = fields.Integer(string="Monthly late interest (%)")
    late_allowance_percentage = fields.Integer(string="Late allowance (%)")
    late_allowance_minimum = fields.Float(string="Late allowance minimum (euro)")

class account_move_line(models.Model):
    _inherit = ['account.move.line']

    payments_interests = fields.Float(compute="_compute_payments_interests", string="Due interests")
    payments_allowances = fields.Float(compute="_compute_payments_allowances", string="Due allowances")

    @api.one
    def _compute_payments_interests(self):
        if not self.blocked:
            balance = self.debit - self.credit
            cr = self.env.cr
            uid = self.env.uid
            context = self.env.context
            followups_obj = self.pool.get('account_followup.followup')
            followup_ids = followups_obj.search(cr, uid, [('company_id', '=', self.env.user.company_id.id)])
            if len(followup_ids) > 0:

                d2 = datetime.datetime.strptime(self.date_maturity,'%Y-%m-%d')
                d1 = datetime.date.today()
                nb_months = (d1.year - d2.year) * 12 + d1.month - d2.month
                if nb_months < 0:
                    nb_months = nb_months * (-1)
                
                followup = followups_obj.browse(cr, uid, followup_ids[0])
                self.payments_interests = nb_months * (balance * followup.monthly_late_interest_percentage) / 100

    @api.one
    def _compute_payments_allowances(self):
        if not self.blocked:
            balance = self.debit - self.credit
            cr = self.env.cr
            uid = self.env.uid
            context = self.env.context
            followups_obj = self.pool.get('account_followup.followup')
            followup_ids = followups_obj.search(cr, uid, [('company_id', '=', self.env.user.company_id.id)])
            if len(followup_ids) > 0:
                followup = followups_obj.browse(cr, uid, followup_ids[0])
            self.payments_allowances = (balance * followup.late_allowance_percentage) / 100
            if self.payments_allowances < followup.late_allowance_minimum:
                self.payments_allowances = followup.late_allowance_minimum

class partnerWithInterest(models.Model):
    _inherit = ['res.partner']

    payments_sum_of_interests = fields.Float(compute="_compute_payments_sum_of_interests", string="Sum of due interests")
    payments_sum_of_allowances = fields.Float(compute="_compute_payments_sum_of_allowances", string="Sum of due allowances")
    payments_sum_due = fields.Float(compute="_compute_payments_sum_due", string="Total amount due")

    @api.one
    def _compute_payments_sum_of_interests(self):
        if len(self.unreconciled_aml_ids) > 0:
            interests = 0
            for line in self.unreconciled_aml_ids:
                interests = interests + line.payments_interests
            self.payments_sum_of_interests = interests

    @api.one
    def _compute_payments_sum_of_allowances(self):
        if len(self.unreconciled_aml_ids) > 0:
            allowances = 0
            for line in self.unreconciled_aml_ids:
                allowances = allowances + line.payments_allowances
            self.payments_sum_of_allowances = allowances

    @api.one
    def _compute_payments_sum_due(self):
        self.payments_sum_due = self.payment_amount_due + self.payments_sum_of_interests + self.payments_sum_of_allowances

    def get_followup_with_interests_table_html(self, cr, uid, ids, context=None):
        _logger.debug("TEST TEST TEST \n\n\n")
        followup_table = super(partnerWithInterest, self).get_followup_table_html(self, cr, uid, ids, context)
        followup_table += '''<tr> </tr>
                            </table>
                            <center>''' + _("Total Amount due") + ''' : 42euros </center>'''
        return followup_table
