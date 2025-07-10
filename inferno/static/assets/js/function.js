console.log("Working Fine huhh?");

const monthNames = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"
];


$(document).ready(function () {
    
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
        // Add to cart functionality 
        $(".add-to-cart-btn[data-shop-id]").on("click", function () {
            
            let this_val = $(this)
            let index = this_val.attr("data-index");
    
            let quantity = $(".product-quantity-" + index).val()
            let product_title = $(".product-title-" + index).val()
    
            let product_id = $(".product-id-" + index).val()
            let product_price = $(".current-product-price-" + index).text().replace(/[^0-9.]/g, '')
    
            let product_pid = $(".product-pid-" + index).val()
            let product_image = $(".product-image-" + index).val()

            // let product_shopID = $(".product-shop-" + index).val()
            let shop_id = $(this).data('shop-id');
    
    
            console.log("Quantity:", quantity);
            console.log("Title:", product_title);
            console.log("Price: ", product_price);
            console.log("ID: ", product_id);
            console.log("PID: ", product_pid);
            console.log("Image: ", product_image);
            console.log("Index: ", index);
            console.log("Currrent Element:", this_val);
            console.log("Currrent Shop ID:", shop_id);
    
            $.ajax({
                url: '/add-to-shop-cart',
                data: {
                    'id': product_id,
                    'pid': product_pid,
                    'sid': shop_id,
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
    
                    this_val.html("Added to cart").prop('disabled', true)
                    console.log("Added Product to Cart!");
                    $(".cart-items-count").text(response.totalcartitems)
                }
            })
        });
// Delete Item Handler (Fixed)
$(document).on("click", ".delete-product", function() {
    const product_id = $(this).data('product');
    const shop_id = $(this).data('shop-id');
    const $shopSection = $(this).closest('.shop-cart-group');
    
    $.ajax({
        url: '/delete-from-shop-cart',
        data: { 'id': product_id, 'sid': shop_id },
        dataType: 'json',
        beforeSend: function() {
            $shopSection.find('.btn-delete').prop('disabled', true);
        },
        success: function(response) {
            if (response.status === 'success') {
                // Update shop section
                if (response.data.shop_html !== null) {
                    // Update the cart content for this shop
                    $(`#cart-content-${shop_id}`).html(response.data.shop_html);
                    
                    // Update shop counts
                    $(`#shop-count-${shop_id}`).text(
                        response.data.shop_quantity + ' item' + (response.data.shop_quantity !== 1 ? 's' : '')
                    );
                    $(`#shop-total-${shop_id}`).text('$'+response.data.shop_total.toFixed(2));
                } else {
                    // Remove entire shop section if no items left
                    $shopSection.remove();
                }
                
                // Update global totals
                $('.grand-total').text('$'+response.data.grand_total.toFixed(2));
                $('.total-cart-items').text(response.data.total_quantity);
                
                // Update header text
                const shopCount = response.data.shop_html !== null ? 
                    $('.shop-cart-group').length : 
                    $('.shop-cart-group').length - 1;
                    
                $('.cart_items_count').text(
                    'You have ' + response.data.total_quantity + ' item' + 
                    (response.data.total_quantity !== 1 ? 's' : '') + 
                    ' from ' + shopCount + ' shop' + 
                    (shopCount !== 1 ? 's' : '')
                );
                
                // Remove grand total section if cart is empty
                if (response.data.total_quantity === 0) {
                    $('.global-cart-summary').remove();
                }
            }
        },
        complete: function() {
            $shopSection.find('.btn-delete').prop('disabled', false);
        }
    });
});

        // Update Quantity
$(document).on("change", ".cart-qty", function() {
    const product_id = $(this).data('item-id');
    const shop_id = $(this).data('shop-id');
    const new_qty = $(this).val();
    const $row = $(this).closest('.cart-item');

    $.ajax({
        url: '/update-shop-cart',
        data: { 'id': product_id, 'sid': shop_id, 'qty': new_qty },
        dataType: 'json',
        beforeSend: function() {
            $row.find('input, button').prop('disabled', true);
        },
        success: function(response) {
            if (response.status === 'success') {
                // Update prices
                $row.find('.cart-total-amount').text('$'+response.data.item_total.toFixed(2));
                $(`#shop-total-${response.data.shop_id}`).text('$'+response.data.shop_total.toFixed(2));
                $('.grand-total').text('$'+response.data.grand_total.toFixed(2));
                
                // Update quantity counts
                $(`#shop-count-${response.data.shop_id}`).text(response.data.shop_quantity + ' item' + (response.data.shop_quantity !== 1 ? 's' : ''));
                $('.total-cart-items').text(response.data.total_quantity);
                
                // Update header
                let shopCount = $('.shop-cart-group').length;
                $('.cart_items_count').text(
                    'You have ' + response.data.total_quantity + ' item' + 
                    (response.data.total_quantity !== 1 ? 's' : '') + 
                    ' from ' + shopCount + ' shop' + 
                    (shopCount !== 1 ? 's' : '')
                );
            }
        },
        complete: function() {
            $row.find('input, button').prop('disabled', false);
        }
    });
});
        //Making Default Address
        $(document).on("click", ".make-default-address", function(){
            let id = $(this).attr("data-address-id")
            let this_val = $(this)

            console.log("ID is:",id);
            console.log("Element is: ", this_val);

            $.ajax({
                url: "/make-default-address",
                data:{
                    "id": id
                },
                dataType: "json",
                success: function(response){
                    if(response.boolean == true){
                        $(".check").hide();
                        $(".action_btn").show()

                        $(".check"+id).show()
                        $(".button"+id).hide()

                        console.log("The default address has been set successfully.");
                    }
                }
            })
        })   

        //Adding to wishlist
        $(document).on("click",".add-to-wishlist", function(){
            let product_id = $(this).attr("data-product-item")
            let this_val = $(this)

            console.log("Product ID: ",product_id);

            $.ajax({
                url: "/add-to-wishlist",
                data:{
                    "id": product_id,
                },
                dataType:"json",
                beforeSend: function(){
                    console.log("Adding to wishlist...");
                },
                success: function(response){
                    $("#wishlist-count").text(response.wishlist_count);
                    this_val.prop("disabled", true).html('<i class="fas fa-heart"></i>');
                    if (response.new_item) {
                        $(".wishlist-items").append(response.new_item);
                    }
                    
                    console.log("Added to wishlist successfully!");
                },
                
                
            })
        })

        
        // Remove from wishlist
        $(document).on("click",".delete-wishlist-product", function(){
            let wishlist_id = $(this).attr("data-wishlist-product")
            let this_val = (this)

            console.log("Wishlist ID:", wishlist_id);
            $.ajax({
                url: "/remove-from-wishlist",
                data:{
                    "id": wishlist_id
                },
                dataType:"json",
                beforeSend: function(){
                    console.log("Removing product from wishlist...");
                },
                success: function(response){
                    $('#wishlist-count').text(response.wishlist_count);

                    $("#wishlist-list").html(response.data)
                    
                    console.log("Removed product from wishlist!");

                }
            })
        })

});
    
        // $(document).on("click",".delete-product",function(){
        //     let product_id = $(this).attr("data-product")
        //     let shop_id = $(this).data("shop-id")
        //     let this_val = $(this)
    
        //     console.log("Product ID: ",product_id);
        //     console.log("Shop ID", shop_id)
    
        //     $.ajax({
        //         url:"/delete-from-shop-cart",
        //         data:{
        //             "id": product_id,
        //             "sid": shop_id,
        //         },
        //         dataType: "json",
        //         beforeSend: function(){
        //             this_val.hide()
    
        //         },
        //         success: function(response){
        //             this_val.show()
        //             $(".cart-items-count").text(response.totalcartitems)
        //             $("#cart-list").html(response.data)
        //             $(".cart-total-amount").text(response.cart_total_amount.toFixed(2));

        //             // Update specific shop's cart section
        //             // $(`#shop-${shop_id}-cart`).html(response.data);
        //         }
        //     })
        // })
    
        
        // $(document).on("click",".update-product",function(){
        //     let product_id = $(this).attr("data-product")
        //     let product_qty = $(".product-qty-"+product_id).val() 
        //     let this_val = $(this)
    
        //     console.log("Product ID: ",product_id);
        //     console.log("Product Qty: ",product_qty);
    
        //     $.ajax({
        //         url:"/update-cart",
        //         data:{
        //             "id": product_id,
        //             "qty": product_qty,
        //         },
        //         dataType: "json",
        //         beforeSend: function(){
        //             this_val.hide()
    
        //         },
        //         success: function(response){
        //             this_val.show()
        //             $(".cart-total-amount").text(response.cart_total_amount.toFixed(2));
    
        //             $(".cart-items-count").text(response.totalcartitems)
        //             $("#cart-list").html(response.data)
        //         }
        //     })
        // })
        // //From this to 
        // // Input field quantity update
        // $(document).on("change", ".cart-qty", function() {
        //     let product_id = $(this).data("item-id");
        //     let product_qty = $(this).val();
        //     // Trigger update AJAX
        //     $(`.update-product[data-product="${product_id}"]`).click();
        // });
        //     // Update quantity on input change
        // $(document).on("change", ".cart-qty", function() {
        //     const product_id = $(this).data("item-id");
        //     const product_qty = $(this).val();
            
        //     $.ajax({
        //         url: "/update-cart",
        //         data: {
        //             "id": product_id,
        //             "qty": product_qty
        //         },
        //         success: function(response) {
        //             $("#cart-list").html(response.data);
        //             $(".cart-items-count").text(response.totalcartitems);
        //         }
        //     });
        // });

        //this have to be add to update the pages without refreshing the page

