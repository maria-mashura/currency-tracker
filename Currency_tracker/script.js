let ratesData = [];
let bankOptionsInitialized = false;
let sortState = {}; 

async function loadRates() {
    try {
        const response = await fetch('http://127.0.0.1:8000/rates/latest');
        const data = await response.json();
        ratesData = data.rates || [];

        if (!bankOptionsInitialized) {
            const banks = new Set(ratesData.filter(r=>r.bank!=="NBU").map(r=>r.bank));
            const bankSelect = document.getElementById('bankFilter');
            banks.forEach(b => {
                const opt = document.createElement('option');
                opt.value = b;
                opt.textContent = b;
                bankSelect.appendChild(opt);
            });
            bankOptionsInitialized = true;
        }

        displayTables();
    } catch(e) {
        console.error("Error fetching rates", e);
    }
}

function onFilterChange() {
    displayTables();
}

function displayTables() {
    const currencyFilter = document.getElementById('currencyFilter').value;
    const bankFilter = document.getElementById('bankFilter').value;

    // --- NBU Table (только актуальные два курса) ---
    const nbu = ["USD","EUR"].map(cur => {
        const r = ratesData.filter(r=>r.bank==="NBU").find(r=>r.currency===cur);
        if(r) return r;
        return {bank:"NBU", currency:cur, buy:0, sell:0, date:""};
    });
    const tbodyNBU = document.querySelector('#nbuRates tbody');
    tbodyNBU.innerHTML = '';
    nbu.forEach(r => {
        const row = document.createElement('tr');
        row.innerHTML = `<td>${r.bank}</td><td>${r.currency}</td><td>${r.buy.toFixed(2)}</td><td>${r.sell.toFixed(2)}</td><td>${r.date}</td>`;
        tbodyNBU.appendChild(row);
    });

    let banksCurrent = ratesData.filter(r=>r.bank!=="NBU");
    if(currencyFilter!=="ALL") banksCurrent = banksCurrent.filter(r=>r.currency===currencyFilter);
    if(bankFilter!=="ALL") banksCurrent = banksCurrent.filter(r=>r.bank===bankFilter);

    const latestMap = {};
    banksCurrent.forEach(r => {
        const key = `${r.bank}__${r.currency}`;
        if(!latestMap[key] || new Date(r.date) > new Date(latestMap[key].date)) {
            latestMap[key] = r;
        }
    });
    const latestArray = Object.values(latestMap);

    const bestBuy = {}, worstSell = {};
    latestArray.forEach(r => {
        const cur = r.currency;
        if(!bestBuy[cur] || r.buy>bestBuy[cur]) bestBuy[cur]=r.buy;
        if(!worstSell[cur] || r.sell<worstSell[cur]) worstSell[cur]=r.sell;
    });

    const tbodyCurrent = document.querySelector('#currentRates tbody');
    tbodyCurrent.innerHTML = '';
    latestArray.forEach(r=>{
        const row = document.createElement('tr');
        row.innerHTML = `<td>${r.bank}</td>
            <td>${r.currency}</td>
            <td class="${r.buy===bestBuy[r.currency]?'best-buy':''}">${r.buy.toFixed(2)}</td>
            <td class="${r.sell===worstSell[r.currency]?'best-sell':''}">${r.sell.toFixed(2)}</td>
            <td>${r.date}</td>`;
        tbodyCurrent.appendChild(row);
    });

let history = ratesData;
if (currencyFilter !== "ALL") {
    history = history.filter(r => r.currency === currencyFilter);
}
if (bankFilter !== "ALL") {
    history = history.filter(r => r.bank === bankFilter);  // NBU скрывается!
}

const tbodyHist = document.querySelector('#historicalRates tbody');
tbodyHist.innerHTML = '';

history.forEach(r => {
    const row = document.createElement('tr');
    row.innerHTML = `
        <td>${r.bank}</td>
        <td>${r.currency}</td>
        <td>${r.buy.toFixed(2)}</td>
        <td>${r.sell.toFixed(2)}</td>
        <td>${r.date}</td>
    `;
    tbodyHist.appendChild(row);
});

}

function sortTable(tableId, keys){
    const table = document.getElementById(tableId);
    const tbody = table.tBodies[0];
    const rows = Array.from(tbody.rows);
    if(rows.length===0) return;

    const stateKey = `${tableId}::${keys.join(',')}`;
    const prev = sortState[stateKey];
    const asc = prev===undefined?true:!prev;
    sortState[stateKey]=asc;

    rows.sort((a,b)=>{
        for(const key of keys){
            let valA = a.querySelector(`td:nth-child(${getColIndex(table,key)+1})`).textContent;
            let valB = b.querySelector(`td:nth-child(${getColIndex(table,key)+1})`).textContent;
            const numA = Number(valA), numB=Number(valB);
            if(!isNaN(numA) && !isNaN(numB)){
                if(numA!==numB) return asc?numA-numB:numB-numA;
            } else {
                const sA=valA.toLowerCase(), sB=valB.toLowerCase();
                if(sA!==sB) return asc?sA.localeCompare(sB):sB.localeCompare(sA);
            }
        }
        return 0;
    });

    rows.forEach(r=>tbody.appendChild(r));

    // стрелки
    table.querySelectorAll('th').forEach(th=>th.classList.remove('asc','desc'));
    const th = Array.from(table.tHead.rows[0].cells).find(c=>c.getAttribute('data-key')===keys[0]);
    if(th) th.classList.add(asc?'asc':'desc');
}

function getColIndex(table,key){
    const cells = Array.from(table.tHead.rows[0].cells);
    for(let i=0;i<cells.length;i++){
        if(cells[i].getAttribute('data-key')===key) return i;
    }
    return 0;
}

// --- Старт ---
loadRates();
setInterval(loadRates,60*1000);
