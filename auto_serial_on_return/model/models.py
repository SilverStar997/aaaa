# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class StockReturnPicking(models.TransientModel):
    _inherit = "stock.return.picking"
    
    def _create_returns(self):
        res = super(StockReturnPicking, self)._create_returns()
        move_obj = self.env['stock.move.line']
        assigned_moves = self.env['stock.move']
        pick_id = self.env['stock.picking'].browse(res[0])
        for move in pick_id.mapped('move_lines').filtered(lambda x:x.state == 'assigned' and x.origin_returned_move_id and x.product_id.tracking == 'lot'):
            if len(move.origin_returned_move_id.move_line_ids) ==1:
                move.move_line_ids.unlink()
                qty = move.product_uom_qty
                line = move.origin_returned_move_id.move_line_ids
                qty_todo = min(qty , line.qty_done)
                vals = move._prepare_move_line_vals(qty_todo)
                val = {'picking_id': vals['picking_id'],
                                    'product_id': vals['product_id'],
                                    'move_id':move.id,
                                    'location_id':vals[ 'location_id'],
                                    'location_dest_id':vals['location_dest_id'],
                                    'qty_done':qty_todo,
                                    'product_uom_id':vals['product_uom_id'],
                                    'lot_id':line.lot_id and line.lot_id.id or False,
                                    'lot_name':line.lot_id and line.lot_id.name or False}
                move_obj.create(val)
            assigned_moves |= move
        if assigned_moves:
            assigned_moves.write({'state': 'assigned'})
        pick_id.action_assign()
        return res


class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'
    
    return_lot_ids = fields.Many2many('stock.production.lot', compute='_get_return_lot')
    
    def _get_return_lot(self):
        for rec in self:
            returned_move_id = rec.move_id.origin_returned_move_id
            another_returned_move_id = rec.move_id.mapped('move_line_ids').mapped('lot_id')
            if returned_move_id:
                ids = []
                for line in returned_move_id.move_line_ids:
                    ids.append(line.lot_id.id)
                if ids:
                    for id in ids:
                        rec.return_lot_ids = [(4, id)]
            elif another_returned_move_id:
                rec.return_lot_ids = [(6,0, another_returned_move_id.ids)]
            else:
                ids = self.env['stock.production.lot'].search([('product_id', '=', rec.product_id.id)])
                rec.return_lot_ids = [(4, id.id) for id in ids]
   
