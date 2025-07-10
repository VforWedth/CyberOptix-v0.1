console.log("Working Fine huhh?");

const monthNames = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"
];

$("#review-form").submit(function (e) {
    e.preventDefault();

    let dt = new Date();
    let time = dt.getDate() + " " + monthNames[dt.getMonth()] + ", " + dt.getFullYear();

    $.ajax({
        data: $(this).serialize(),
        method: $(this).attr('method'),
        url: $(this).attr('action'),
        dataType: 'json',

        success: function (res) {
            console.log("Review Saved to DB...");

            if (res.bool == true) {
                $("#review-form").trigger("reset");
                $('#review-form').html('<p>Thank you for your review!</p>');

                let avatarUrl = res.context.avatar_url ? res.context.avatar_url : "/static/assets/images/avatar-01.jpg";

                let _html = '<div class="review-card">';
                _html += '<div class="review-header">';
                _html += '<img src="' + avatarUrl + '" >';
                _html += '<strong>' + res.context.user + '</strong> - <span>' + time + '</span>';

                for (let i = 1; i <= res.context.rating; i++) {
                    _html += '<i class="fa fa-star stars"></i>';
                }

                _html += '</div>';
                _html += '<p>' + res.context.review + '</p>';
                _html += '</div>';

                // Remove "No reviews yet" message if it exists
                $(".customer-reviews p:contains('No reviews yet')").remove();

                // Append new review at the top
                $(".customer-reviews").prepend(_html);
            }
        }
    });
});

$(document).ready(function () {
    $(".filter-checkbox, #price-filter-btn").on("click", function () {
        console.log("A checkbox has been clicked.");

        let filter_object = {}
        let min_price = $("#max_price").attr("min")
        let max_price = $("#max_price").val()

        filter_object.min_price = min_price;
        filter_object.max_price = max_price;

        $(".filter-checkbox").each(function () {
            let filter_value = $(this).val();
            let filter_key = $(this).data("filter");

            console.log("Filter Key is", filter_key);
            console.log("Filter Value is", filter_value);

            filter_object[filter_key] = Array.from(document.querySelectorAll('input[data-filter=' + filter_key + ']:checked')).map(function (element) {
                return element.value;
            }
            );
        })
        console.log("Filter Object is", filter_object);
        $.ajax({
            url: "/filter-products",
            data: filter_object,
            dataType: "json",
            beforeSend: function () {
                console.log("Trying to filter data...");
            },
            success: function (response) {
                console.log(response);
                console.log("Data filtered successfully");
                $("#filtered-product").html(response.data);
            }
        })
    })

    // Event listener for the max_price input blur event
    $("#max_price").on("blur", function () {
        let max_price = $(this).attr("max");
        let min_price = $(this).attr("min");
        let current_price = $(this).val();

        // console.log("Current Price is : ", current_price);
        // console.log("Maximum Price is : ", max_price);
        // console.log("Minimum Price is : ", min_price);

        if (current_price < parseInt(min_price) || current_price > parseInt(max_price)) {
            // console.log("Price is out of range");
            min_price = Math.round(min_price * 100) / 100
            max_price = Math.round(max_price * 100) / 100

            alert("Price must be between $" + min_price + " and $" + max_price);
            $(this).val(min_price);
            $("#range").val(min_price);

            $(this).focus();

            return false;
        }
    });

    
    // $(".delete-product").on("click", function(){
    //     let product_id = $(this).attr("data-product")
    //     let this_val = $(this)

    //     console.log("Product ID:",product_id)
    // })

    // $ajax({
    //     url: "/delete-from-cart",
    //     data: {
    //         "id": product_id,
    //     },
    //     dataType: "json",
    //     beforeSend: function(){
    //         this_val.hide()

    //     },
    //     success: function(response){
    //         this_val.show()
    //         $(".cart-items-count").text(response.totalcartitems)
    //         $("#cart-list").html(response.data)
    //     }
    // })



});


