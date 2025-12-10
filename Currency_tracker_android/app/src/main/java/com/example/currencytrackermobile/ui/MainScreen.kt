package com.example.currencytrackermobile.ui

package com.example.currencyapp.ui

import androidx.compose.foundation.layout.*
import androidx.compose.material.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.example.currencyapp.ui.components.BankFilter
import com.example.currencyapp.ui.components.CurrencyFilter
import com.example.currencyapp.ui.components.RatesTable
import com.example.currencyapp.viewmodel.RatesViewModel

@Composable
fun MainScreen(viewModel: RatesViewModel) {

    // Column — вертикальный слой
    Column(modifier = Modifier.fillMaxSize().padding(16.dp)) {

        // Фильтр по банкам
        BankFilter(selectedBank = viewModel.selectedBank) {
            viewModel.selectedBank = it
            viewModel.loadRates() // обновляем курсы при смене банка
        }

        Spacer(modifier = Modifier.height(8.dp))

        // Фильтр по валютам
        CurrencyFilter(selectedCurrency = viewModel.selectedCurrency) {
            viewModel.selectedCurrency = it
            // Можно добавить локальную фильтрацию, чтобы показывать только выбранную валюту
        }

        Spacer(modifier = Modifier.height(16.dp))

        // Таблица курсов
        RatesTable(
            rates = viewModel.rates.filter { it.currency == viewModel.selectedCurrency }
        )
    }
}