// // Dynamic Filter Handling
// document.querySelectorAll('.filter-option').forEach(option => {
//     option.addEventListener('click', function(e) {
//         e.preventDefault();
//         const filterType = this.getAttribute('data-filter-type');
//         const filterValue = this.getAttribute('data-filter-value');
        
//         // Update URL with new filter parameters
//         const url = new URL(window.location.href);
//         url.searchParams.set(filterType, filterValue);
//         window.history.pushState({}, '', url);
        
//         // Refresh products
//         fetchFilteredProducts();
//     });
// });

// async function fetchFilteredProducts() {
//     const response = await fetch(window.location.href, {
//         headers: {'X-Requested-With': 'XMLHttpRequest'}
//     });
//     const data = await response.text();
    
//     // Update product grid
//     const parser = new DOMParser();
//     const doc = parser.parseFromString(data, 'text/html');
//     document.querySelector('.product-grid').innerHTML = 
//         doc.querySelector('.product-grid').innerHTML;
        
//     // Reattach event listeners
//     attachCartHandlers();
// }

// // Cart Handling with Shop Context
// function attachCartHandlers() {
//     document.querySelectorAll('.cartButton').forEach(button => {
//         button.addEventListener('click', async function() {
//             const productId = this.dataset.productId;
//             const shopSlug = "{{ current_shop.slug }}";
            
//             try {
//                 const response = await fetch(`/add-to-cart/${shopSlug}/${productId}/`, {
//                     method: 'POST',
//                     headers: {
//                         'X-CSRFToken': getCookie('csrftoken'),
//                         'Content-Type': 'application/json'
//                     }
//                 });
                
//                 if (response.ok) {
//                     updateCartUI();
//                 }
//             } catch (error) {
//                 console.error('Error adding to cart:', error);
//             }
//         });
//     });
// }