// Add to cart functionality 
$(".add-to-cart-btn").on("click", function () {
 
    let this_val = $(this)
    let index = this_val.attr("data-index");

    let quantity = $(".product-quantity-" + index).val()
    let product_title = $(".product-title-" + index).val()

    let product_id = $(".product-id-" + index).val()
    let product_price = $(".current-product-price-" + index).text().replace(/[^0-9.]/g, '')

    let product_pid = $(".product-pid-" + index).val()
    let product_image = $(".product-image-" + index).val()


    console.log("Quantity:", quantity);
    console.log("Title:", product_title);
    console.log("Price: ", product_price);
    console.log("ID: ", product_id);
    console.log("PID: ", product_pid);
    console.log("Image: ", product_image);
    console.log("Index: ", index);
    console.log("Currrent Element:", this_val);

    $.ajax({
        url: '/add-to-cart',
        data: {
            'id': product_id,
            'pid': product_pid,
            'image': product_image,
            'qty': quantity,
            'title': product_title,
            'price': product_price,
        },
        dataType: 'json',
        beforeSend: function () {
            console.log("Adding Product to Cart...");
        },
        success: function (response) {
            
            this_val.html("Item added to cart").prop('disabled', true  )
            console.log("Added Product to Cart!");
            $(".cart-items-count").text(response.totalcartitems)
             // Update the displayed total amount (add this line)
            $(".cart-total-amount").text(response.cart_total_amount.toFixed(2));

                // Clear existing cart items
    $(".cart-items").empty();
    
    // Rebuild cart items list
    $.each(response.data, function(item_id, item) {
        const itemTotal = (item.qty * item.price).toFixed(2);
        const cartItemHTML = `
            <div class="item" data-item-id="${item_id}">
                <div class="product-info">
                <img src="${item.image}" style="width: 70px;height: 70px;display: flex;" >
                   <h3 style="color:rgb(168, 160, 160);"><a href="{% url "flame:product-detail" item.pid %}" style="text-decoration:none;color: inherit;">${ item.title }</a></h3>
                    <div class="price">$${item.price}</div>
                    <div class="quantity">
                        <input type="number" value="${item.qty}" min="1">
                    </div>
                </div>
                <div class="item-total">
                    <span>$${itemTotal}</span>
                    <button class="remove-item update-product" ><i class="fa fa-refresh"></i></button>
                    <button class="remove-item delete-product" data-product="${item_id}"><i class="fa fa-trash"></i></button>
                </div>
            </div>
        `;
        $(".cart-items").append(cartItemHTML);
    });

    // Update subtotal and total
    $(".subtotal span:last").text("$" + response.cart_total_amount.toFixed(2));
    $(".total span:last").text("$" + response.cart_total_amount.toFixed(2));
        }
    })
});
// Update the delete-product handler in function.js
$(document).on('click', '.delete-product', function(e) {
    e.preventDefault();
    let product_id = $(this).data('product');
    let item_element = $(this).closest('.item');
    
    $.ajax({
        url: '/delete-from-cart',
        method: 'GET',
        data: { 'id': product_id },
        success: function(response) {
            // Remove from cart modal
            item_element.remove();
            
            // Remove from checkout page if exists
            $(`.checkout-item[data-item-id="${product_id}"]`).remove();
            
            // Update all counters and totals
            $(".cart-items-count, #cart-count").text(response.totalcartitems);
            $(".cart-total-amount, #subtotal").text(
                "$" + response.cart_total_amount.toFixed(2)
            );
            
            // Update checkout total if on checkout page
            $("#checkout-total").text("$" + response.cart_total_amount.toFixed(2));
        }
    });
});
// Universal cart update function
function updateCartTotals(response) {
    $(".cart-items-count").text(response.totalcartitems);
    $(".cart-total-amount").text(response.cart_total_amount.toFixed(2));
    $("#subtotal").text(response.cart_total_amount.toFixed(2));
}

// Update quantity handler
$(document).on('click', '.update-product', function(e) {
    let item_element = $(this).closest('.item');
    let product_id = item_element.data('item-id');
    let new_qty = item_element.find('input').val();
    
    $.ajax({
        url: '/update-cart',
        data: { 'id': product_id, 'qty': new_qty },
        success: function(response) {
            item_element.find('.item-total span').text(
                '$' + response.item_total.toFixed(2)
            );
            updateCartTotals(response);
        }
    });
});

// Update item quantity in cart
// Update item quantity
$(document).on('click', '.update-product', function(e) {
    e.preventDefault();
    let item_element = $(this).closest('.item');
    let product_id = item_element.data('item-id');
    let new_qty = item_element.find('input[type="number"]').val();
    
    $.ajax({
        url: '/update-cart',
        method: 'GET',
        data: {
            'id': product_id,
            'qty': new_qty
        },
        dataType: 'json',
        beforeSend: function() {
            console.log("Updating quantity...");
        },
        success: function(response) {
            // Update specific item's display
            let itemTotal = (new_qty * item_element.find('.price').text().replace('$', '')).toFixed(2);
            item_element.find('.item-total span').text('$' + itemTotal);
            
            // Update global totals
            $(".cart-total-amount").text(response.cart_total_amount.toFixed(2));
            $(".cart-items-count").text(response.totalcartitems);
            
            // Optional: Full cart refresh
            $(".subtotal span:last, .total span:last").text("$" + response.cart_total_amount.toFixed(2));
            // Add visual feedback
            //item_element.css({'background': '#e8f5e9'}).animate({'background': 'white'}, 1000);
        },
        error: function(xhr) {
            console.log("Error updating quantity:", xhr.responseText);
        }
    });
});

//Add real-time quantity validation:
$(document).on('input', '.quantity input', function() {
    let min = parseInt($(this).attr('min'));
    let val = parseInt($(this).val()) || min;
    
    if (val < min) {
        $(this).val(min);
    }
});