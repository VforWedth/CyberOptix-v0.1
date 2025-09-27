/**
 * KBZPay Mock JavaScript SDK
 * This is a mock implementation for testing purposes
 */

(function(window) {
    'use strict';

    const KBZPayJS = {
        config: {
            baseUrl: '/kbzpay',
            popupWidth: 500,
            popupHeight: 700
        },

        /**
         * Initialize payment with KBZPay
         * @param {string} dataString - JSON string containing prepay_id and payment info
         * @param {function} callback - Callback function with response
         */
        pay: function(dataString, callback) {
            try {
                // Parse the data string
                let paymentData;
                if (typeof dataString === 'string') {
                    try {
                        paymentData = JSON.parse(dataString);
                    } catch (e) {
                        paymentData = { prepay_id: dataString };
                    }
                } else {
                    paymentData = dataString;
                }

                // Extract prepay_id
                const prepayId = paymentData.prepay_id || paymentData;

                // Open payment window
                const paymentUrl = `${this.config.baseUrl}/payment/${prepayId}/`;
                const left = (window.screen.width - this.config.popupWidth) / 2;
                const top = (window.screen.height - this.config.popupHeight) / 2;

                const paymentWindow = window.open(
                    paymentUrl,
                    'KBZPayPayment',
                    `width=${this.config.popupWidth},height=${this.config.popupHeight},left=${left},top=${top},toolbar=no,menubar=no,scrollbars=yes,resizable=no,location=no,status=no`
                );

                // Listen for messages from payment window
                const messageHandler = function(event) {
                    if (event.data && event.data.type) {
                        if (event.data.type === 'kbzpay_success') {
                            window.removeEventListener('message', messageHandler);
                            if (callback) {
                                callback({
                                    code: 0,
                                    msg: 'Payment successful',
                                    data: event.data.data
                                });
                            }
                        } else if (event.data.type === 'kbzpay_canceled') {
                            window.removeEventListener('message', messageHandler);
                            if (callback) {
                                callback({
                                    code: 1,
                                    msg: 'Payment canceled',
                                    data: event.data.data
                                });
                            }
                        }
                    }
                };

                window.addEventListener('message', messageHandler);

                // Check if window was blocked
                if (!paymentWindow || paymentWindow.closed || typeof paymentWindow.closed === 'undefined') {
                    if (callback) {
                        callback({
                            code: -1,
                            msg: 'Failed to open payment window. Please check your popup blocker settings.',
                            data: {}
                        });
                    }
                    return;
                }

                // Monitor window closure
                const checkClosed = setInterval(function() {
                    if (paymentWindow.closed) {
                        clearInterval(checkClosed);
                        window.removeEventListener('message', messageHandler);
                        // Only call callback if not already called
                        if (callback) {
                            callback({
                                code: 2,
                                msg: 'Payment window closed',
                                data: {}
                            });
                        }
                    }
                }, 500);

            } catch (error) {
                if (callback) {
                    callback({
                        code: -1,
                        msg: 'Error initializing payment: ' + error.message,
                        data: {}
                    });
                }
            }
        },

        /**
         * Query payment status
         * @param {object} params - Query parameters (out_trade_no or prepay_id)
         * @param {function} callback - Callback function with response
         */
        queryStatus: function(params, callback) {
            const xhr = new XMLHttpRequest();
            xhr.open('POST', `${this.config.baseUrl}/api/query/`, true);
            xhr.setRequestHeader('Content-Type', 'application/json');

            xhr.onreadystatechange = function() {
                if (xhr.readyState === 4) {
                    if (xhr.status === 200) {
                        const response = JSON.parse(xhr.responseText);
                        if (callback) callback(response);
                    } else {
                        if (callback) {
                            callback({
                                code: 'ERROR',
                                msg: 'Failed to query status',
                                data: {}
                            });
                        }
                    }
                }
            };

            xhr.send(JSON.stringify(params));
        }
    };

    // Export to window
    window.KBZPayJS = KBZPayJS;

})(window);