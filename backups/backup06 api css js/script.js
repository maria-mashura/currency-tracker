let ratesData = [];
let bankOptionsInitialized = false;
let sortState = {};

// Обработчик фильтров
function onFilterChange() {
    displayTables();
}

async function loadRates() {
    try {
        const response = await fetch('http://127.0.0.1:8000/rates/latest');
        const data = await response.json();

        // фильтруем RUB и кросс-курсы Монобанка
        ratesData = (data.rates || []).filter(r => {
            const cur = (r.currency || "").trim().toUpperCase();
            if (cur === "RUB") return false;
            if (r.bank === "Monobank" && Number(r.buy) < 10) return false;
            return true;
        });

        if (!bankOptionsInitialized) {
            const bankSet = new Set(ratesData.map(r => r.bank).filter(Boolean));
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
    } catch (err) {
        console.error('Error loading rates', err);
    }
}

function displayTables() {
    const currencyFilter = document.getElementById('currencyFilter').value;
    const bankFilter = document.getElementById('bankFilter').value;

    let filtered = ratesData;
    if (currencyFilter !== "ALL") filtered = filtered.filter(r => (r.currency||"").toUpperCase() === currencyFilter);
    if (bankFilter !== "ALL") filtered = filtered.filter(r => r.bank === bankFilter);

    const latestMap = {};
    filtered.forEach(rate => {
        const key = `${rate.bank}__${(rate.currency||"").toUpperCase()}`;
        const ts = parseDateToTs(rate.date);
        if (!latestMap[key] || ts > latestMap[key]._ts) {
            latestMap[key] = {...rate, _ts: ts};
        }
    });

    const latestArray = Object.values(latestMap).map(r => {
        const copy = {...r};
        delete copy._ts;
        return copy;
    });

    const bestBuy = {};
    const worstSell = {};
    latestArray.forEach(rate => {
        const cur = (rate.currency||"").toUpperCase();
        if (!bestBuy[cur] || rate.buy > bestBuy[cur]) bestBuy[cur] = rate.buy;
        if (!worstSell[cur] || rate.sell < worstSell[cur]) worstSell[cur] = rate.sell;
    });

    const tbodyCurrent = document.querySelector('#currentRates tbody');
    tbodyCurrent.innerHTML = '';
    latestArray.forEach(rate => {
        const row = document.createElement('tr');
        const buyVal = Number(rate.buy) || 0;
        const sellVal = Number(rate.sell) || 0;
        row.setAttribute('data-bank', rate.bank || "");
        row.setAttribute('data-currency', (rate.currency||"").toUpperCase());
        row.setAttribute('data-buy', buyVal);
        row.setAttribute('data-sell', sellVal);
        row.setAttribute('data-date', parseDateToTs(rate.date));
        row.innerHTML = `
            <td>${escapeHtml(rate.bank || "")}</td>
            <td>${escapeHtml((rate.currency||"").toUpperCase())}</td>
            <td class="${buyVal === bestBuy[(rate.currency||"").toUpperCase()] ? 'best-buy' : ''}">${buyVal.toFixed(2)}</td>
            <td class="${sellVal === worstSell[(rate.currency||"").toUpperCase()] ? 'best-sell' : ''}">${sellVal.toFixed(2)}</td>
            <td>${escapeHtml(rate.date || "")}</td>
        `;
        tbodyCurrent.appendChild(row);
    });

    const tbodyHist = document.querySelector('#historicalRates tbody');
    tbodyHist.innerHTML = '';
    filtered.forEach(rate => {
        const row = document.createElement('tr');
        const buyVal = Number(rate.buy) || 0;
        const sellVal = Number(rate.sell) || 0;
        row.setAttribute('data-bank', rate.bank || "");
        row.setAttribute('data-currency', (rate.currency||"").toUpperCase());
        row.setAttribute('data-buy', buyVal);
        row.setAttribute('data-sell', sellVal);
        row.setAttribute('data-date', parseDateToTs(rate.date));
        row.innerHTML = `
            <td>${escapeHtml(rate.bank || "")}</td>
            <td>${escapeHtml((rate.currency||"").toUpperCase())}</td>
            <td>${buyVal.toFixed(2)}</td>
            <td>${sellVal.toFixed(2)}</td>
            <td>${escapeHtml(rate.date || "")}</td>
        `;
        tbodyHist.appendChild(row);
    });
}

// Парсинг даты в timestamp
function parseDateToTs(dateStr) {
    if (!dateStr) return 0;
    try {
        return new Date(dateStr.replace(' ', 'T')).getTime();
    } catch { return 0; }
}

// Сортировка
function sortTable(tableId, keys) {
    const table = document.getElementById(tableId);
    const rows = Array.from(table.tBodies[0].rows);
    const stateKey = `${tableId}::${keys.join(',')}`;
    const asc = sortState[stateKey] === undefined ? true : !sortState[stateKey];
    sortState[stateKey] = asc;

    rows.sort((a,b) => {
        for (const key of keys) {
            let valA = a.getAttribute(`data-${key}`) || "";
            let valB = b.getAttribute(`data-${key}`) || "";
            const numA = Number(valA), numB = Number(valB);
            if (!isNaN(numA) && !isNaN(numB)) {
                if (numA !== numB) return asc ? numA - numB : numB - numA;
            } else {
                const sA = valA.toLowerCase(), sB = valB.toLowerCase();
                if (sA !== sB) return asc ? sA.localeCompare(sB) : sB.localeCompare(sA);
            }
        }
        return 0;
    });

    rows.forEach(r => table.tBodies[0].appendChild(r));
    table.querySelectorAll('th').forEach(th => th.classList.remove('asc','desc'));
    const headerCells = table.tHead.rows[0].cells;
    for (let th of headerCells) {
        if (th.getAttribute('data-key') === keys[0]) {
            th.classList.add(asc ? 'asc' : 'desc');
            break;
        }
    }
}

// Простая защита от XSS
function escapeHtml(text) {
    if (!text) return "";
    return text.replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;');
}

// Запуск
loadRates();
setInterval(loadRates, 60000);
