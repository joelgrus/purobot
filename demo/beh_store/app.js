const STORE = {
  all: "All departments",
  quickPicks: [
    "Spaghetti",
    "Garlic Bulb",
    "Olive Oil",
    "Parmesan Shredded Cheese",
    "Fresh Basil",
    "Chicken Thighs",
    "Flour Tortillas",
    "Limes",
  ],
};

const state = {
  query: "",
  category: STORE.all,
  cart: [],
};

const elements = {
  search: document.querySelector("#store-search"),
  clearSearch: document.querySelector("#clear-search"),
  categoryPills: document.querySelector("#category-pills"),
  resultsCount: document.querySelector("#results-count"),
  searchStatus: document.querySelector("#search-status"),
  productGrid: document.querySelector("#product-grid"),
  quickPicks: document.querySelector("#quick-picks"),
  cartSummary: document.querySelector("#cart-summary"),
  cartItems: document.querySelector("#cart-items"),
  subtotal: document.querySelector("#subtotal"),
  taxTotal: document.querySelector("#tax-total"),
  grandTotal: document.querySelector("#grand-total"),
  checkoutTotal: document.querySelector("#checkout-total"),
  checkoutItems: document.querySelector("#checkout-items"),
  startCheckout: document.querySelector("#start-checkout"),
  status: document.querySelector("#status"),
  checkoutModal: document.querySelector("#checkout-modal"),
  closeCheckout: document.querySelector("#close-checkout"),
  closeCheckoutButton: document.querySelector("#close-checkout-button"),
  checkoutStatus: document.querySelector("#checkout-status"),
  submitOrder: document.querySelector("#submit-order"),
};

function formatMoney(value) {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
  }).format(value);
}

function cartSubtotal() {
  return state.cart.reduce((sum, item) => sum + item.price, 0);
}

function estimatedTax() {
  return cartSubtotal() * 0.0825;
}

function grandTotal() {
  return cartSubtotal() + 7.95 + estimatedTax();
}

function categories() {
  return [STORE.all, ...new Set(BEH_CATALOG.map((item) => item.categoryLabel))];
}

function matchesQuery(item, query) {
  if (!query) {
    return false;
  }
  return matchScore(item, query) > 0;
}

function matchScore(item, query) {
  const tokens = query
    .toLowerCase()
    .split(/\s+/)
    .filter(Boolean);
  const haystack = [item.name, item.size, item.categoryLabel, ...item.keywords]
    .join(" ")
    .toLowerCase();
  return tokens.reduce((score, token) => score + (haystack.includes(token) ? 1 : 0), 0);
}

function visibleItems() {
  if (!state.query) {
    return [];
  }
  const items = BEH_CATALOG.filter((item) => {
    const matchesCategory =
      state.category === STORE.all || item.categoryLabel === state.category;
    return matchesCategory && matchesQuery(item, state.query);
  });
  return items.sort((left, right) => {
    return matchScore(right, state.query) - matchScore(left, state.query);
  });
}

function setStatus(message) {
  elements.status.innerHTML = message;
}

function renderPills() {
  elements.categoryPills.innerHTML = "";
  categories().forEach((label) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = `pill${state.category === label ? " is-active" : ""}`;
    button.textContent = label;
    button.addEventListener("click", () => {
      state.category = label;
      renderResults();
    });
    elements.categoryPills.appendChild(button);
  });
}

function renderQuickPicks() {
  elements.quickPicks.innerHTML = "";
  STORE.quickPicks
    .map((name) => BEH_CATALOG.find((item) => item.name === name))
    .filter(Boolean)
    .forEach((item) => {
      const card = document.createElement("article");
      card.className = "highlight-card";
      card.innerHTML = `
        <p class="eyebrow">${item.categoryLabel}</p>
        <h3>${item.name}</h3>
        <p class="product-card__meta">${item.size}</p>
        <div class="price-row">
          <span class="price">${formatMoney(item.price)}</span>
          <button class="button button--add" type="button" data-add-item="${item.id}">Add</button>
        </div>
      `;
      elements.quickPicks.appendChild(card);
    });
}

