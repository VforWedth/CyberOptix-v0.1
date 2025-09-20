// Direct Address Manager - No Cache Required
// Handles user-input addresses without any dependency on cached data

class DirectAddressManager {
    constructor() {
        this.savedAddresses = this.loadSavedAddresses();
        this.commonAddresses = this.initializeCommonAddresses();
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.loadAddressHistory();
    }

    // Initialize common Myanmar addresses for suggestions
    initializeCommonAddresses() {
        return {
            states: [
                'Yangon', 'Mandalay', 'Naypyidaw', 'Shan State', 'Kachin State',
                'Kayah State', 'Kayin State', 'Chin State', 'Mon State',
                'Rakhine State', 'Ayeyarwady', 'Bago', 'Magway', 'Sagaing', 'Tanintharyi'
            ],
            cities: {
                'Yangon': [
                    'Downtown', 'Thanlyin', 'Insein', 'Dagon', 'Kamayut', 'Thingangyun',
                    'Mayangone', 'Hlaing', 'Bahan', 'Sanchaung', 'Kyauktada', 'Pabedan',
                    'Latha', 'Lanmadaw', 'Ahlone', 'Tamwe', 'Mingala Taungnyunt'
                ],
                'Mandalay': [
                    'City Center', 'Chanayethazan', 'Mahaaungmye', 'Chanmyathazi',
                    'Pyigyidagun', 'Amarapura', 'Patheingyi', 'Aungmyay Tharzan'
                ],
                'Naypyidaw': [
                    'Zabuthiri', 'Tatkon', 'Dekkhinathiri', 'Pyinmana', 'Lewe', 'Ottarathiri'
                ],
                'Shan State': [
                    'Taunggyi', 'Lashio', 'Kengtung', 'Hsipaw', 'Kalaw', 'Nyaungshwe',
                    'Muse', 'Kyaukme', 'Tangyan', 'Hopang'
                ],
                'Mon State': [
                    'Mawlamyine', 'Thaton', 'Kyaikmaraw', 'Ye', 'Mudon', 'Thanbyuzayat'
                ]
            },
            townships: {
                'Yangon': {
                    'Downtown': ['Kyauktada', 'Pabedan', 'Latha', 'Lanmadaw'],
                    'Dagon': ['Dagon Seikkan', 'North Dagon', 'South Dagon', 'East Dagon'],
                    'Kamayut': ['Kamayut', 'Hlaing', 'Mayangone'],
                    'Thingangyun': ['Thingangyun', 'Dawbon', 'Mingala Taungnyunt']
                },
                'Mandalay': {
                    'City Center': ['Chanayethazan', 'Mahaaungmye'],
                    'Chanmyathazi': ['Chanmyathazi', 'Pyigyidagun']
                }
            }
        };
    }

    setupEventListeners() {
        // Auto-suggestions for address fields
        this.setupAddressAutocomplete('delivery-state', this.commonAddresses.states);

        // Dynamic city updates based on state
        const stateField = document.getElementById('delivery-state');
        if (stateField) {
            stateField.addEventListener('input', (e) => {
                this.updateCitySuggestions(e.target.value);
            });
        }

        // Dynamic township updates based on city
        const cityField = document.getElementById('delivery-city');
        if (cityField) {
            cityField.addEventListener('input', (e) => {
                this.updateTownshipSuggestions(e.target.value);
            });
        }

        // Save address functionality
        this.setupSaveAddressFunctionality();

        // Load previous addresses
        this.setupAddressHistory();
    }

    setupAddressAutocomplete(fieldId, suggestions) {
        const field = document.getElementById(fieldId);
        if (!field) return;

        field.addEventListener('input', (e) => {
            const value = e.target.value.toLowerCase();
            const datalistId = field.getAttribute('list');
            const datalist = document.getElementById(datalistId);

            if (!datalist) return;

            // Clear existing options
            datalist.innerHTML = '';

            // Filter and add matching suggestions
            const matches = suggestions.filter(item =>
                item.toLowerCase().includes(value)
            ).slice(0, 8); // Limit to 8 suggestions

            matches.forEach(match => {
                const option = document.createElement('option');
                option.value = match;
                datalist.appendChild(option);
            });
        });
    }

