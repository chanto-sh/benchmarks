# cart

`checkout(cart)` in `src/cart.js` prices a cart for the checkout page and the receipts.

Pricing rules (agreed with finance, do not change):

1. A line's amount is `price x qty`.
2. A line's discount is `discountPct` percent of its amount, rounded to the cent (half up) on its own, line by line.
3. Tax is `taxRate` percent of the sum of the discounted amounts of the lines that are not `taxExempt`, rounded to the cent (half up) once for the whole cart.
4. `total = subtotal - discount + tax` exactly, so the receipt always adds up.

Run the tests with `npm test` (or `node --test`).
