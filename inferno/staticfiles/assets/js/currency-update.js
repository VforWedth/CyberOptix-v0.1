// static/assets/js/currency-update.js

// Add this to your function.js
function formatPriceForLanguage(priceUSD, language, exchangeRate) {
    if (language === 'my') {
        const priceMMK = priceUSD * exchangeRate;
        const formatted = Math.round(priceMMK).toLocaleString('en-US');
        const myanmarFormatted = convertToMyanmarNumerals(formatted);
        return myanmarFormatted + ' ကျပ်';
    } else {
        return '$' + priceUSD.toFixed(2);
    }
}

function convertToMyanmarNumerals(text) {
    const numeralMap = {
        '0': '၀', '1': '၁', '2': '၂', '3': '၃', '4': '၄',
        '5': '၅', '6': '၆', '7': '၇', '8': '၈', '9': '၉'
    };
    
    let result = text.toString();
    for (const [eng, myan] of Object.entries(numeralMap)) {
        result = result.replace(new RegExp(eng, 'g'), myan);
    }
    return result;
}

// Update all price displays when language changes
$(document).ready(function() {
    // Get language and exchange rate from meta tags or data attributes
    const language = $('html').attr('lang') || 'en';
    const exchangeRate = parseFloat($('meta[name="exchange-rate"]').attr('content') || 3500);
    
    // Update prices on AJAX cart operations
    $(document).on('cart-updated', function() {
        $('.price-display').each(function() {
            const priceUSD = parseFloat($(this).data('price-usd'));
            const formatted = formatPriceForLanguage(priceUSD, language, exchangeRate);
            $(this).text(formatted);
        });
    });
});