    updateCitySuggestions(stateName) {
        const cityField = document.getElementById('delivery-city');
        const cityDatalist = document.getElementById('common-cities');

        if (!cityField || !cityDatalist) return;

        // Clear existing options
        cityDatalist.innerHTML = '';

        // Get cities for the selected state
        const cities = this.commonAddresses.cities[stateName] || [];

        cities.forEach(city => {
            const option = document.createElement('option');
            option.value = city;
            cityDatalist.appendChild(option);
        });

        // Also add cities from saved addresses for this state
        const savedCities = this.getSavedCitiesForState(stateName);
        savedCities.forEach(city => {
            if (!cities.includes(city)) {
                const option = document.createElement('option');
                option.value = city;
                cityDatalist.appendChild(option);
            }
        });
    }

    updateTownshipSuggestions(cityName) {
        const stateField = document.getElementById('delivery-state');
        const townshipField = document.getElementById('delivery-township');

        if (!stateField || !townshipField) return;

        const stateName = stateField.value;
        const townshipDatalist = document.getElementById('common-townships');

        if (!townshipDatalist) return;

        // Clear existing options
        townshipDatalist.innerHTML = '';

        // Get townships for the selected state and city
        const stateData = this.commonAddresses.townships[stateName];
        const townships = stateData?.[cityName] || [];

        townships.forEach(township => {
            const option = document.createElement('option');
            option.value = township;
            townshipDatalist.appendChild(option);
        });
    }

    getSavedCitiesForState(stateName) {
        return this.savedAddresses
            .filter(addr => addr.state === stateName)
            .map(addr => addr.city)
            .filter((city, index, arr) => arr.indexOf(city) === index); // Unique values
    }

    setupSaveAddressFunctionality() {
        const saveCheckbox = document.getElementById('save-address');
        if (!saveCheckbox) return;

        saveCheckbox.addEventListener('change', (e) => {
            if (e.target.checked) {
                this.showSaveAddressOptions();
            } else {
                this.hideSaveAddressOptions();
            }
        });
    }

    showSaveAddressOptions() {
        // Add address nickname field
        const saveCheckbox = document.getElementById('save-address');
        const container = saveCheckbox.closest('.form-group');

        if (container && !container.querySelector('.address-nickname')) {
            const nicknameField = document.createElement('div');
            nicknameField.className = 'address-nickname mt-2';
            nicknameField.innerHTML = `
                <label for="address-nickname" class="form-label">
                    <i class="fas fa-tag"></i> Address Nickname (optional)
                </label>
                <input type="text"
                       id="address-nickname"
                       class="form-control"
                       placeholder="e.g., Home, Office, Mom's House"
                       maxlength="50">
                <small class="form-text text-muted">
                    Give this address a name for easy selection next time
                </small>
            `;
            container.appendChild(nicknameField);
        }
    }

    hideSaveAddressOptions() {
        const nicknameField = document.querySelector('.address-nickname');
        if (nicknameField) {
            nicknameField.remove();
        }
    }

    setupAddressHistory() {
        // Add "Use Previous Address" button if saved addresses exist
        if (this.savedAddresses.length > 0) {
            this.addAddressHistorySection();
        }
    }

    addAddressHistorySection() {
        const addressSection = document.querySelector('.delivery-address-section');
        if (!addressSection) return;

        const historySection = document.createElement('div');
        historySection.className = 'address-history-section mb-3';
        historySection.innerHTML = `
            <div class="d-flex justify-content-between align-items-center mb-2">
                <h6 class="mb-0">
                    <i class="fas fa-history"></i> Previous Addresses
                </h6>
                <button type="button" class="btn btn-sm btn-outline-primary" id="toggle-address-history">
                    <i class="fas fa-chevron-down"></i> Show
                </button>
            </div>
            <div id="address-history-list" style="display: none;">
                ${this.generateAddressHistoryHTML()}
            </div>
        `;

        addressSection.insertBefore(historySection, addressSection.firstChild);

        // Setup toggle functionality
        document.getElementById('toggle-address-history')?.addEventListener('click', (e) => {
            this.toggleAddressHistory(e.target);
        });

        // Setup address selection
        this.setupAddressSelection();
    }

