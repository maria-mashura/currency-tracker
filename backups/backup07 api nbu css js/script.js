let ratesData = [];
let sortState = {};
let bankOptionsInitialized = false;

// --- Фильтры ---
function onFilterChange() {
    displayTables();
}

// --- Fetch ---
async function loadRates() {
    try {
        const res = await fetch('http://127.0.0.1:8000/rates/latest');
        const data = await res.json();
        ratesData = data.rates || [];

        // --- Обработка НБУ: берем только USD/EUR, один курс на валюту ---
        const nbuRatesMap = {};
        ratesData.forEach(r => {
            if (r.bank === 'NBU' && (r.currency === 'USD' || r.currency === 'EUR')) {
                nbuRatesMap[r.currency] = r; // сохраняем только последний курс по валюте
            }
        });
        // удаляем старые НБУ и оставляем только актуальный курс USD/EUR
        ratesData = ratesData.filter(r => r.bank !== 'NBU');
        ratesData.push(...Object.values(nbuRatesMap));

        displayTables();
    } catch (err) {
        console.error('Error loading rates', err);
    }
}

// --- Display Tables ---
function displayTables() {
    displayNbuTable();
    displayBankTable();
    displayHistoryTable();
}

// --- NBU Table ---
function displayNbuTable() {
    const tbody = document.querySelector('#nbuRates tbody');
    tbody.innerHTML = '';

    const nbuRates = ratesData.filter(r => r.bank === 'NBU');
    const currencyFilter = document.getElementById('currencyFilter').value;
    nbuRates.forEach(rate => {
        if (currencyFilter !== 'ALL' && rate.currency !== currencyFilter) return;
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${rate.bank}</td>
            <td>${rate.currency}</td>
            <td>${rate.buy.toFixed(2)}</td>
            <td>${rate.sell.toFixed(2)}</td>
            <td>${rate.date}</td>
        `;
        tbody.appendChild(row);
    });
}

// --- Bank Table ---
function displayBankTable() {
    const currencyFilter = document.getElementById('currencyFilter').value;
    const bankFilter = document.getElementById('bankFilter').value;

    // Только банки, Monobank без кросс-курсов
    let filtered = ratesData.filter(r => r.bank !== 'NBU');
    filtered = filtered.filter(r => {
        if (r.bank === 'Monobank' && r.buy < 10) return false; // убираем кросс-курс
        return true;
    });
    if (currencyFilter !== 'ALL') filtered = filtered.filter(r => r.currency === currencyFilter);
    if (bankFilter !== 'ALL') filtered = filtered.filter(r => r.bank === bankFilter);

    // Заполняем фильтр банков один раз
    if (!bankOptionsInitialized) {
        const bankSet = new Set(filtered.map(r => r.bank));
        const bankSelect = document.getElementById('bankFilter');
        bankSet.forEach(bank => {
            const opt = document.createElement('option');
            opt.value = bank;
            opt.textContent = bank;
            bankSelect.appendChild(opt);
        });
        bankOptionsInitialized = true;
    }

    // --- Current Rates: берем только 2 строки на банк (USD/EUR)
    const latestMap = {};
    filtered.forEach(rate => {
        const key = `${rate.bank}__${rate.currency}`;
        const ts = new Date(rate.date).getTime();
        if (!latestMap[key] || ts > latestMap[key]._ts) {
            latestMap[key] = Object.assign({}, rate);
            latestMap[key]._ts = ts;
        }
    });
    const latestArray = Object.values(latestMap);

    // подсветка лучших курсов
    const bestBuy = {};
    const worstSell = {};
    latestArray.forEach(rate => {
        const cur = rate.currency;
        if (!bestBuy[cur] || rate.buy > bestBuy[cur]) bestBuy[cur] = rate.buy;
        if (!worstSell[cur] || rate.sell < worstSell[cur]) worstSell[cur] = rate.sell;
    });

    const tbody = document.querySelector('#currentRates tbody');
    tbody.innerHTML = '';
    latestArray.forEach(rate => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${rate.bank}</td>
            <td>${rate.currency}</td>
            <td class="${rate.buy === bestBuy[rate.currency] ? 'best-buy' : ''}">${rate.buy.toFixed(2)}</td>
            <td class="${rate.sell === worstSell[rate.currency] ? 'best-sell' : ''}">${rate.sell.toFixed(2)}</td>
            <td>${rate.date}</td>
        `;
        tbody.appendChild(row);
    });
}

// --- History Table ---
function displayHistoryTable() {
    const tbody = document.querySelector('#historicalRates tbody');
    tbody.innerHTML = '';

    const currencyFilter = document.getElementById('currencyFilter').value;
    const history = ratesData.filter(r =>
        r.bank === 'PrivatBank' || r.bank === 'Monobank' || r.bank === 'NBU'
    );
    history.sort((a,b) => new Date(b.date) - new Date(a.date));

    history.forEach(rate => {
        if (currencyFilter !== 'ALL' && rate.currency !== currencyFilter) return;
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${rate.bank}</td>
            <td>${rate.currency}</td>
            <td>${rate.buy.toFixed(2)}</td>
            <td>${rate.sell.toFixed(2)}</td>
            <td>${rate.date}</td>
        `;
        tbody.appendChild(row);
    });
}

// --- Start ---
loadRates();
setInterval(loadRates, 60*1000);
