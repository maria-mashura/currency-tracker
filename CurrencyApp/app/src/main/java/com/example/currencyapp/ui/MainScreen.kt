package com.example.currencyapp.ui

import androidx.compose.foundation.layout.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.example.currencyapp.ui.components.BankFilter
import com.example.currencyapp.ui.components.CurrencyFilter
import com.example.currencyapp.ui.components.RatesTable
import com.example.currencyapp.viewmodel.RatesViewModel

@Composable
fun MainScreen(viewModel: RatesViewModel) {
    Column(modifier = Modifier.fillMaxSize().padding(16.dp)) {
        BankFilter(selectedBank = viewModel.selectedBank) {
            viewModel.selectedBank = it
            viewModel.loadRates()
        }
        Spacer(modifier = Modifier.height(8.dp))
        CurrencyFilter(selectedCurrency = viewModel.selectedCurrency) {
            viewModel.selectedCurrency = it
        }
        Spacer(modifier = Modifier.height(16.dp))
        RatesTable(rates = viewModel.rates.filter { it.currency == viewModel.selectedCurrency })
    }
}