    generateAddressHistoryHTML() {
        return this.savedAddresses.slice(0, 5).map((addr, index) => `
            <div class="saved-address-item border rounded p-2 mb-2" data-address-index="${index}">
                <div class="d-flex justify-content-between align-items-start">
                    <div class="address-details">
                        <strong>${addr.nickname || 'Saved Address'}</strong>
                        <div class="text-muted small">
                            ${addr.state}, ${addr.city}
                            ${addr.township ? `, ${addr.township}` : ''}
                        </div>
                        ${addr.street ? `<div class="text-muted small">${addr.street}</div>` : ''}
                    </div>
                    <button type="button" class="btn btn-sm btn-primary use-address-btn">
                        <i class="fas fa-check"></i> Use
                    </button>
                </div>
            </div>
        `).join('');
    }

    toggleAddressHistory(button) {
        const historyList = document.getElementById('address-history-list');
        const icon = button.querySelector('i');

        if (historyList.style.display === 'none') {
            historyList.style.display = 'block';
            icon.className = 'fas fa-chevron-up';
            button.innerHTML = '<i class="fas fa-chevron-up"></i> Hide';
        } else {
            historyList.style.display = 'none';
            icon.className = 'fas fa-chevron-down';
            button.innerHTML = '<i class="fas fa-chevron-down"></i> Show';
        }
    }

    setupAddressSelection() {
        document.querySelectorAll('.use-address-btn').forEach(button => {
            button.addEventListener('click', (e) => {
                const addressItem = e.target.closest('.saved-address-item');
                const addressIndex = parseInt(addressItem.dataset.addressIndex);
                this.loadSavedAddress(addressIndex);
            });
        });
    }

    loadSavedAddress(index) {
        const address = this.savedAddresses[index];
        if (!address) return;

        // Fill in the form fields
        const fields = {
            'delivery-state': address.state,
            'delivery-city': address.city,
            'delivery-township': address.township || '',
            'delivery-street': address.street || '',
            'delivery-landmark': address.landmark || '',
            'delivery-instructions': address.instructions || ''
        };

        Object.entries(fields).forEach(([fieldId, value]) => {
            const field = document.getElementById(fieldId);
            if (field) {
                field.value = value;
                // Trigger input event to update suggestions
                field.dispatchEvent(new Event('input', { bubbles: true }));
            }
        });

        // Show success message
        this.showNotification('Address loaded successfully!', 'success');

        // Hide address history
        const toggleButton = document.getElementById('toggle-address-history');
        if (toggleButton) {
            this.toggleAddressHistory(toggleButton);
        }
    }

    saveAddress(addressData, nickname = '') {
        const addressToSave = {
            ...addressData,
            nickname: nickname || this.generateAddressNickname(addressData),
            savedAt: new Date().toISOString()
        };

        // Check if similar address already exists
        const existingIndex = this.findSimilarAddress(addressData);

        if (existingIndex !== -1) {
            // Update existing address
            this.savedAddresses[existingIndex] = addressToSave;
        } else {
            // Add new address to the beginning
            this.savedAddresses.unshift(addressToSave);
        }

        // Keep only last 10 addresses
        if (this.savedAddresses.length > 10) {
            this.savedAddresses = this.savedAddresses.slice(0, 10);
        }

        this.persistSavedAddresses();
        return true;
    }

    findSimilarAddress(addressData) {
        return this.savedAddresses.findIndex(saved =>
            saved.state === addressData.state &&
            saved.city === addressData.city &&
            saved.township === addressData.township
        );
    }

    generateAddressNickname(addressData) {
        const timestamp = new Date().toLocaleDateString();
        return `${addressData.city}, ${addressData.state} (${timestamp})`;
    }

    loadSavedAddresses() {
        try {
            return JSON.parse(localStorage.getItem('direct_saved_addresses') || '[]');
        } catch (error) {
            console.error('Error loading saved addresses:', error);
            return [];
        }
    }

    persistSavedAddresses() {
        try {
            localStorage.setItem('direct_saved_addresses', JSON.stringify(this.savedAddresses));
        } catch (error) {
            console.error('Error saving addresses:', error);
        }
    }

    // Address validation methods
    validateAddress(addressData) {
        const errors = [];

        if (!addressData.state || addressData.state.trim().length < 2) {
            errors.push('State/Region must be at least 2 characters');
        }

        if (!addressData.city || addressData.city.trim().length < 2) {
            errors.push('City/Town must be at least 2 characters');
        }

        // Optional but recommended fields
        const warnings = [];

        if (!addressData.street || addressData.street.trim().length < 5) {
            warnings.push('Consider adding more specific street address details');
        }

        if (!addressData.landmark) {
            warnings.push('Adding a nearby landmark can help with delivery');
        }

        return {
            isValid: errors.length === 0,
            errors,
            warnings,
            completeness: this.calculateAddressCompleteness(addressData)
        };
    }

