from odoo import models, fields, api


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.model
    def create(self, vals):
        sale_order = super(SaleOrder, self).create(vals)
        sale_order._manage_customer_pricelist()
        return sale_order

    def write(self, vals):
        res = super(SaleOrder, self).write(vals)
        self._manage_customer_pricelist()
        return res

    def _manage_customer_pricelist(self):
        for order in self:
            customer = order.partner_id
            product_prices = {line.product_id: line.price_unit for line in order.order_line}
            if not customer.property_product_pricelist:
                pricelist = self.env['product.pricelist'].create({
                    'name': f'{customer.name} Pricelist',
                    'item_ids': [(0, 0, {
                        'applied_on': '1_product',
                        'product_id': product.id,
                        'fixed_price': price,
                        'product_tmpl_id': product.product_tmpl_id.id
                    }) for product, price in product_prices.items()],
                })
                customer.write({'property_product_pricelist': pricelist.id})
            else:
                pricelist = customer.property_product_pricelist
                for product, price in product_prices.items():
                    pricelist_item = self.env['product.pricelist.item'].search([
                        ('pricelist_id', '=', pricelist.id),
                        ('product_id', '=', product.id),
                    ], limit=1)
                    if pricelist_item:
                        pricelist_item.write({'fixed_price': price})
                    else:
                        self.env['product.pricelist.item'].create({
                            'pricelist_id': pricelist.id,
                            'applied_on': '1_product',
                            'product_id': product.id,
                            'fixed_price': price,
                            'product_tmpl_id': product.product_tmpl_id.id
                        })
