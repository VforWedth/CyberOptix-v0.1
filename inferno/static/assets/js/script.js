document.addEventListener("DOMContentLoaded", function () {
  const navItems = document.querySelectorAll(".nav-item");
  const mainContent = document.querySelector(".main-content");

  navItems.forEach((item) => {
    item.addEventListener("click", function () {
      navItems.forEach((el) => el.classList.remove("active"));
      this.classList.add("active");

      const sectionName = this.querySelector("span")?.innerText.trim();
      console.log("Clicked section:", sectionName);

      if (!sectionName) {
        console.warn("No section name found for nav item.");
        return;
      }

      if (sectionName === "Products") {
        fetch("products.html")
          .then((res) => {
            if (!res.ok) throw new Error("Page");
            return res.text();
          })
          .then((html) => {
            mainContent.innerHTML = html;
          })
          .catch((err) => {
            mainContent.innerHTML = `<p>Error loading content: ${err.message}</p>`;
            console.error(err);
          });
      } 
      else if (sectionName === "Orders") {
        fetch("/orders/")
          .then(res => {
            if (!res.ok) throw new Error("Load failed");
            return res.text();
          })
          .then(html => {
            mainContent.innerHTML = html;
            
            // Add event listeners for edit buttons after orders load
            document.querySelectorAll('.edit-icon').forEach(button => {
              button.addEventListener('click', function() {
                const orderId = this.getAttribute('data-order-id');
                loadEditOrder(orderId);
              });
            });
          })
          .catch(err => {
            mainContent.innerHTML = `<p>Error loading content: ${err.message}</p>`;
          });
      }
      else {
        mainContent.innerHTML = `
          <div class="page-title">
            <div class="title">${sectionName}</div>
          </div>
          <p>${sectionName} content goes here.</p>
        `;
      }
    });
  });

  // Function to load edit order form
  function loadEditOrder(orderId) {
    fetch(`/orders/${orderId}/edit/`)
      .then(res => {
        if (!res.ok) throw new Error("Failed to load edit form");
        return res.text();
      })
      .then(html => {
        mainContent.innerHTML = html;
      })
      .catch(err => {
        mainContent.innerHTML = `<p>Error loading edit form: ${err.message}</p>`;
        console.error(err);
      });
  }

  // Helper function to get CSRF token
  function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
      const cookies = document.cookie.split(';');
      for (let i = 0; i < cookies.length; i++) {
        const cookie = cookies[i].trim();
        if (cookie.substring(0, name.length + 1) === (name + '=')) {
          cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
          break;
        }
      }
    }
    return cookieValue;
  }
});