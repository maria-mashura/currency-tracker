package com.example.currencyapp.viewmodel

import androidx.compose.runtime.*
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.example.currencyapp.network.RatesApi
import com.example.currencyapp.network.Rate
import kotlinx.coroutines.launch

class RatesViewModel(private val api: RatesApi) : ViewModel() {

    var rates by mutableStateOf<List<Rate>>(emptyList())
        private set

    var selectedCurrency by mutableStateOf("USD")
    var selectedBank by mutableStateOf("NBU")

    fun loadRates() {
        viewModelScope.launch {
            rates = if (selectedBank == "NBU") api.getNbuRates() else api.getBankRates()
        }
    }
}