function renderResults() {
  const items = visibleItems();
  renderPills();
  elements.resultsCount.textContent = `${items.length} items`;
  elements.searchStatus.textContent = state.query
    ? `Showing matches for "${state.query}".`
    : "Search to see matching store items.";

  elements.productGrid.innerHTML = "";
  if (!state.query) {
    elements.productGrid.innerHTML = `
      <div class="empty-state empty-state--results">
        <strong>Search the store to see results.</strong>
        <span class="muted">Try spaghetti, basil, chicken thighs, tortillas, milk, or apples.</span>
      </div>
    `;
    return;
  }

  if (!items.length) {
    elements.productGrid.innerHTML = `
      <div class="empty-state empty-state--results">
        <strong>No items matched "${state.query}".</strong>
        <span class="muted">Try a broader ingredient name or a different department.</span>
      </div>
    `;
    return;
  }

  items.forEach((item) => {
    const card = document.createElement("article");
    card.className = "product-card";
    card.innerHTML = `
      <p class="product-card__badge">${item.categoryLabel}</p>
      <div>
        <h3>${item.name}</h3>
        <p class="product-card__meta">${item.size} · SKU ${item.sku}</p>
      </div>
      <p class="product-card__keywords">${item.keywords.slice(0, 4).join(" · ")}</p>
      <div class="price-row">
        <span class="price">${formatMoney(item.price)}</span>
        <button class="button button--add" type="button" data-add-item="${item.id}">Add to cart</button>
      </div>
    `;
    elements.productGrid.appendChild(card);
  });
}

function renderCart() {
  elements.cartItems.innerHTML = "";

  if (!state.cart.length) {
    elements.cartItems.innerHTML = `
      <div class="empty-state">
        <strong>Your cart is empty.</strong>
        <span class="muted">Try spaghetti, garlic, basil, tortillas, or chicken thighs.</span>
      </div>
    `;
  } else {
    state.cart.forEach((item) => {
      const row = document.createElement("div");
      row.className = "cart-item";
      row.innerHTML = `
        <div class="cart-item__top">
          <span class="cart-item__name">${item.name}</span>
          <strong>${formatMoney(item.price)}</strong>
        </div>
        <div class="cart-item__meta">${item.size} · ${item.categoryLabel}</div>
      `;
      elements.cartItems.appendChild(row);
    });
  }

  const subtotal = cartSubtotal();
  const tax = estimatedTax();
  const total = grandTotal();
  elements.cartSummary.textContent = `Cart has ${state.cart.length} items.`;
  elements.subtotal.textContent = formatMoney(subtotal);
  elements.taxTotal.textContent = formatMoney(tax);
  elements.grandTotal.textContent = formatMoney(total);
  elements.checkoutTotal.textContent = formatMoney(total);
  elements.startCheckout.disabled = state.cart.length === 0;
}

function renderCheckout() {
  elements.checkoutItems.innerHTML = "";
  if (!state.cart.length) {
    elements.checkoutItems.innerHTML = `<div class="empty-state"><strong>No items yet.</strong></div>`;
    return;
  }

  state.cart.forEach((item) => {
    const row = document.createElement("div");
    row.className = "checkout-item";
    row.innerHTML = `
      <div class="checkout-item__top">
        <span class="checkout-item__name">${item.name}</span>
        <strong>${formatMoney(item.price)}</strong>
      </div>
      <div class="checkout-item__meta">${item.size} · Delivery eligible</div>
    `;
    elements.checkoutItems.appendChild(row);
  });
}

function addToCart(itemId) {
  const item = BEH_CATALOG.find((entry) => entry.id === itemId);
  if (!item) {
    setStatus("That item was not found.");
    return;
  }
  state.cart.push(item);
  renderCart();
  renderCheckout();
  setStatus(`<strong>Added ${item.name}</strong> to your B-E-H cart.`);
}

function openCheckout() {
  renderCheckout();
  elements.checkoutStatus.textContent = "Review items, total, and delivery details before placing the order.";
  elements.checkoutModal.hidden = false;
}

function closeCheckout() {
  elements.checkoutModal.hidden = true;
}

function placeOrder() {
  const orderNumber = `BEH-${Math.floor(100000 + Math.random() * 900000)}`;
  elements.checkoutStatus.innerHTML = `<strong>Order placed.</strong> Confirmation ${orderNumber}.`;
  setStatus(`<strong>Order submitted.</strong> Confirmation ${orderNumber}.`);
}

function attachEvents() {
  elements.search.addEventListener("input", (event) => {
    state.query = event.target.value.trim();
    renderResults();
  });

  elements.clearSearch.addEventListener("click", () => {
    state.query = "";
    elements.search.value = "";
    renderResults();
    setStatus("Search cleared.");
  });

  document.addEventListener("click", (event) => {
    const target = event.target;
    if (!(target instanceof HTMLElement)) {
      return;
    }
    const addButton = target.closest("[data-add-item]");
    if (addButton instanceof HTMLElement) {
      addToCart(addButton.dataset.addItem);
    }
  });

  elements.startCheckout.addEventListener("click", openCheckout);
  elements.closeCheckout.addEventListener("click", closeCheckout);
  elements.closeCheckoutButton.addEventListener("click", closeCheckout);
  elements.submitOrder.addEventListener("click", placeOrder);
}

function init() {
  renderQuickPicks();
  renderResults();
  renderCart();
  renderCheckout();
  attachEvents();
}

init();
