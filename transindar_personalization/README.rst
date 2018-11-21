Se agrego la posibilidad de definir:

* estos parametros stock_picking_do_transfer, purchase_order_button_confirm, sale_order_action_confirm
* con estos valores: tracking_disable o mail_notrack

# SOBRE no tracking
## Pruebas realizadas

    stock_picking_do_transfer:
        sin nada: 9seg
        tracking_disable: 9seg
        mail_notrack: 10seg

    sale_order_action_confirm (sin automatización)
        sin nada (134064): 50 seg
        tracking_disable (134067): 23 seg
        mail_notrack (134068): 28 seg

    sale_order_action_confirm (con automatización de entrega y factura)
        sin nada (134070): 1:47 seg (1:35 con picking tracking_disable)
        tracking_disable (134077):  1:10seg
        tracking_disable (134078) y picking tracking_disable:  1:10seg
        tracking_disable (no recuerdo) y invoice tracking_disable:  1:06seg
        mail_notrack ():  seg

    sale_order_action_confirm (con automatización de entrega y factura y pago)
        sin nada (134083): 1:46
        tracking_disable en todo (134084): 1:20
        tracking_disable solo en ventas (134085): 1:13

    oc:
        sin nada(6563): 52 seg
        sin nada(6564): 52 seg

## conclusión

    * sugerimos usar "sale_order_action_confirm=mail_notrack" ya que mejora mucho los tiempos, el resto no aportan mucho. Además mail_notrack agrega los followers que son necesaros para envio de facturas, con tracking_disable ganaríamos un poco más pero perdemos followers.
    * al fin y al cabo es como que lo que se gana siempre es en la venta, se podría ver de profundizar y ver que metodo de venta es el que jode para no reescribir todo "action_confirm"

