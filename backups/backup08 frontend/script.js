let ratesData = [];
let sortState = {};
let bankOptionsInitialized = false;

async function loadRates() {
    try {
        const response = await fetch('http://127.0.0.1:8000/rates/latest');
        const data = await response.json();
        ratesData = data.rates;

        if (!bankOptionsInitialized) {
            const bankSet = new Set(ratesData.filter(r => r.bank !== "NBU").map(r => r.bank));
            const bankSelect = document.getElementById('bankFilter');
            bankSet.forEach(bank => {
                const opt = document.createElement('option');
                opt.value = bank;
                opt.textContent = bank;
                bankSelect.appendChild(opt);
            });
            bankOptionsInitialized = true;
        }

        displayTables();
    } catch(e) {
        console.error("Error loading rates", e);
    }
}

function onFilterChange() {
    displayTables();
}

function displayTables() {
    const currencyFilter = document.getElementById('currencyFilter').value;
    const bankFilter = document.getElementById('bankFilter').value;

    // --- NBU Table ---
const nbu = ["USD","EUR"].map(cur => {
    const r = ratesData
                .filter(r => r.bank === "NBU")
                .find(r => r.currency === cur);
    if(r) return r;
    return {bank:"NBU", currency:cur, buy:0, sell:0, date:""}; // если данных нет
});

const tbodyNBU = document.querySelector('#nbuRates tbody');
tbodyNBU.innerHTML = '';
nbu.forEach(r => {
    const row = document.createElement('tr');
    row.innerHTML = `<td>${r.bank}</td><td>${r.currency}</td><td>${r.buy.toFixed(2)}</td><td>${r.sell.toFixed(2)}</td><td>${r.date}</td>`;
    tbodyNBU.appendChild(row);
});


    // --- Current Bank Rates ---
    let currentBanks = ratesData.filter(r => r.bank !== "NBU")
                                .filter(r => currencyFilter === "ALL" || r.currency === currencyFilter)
                                .filter(r => bankFilter === "ALL" || r.bank === bankFilter);

    // Оставляем только USD и EUR для каждого банка
    const latestMap = {};
    currentBanks.forEach(rate => {
        const key = rate.bank + '__' + rate.currency;
        const ts = new Date(rate.date).getTime();
        if (!latestMap[key] || ts > new Date(latestMap[key].date).getTime()) {
            latestMap[key] = rate;
        }
    });
    currentBanks = Object.values(latestMap);

    // Подсветка выгодного курса
    const bestBuy = {}, worstSell = {};
    currentBanks.forEach(r => {
        const cur = r.currency;
        if (!bestBuy[cur] || r.buy > bestBuy[cur]) bestBuy[cur] = r.buy;
        if (!worstSell[cur] || r.sell < worstSell[cur]) worstSell[cur] = r.sell;
    });

    const tbodyCurrent = document.querySelector('#currentRates tbody');
    tbodyCurrent.innerHTML = '';
    currentBanks.forEach(r => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${r.bank}</td>
            <td>${r.currency}</td>
            <td class="${r.buy === bestBuy[r.currency] ? 'best-buy' : ''}">${r.buy.toFixed(2)}</td>
            <td class="${r.sell === worstSell[r.currency] ? 'best-sell' : ''}">${r.sell.toFixed(2)}</td>
            <td>${r.date}</td>
        `;
        tbodyCurrent.appendChild(row);
    });

    // --- Historical Table ---
    let hist = ratesData.filter(r => currencyFilter === "ALL" || r.currency === currencyFilter)
                        .filter(r => r.bank === "NBU" || bankFilter === "ALL" || r.bank === bankFilter);

    const tbodyHist = document.querySelector('#historicalRates tbody');
    tbodyHist.innerHTML = '';
    hist.forEach(r => {
        const row = document.createElement('tr');
        row.innerHTML = `<td>${r.bank}</td><td>${r.currency}</td><td>${r.buy.toFixed(2)}</td><td>${r.sell.toFixed(2)}</td><td>${r.date}</td>`;
        tbodyHist.appendChild(row);
    });
}

// Сортировка таблицы Current Bank Rates
function sortTable(tableId, keys) {
    const table = document.getElementById(tableId);
    const tbody = table.tBodies[0];
    const rows = Array.from(tbody.rows);
    if (!rows.length) return;

    const stateKey = tableId + '::' + keys.join(',');
    const asc = !(sortState[stateKey] ?? true);
    sortState[stateKey] = asc;

    rows.sort((a,b) => {
        for(const k of keys){
            let valA = a.cells[table.querySelectorAll('th[data-key]').findIndex(th=>th.dataset.key===k)].innerText;
            let valB = b.cells[table.querySelectorAll('th[data-key]').findIndex(th=>th.dataset.key===k)].innerText;
            const numA = parseFloat(valA), numB = parseFloat(valB);
            if(!isNaN(numA) && !isNaN(numB)) {
                if(numA!==numB) return asc ? numA-numB : numB-numA;
            } else {
                if(valA!==valB) return asc ? valA.localeCompare(valB) : valB.localeCompare(valA);
            }
        }
        return 0;
    });

    rows.forEach(r => tbody.appendChild(r));

    table.querySelectorAll('th').forEach(th => th.classList.remove('asc','desc'));
    const th = table.querySelector(`th[data-key="${keys[0]}"]`);
    if(th) th.classList.add(asc ? 'asc' : 'desc');
}

loadRates();
setInterval(loadRates, 60*1000);