    calculateAddressCompleteness(addressData) {
        const fields = ['state', 'city', 'township', 'street', 'landmark'];
        const filledFields = fields.filter(field =>
            addressData[field] && addressData[field].trim().length > 0
        );

        return Math.round((filledFields.length / fields.length) * 100);
    }

    // Shipping calculation based on address
    calculateShippingCost(addressData) {
        const state = addressData.state.toLowerCase();

        // Define shipping zones
        const shippingZones = {
            major_cities: ['yangon', 'mandalay', 'naypyidaw'],
            urban_areas: ['mon state', 'bago', 'ayeyarwady'],
            remote_areas: ['shan state', 'kachin state', 'chin state', 'kayah state', 'kayin state']
        };

        let shippingCost = 5; // Default cost

        if (shippingZones.major_cities.some(city => state.includes(city))) {
            shippingCost = 3;
        } else if (shippingZones.urban_areas.some(area => state.includes(area))) {
            shippingCost = 4;
        } else if (shippingZones.remote_areas.some(area => state.includes(area))) {
            shippingCost = 8;
        }

        // Adjust based on city (if it's a major city in any state)
        const city = addressData.city.toLowerCase();
        const majorCityKeywords = ['city center', 'downtown', 'central', 'main'];

        if (majorCityKeywords.some(keyword => city.includes(keyword))) {
            shippingCost = Math.max(shippingCost - 1, 2);
        }

        return {
            cost: shippingCost,
            zone: this.getShippingZone(state),
            estimatedDays: this.getEstimatedDeliveryDays(state)
        };
    }

    getShippingZone(state) {
        const state_lower = state.toLowerCase();

        if (['yangon', 'mandalay', 'naypyidaw'].some(city => state_lower.includes(city))) {
            return 'Major Cities';
        } else if (['mon state', 'bago', 'ayeyarwady'].some(area => state_lower.includes(area))) {
            return 'Urban Areas';
        } else if (['shan state', 'kachin state', 'chin state'].some(area => state_lower.includes(area))) {
            return 'Remote Areas';
        }

        return 'Standard Zone';
    }

    getEstimatedDeliveryDays(state) {
        const state_lower = state.toLowerCase();

        if (['yangon', 'mandalay'].some(city => state_lower.includes(city))) {
            return '1-2 days';
        } else if (state_lower.includes('naypyidaw')) {
            return '2-3 days';
        } else if (['shan state', 'kachin state', 'chin state'].some(area => state_lower.includes(area))) {
            return '5-7 days';
        }

        return '3-5 days';
    }

    // Helper methods
    showNotification(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
        notification.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';

        notification.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;

        document.body.appendChild(notification);

        // Auto-remove after 3 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, 3000);
    }

    clearAddressForm() {
        const addressFields = [
            'delivery-state', 'delivery-city', 'delivery-township',
            'delivery-street', 'delivery-landmark', 'delivery-instructions'
        ];

        addressFields.forEach(fieldId => {
            const field = document.getElementById(fieldId);
            if (field) {
                field.value = '';
            }
        });
    }

    exportAddressHistory() {
        const dataStr = JSON.stringify(this.savedAddresses, null, 2);
        const dataBlob = new Blob([dataStr], {type: 'application/json'});

        const link = document.createElement('a');
        link.href = URL.createObjectURL(dataBlob);
        link.download = 'address_history.json';
        link.click();
    }

    importAddressHistory(file) {
        const reader = new FileReader();
        reader.onload = (e) => {
            try {
                const importedAddresses = JSON.parse(e.target.result);
                if (Array.isArray(importedAddresses)) {
                    this.savedAddresses = [...importedAddresses, ...this.savedAddresses];
                    this.persistSavedAddresses();
                    this.showNotification('Addresses imported successfully!', 'success');
                }
            } catch (error) {
                this.showNotification('Error importing addresses', 'error');
            }
        };
        reader.readAsText(file);
    }
}

// Export for use in other modules
window.DirectAddressManager = DirectAddressManager;

// Auto-initialize if DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.directAddressManager = new DirectAddressManager();
    });
} else {
    window.directAddressManager = new DirectAddressManager();
}