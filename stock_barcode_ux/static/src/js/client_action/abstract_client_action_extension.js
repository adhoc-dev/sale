odoo.define('stock_barcode.ClientActionExtension', function (require) {
    'use strict';

var ClientAction = require('stock_barcode.ClientAction');
var core = require('web.core');
var _t = core._t;


ClientAction.include({
    // Start change: Declaramos variable de clase que contendrá el valor recibido de bloqueo end
    init: function (parent, action) {
        this._super.apply(this, arguments);
        this.stateblockquantity;
    },

    /* Start change: Llamamos a la función asíncrona que traerá el valor del back y luego forzamos una entrada para lograr que el método asincrono termine de traer la variable end */

    start: function () {
        this._buscaBAQ(this.actionParams.model, this.actionParams.pickingId); //aca verificamos si la variable es true o false
        this._super.apply(this, arguments);
    },
    /* Start change: El retorno depende de lo escaneado y del valor de la variable end */
    /**
     * @override
     * @abstract
     * @private
     * @param {Object} product product on the new line
     * @param {Object} barcode barcode of the product
     * @param {Object} qty_done
     * @returns {object} created line
     */
    _makeNewLine: function (product, barcode, qty_done) {  // jshint ignore:line
        if (this.stateblockquantity){
            return ;
        }else{
            return(this._super.apply(this, arguments));
        }
    },
    /* Start change: Seteo y retorno de variable de clase end */
    /**
     * @private
     */
    _setVariableBAQ: function (a){
        this.stateblockquantity = a;
    },

    /**
     * @private
     */
    _getVariableBAQ: function(){
        return this.stateblockquantity;
    },
    /* Start change: Método asíncrono que se relaciona con el método de stock_picking_py para lograr atrapar la variable block additional quantities end */
    /**
     * @private
     * @returns {Promise}
     */
    _buscaBAQ: async function (apmodel, appickingid) {
        var verifica = await this._rpc({
            model: apmodel,
            method: 'getPickingTypeOperation',
            args: [appickingid],
        }).then((result)=>result);
        this._setVariableBAQ(verifica);
    },

    /* Start change: El cambio se encuentra cuando lee una linea que no se encuentra registrada en la transferencia. En ese caso verifica la variable de bloqueo para ver si la nueva linea es aceptada en la transferencia end */
    /**
     * @override
     * @private
     * @param {Object} params information needed to find the potential candidate line
     * @param {Object} params.product
     * @param {Object} params.lot_id
     * @param {Object} params.lot_name
     * @param {Object} params.package_id
     * @param {Object} params.result_package_id
     * @param {Boolean} params.doNotClearLineHighlight don't clear the previous line highlight when
     *     highlighting a new one
     * @return {object} object wrapping the incremented line and some other informations
     */
    _incrementLines: function (params) {
        if (!this.stateblockquantity){
            /* super._incrementProduct(params); */
            return(this._super.apply(this, arguments));
        } else{
            var line = this._findCandidateLineToIncrement(params);
            var isNewLine = false;
            if (line) {
                /* super._incrementProduct(params); */
                return(this._super.apply(this, arguments));
            } else {
                isNewLine = true;
                // Create a line with the processed quantity.
                if(!this.stateblockquantity){
                    if (params.product.tracking === 'none' ||
                        params.lot_id ||
                        params.lot_name ||
                        !this.requireLotNumber
                        ) {//Entra aca si hay una nueva linea
                        line = this._makeNewLine(params.product, params.barcode, params.product.qty || 1, params.package_id, params.result_package_id, params.owner_id);
                    } else {
                        line = this._makeNewLine(params.product, params.barcode, 0, params.package_id, params.result_package_id);
                    }
                    this._getLines(this.currentState).push(line);
                    this.pages[this.currentPageIndex].lines.push(line);
                }
            }
            if (this.actionParams.model === 'stock.picking') {
                if (params.lot_id) {
                    line.lot_id = [params.lot_id];
                }
                if (params.lot_name) {
                    line.lot_name = params.lot_name;
                }
            } else if (this.actionParams.model === 'stock.inventory') {
                if (params.lot_id) {
                    line.prod_lot_id = [params.lot_id, params.lot_name];
                }
            }
            return {
                'id': line.id,
                'virtualId': line.virtual_id,
                'lineDescription': line,
                'isNewLine': isNewLine,
            };
        }
    },

    /* Start change: Agregamos el mensaje de error si cumple las restricciones del if dependiendo lo seteado en la variable de bloqueo end */
    /**
     * @override
     * @param {string} barcode scanned barcode
     * @param {Object} linesActions
     * @returns {Promise}
     */
    _step_product: async function (barcode, linesActions) {
        var self = this;
        this.currentStep = 'product';
        var errorMessage;
        var product = await this._isProduct(barcode)
        if (product) {
            if (product.tracking !== 'none' && self.requireLotNumber) {
                this.currentStep = 'lot';
            }
            var res = this._incrementLines({'product': product, 'barcode': barcode});
            if (res.isNewLine && !this.stateblockquantity) {
                if (this.actionParams.model === 'stock.inventory') {
                    // FIXME sle: add owner_id, prod_lot_id, owner_id, product_uom_id
                    return this._rpc({
                        model: 'product.product',
                        method: 'get_theoretical_quantity',
                        args: [
                            res.lineDescription.product_id.id,
                            res.lineDescription.location_id.id,
                        ],
                    }).then(function (theoretical_qty) {
                        res.lineDescription.theoretical_qty = theoretical_qty;
                        linesActions.push([self.linesWidget.addProduct, [res.lineDescription, self.actionParams.model]]);
                        self.scannedLines.push(res.id || res.virtualId);
                        return Promise.resolve({linesActions: linesActions});
                    });
                } else {
                    linesActions.push([this.linesWidget.addProduct, [res.lineDescription, this.actionParams.model]]);
                }
            }else if(res.isNewLine && this.stateblockquantity){
                errorMessage = _t('You can not scan quantities that were not reserved or products that have not been initially registered in the transfer.');
                return Promise.reject(errorMessage);
            } else {
                if (product.tracking === 'none' || !self.requireLotNumber) {
                    linesActions.push([this.linesWidget.incrementProduct, [res.id || res.virtualId, product.qty || 1, this.actionParams.model]]);
                } else {
                    linesActions.push([this.linesWidget.incrementProduct, [res.id || res.virtualId, 0, this.actionParams.model]]);
                }
            }
            this.scannedLines.push(res.id || res.virtualId);
            return Promise.resolve({linesActions: linesActions});
        } else {
            var success = function (res) {
                return Promise.resolve({linesActions: res.linesActions});
            };
            var fail = function (specializedErrorMessage) {
                self.currentStep = 'product';
                if (specializedErrorMessage){
                    return Promise.reject(specializedErrorMessage);
                }
                if (! self.scannedLines.length) {
                    if (self.groups.group_tracking_lot) {
                        errorMessage = _t("You are expected to scan one or more products or a package available at the picking's location");
                    } else {
                        errorMessage = _t('You are expected to scan one or more products.');
                    }
                    return Promise.reject(errorMessage);
                }

                var destinationLocation = self.locationsByBarcode[barcode];
                if (destinationLocation) {
                    return self._step_destination(barcode, linesActions);
                } else {
                    errorMessage = _t('You are expected to scan more products or a destination location. ');
                    return Promise.reject(errorMessage);
                }
            };
            return self._step_lot(barcode, linesActions).then(success, function () {
                return self._step_package(barcode, linesActions).then(success, fail);
            });
        }
    },
})
});
