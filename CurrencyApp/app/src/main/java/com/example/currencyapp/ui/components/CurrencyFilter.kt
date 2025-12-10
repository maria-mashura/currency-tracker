package com.example.currencyapp.ui.components

import androidx.compose.material.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.foundation.layout.Box

@Composable
fun CurrencyFilter(selectedCurrency: String, onCurrencySelected: (String) -> Unit) {
    var expanded by remember { mutableStateOf(false) }
    val currencies = listOf("USD", "EUR", "GBP", "UAH")

    Box {
        Button(onClick = { expanded = true }) {
            Text(selectedCurrency)
        }
        DropdownMenu(expanded = expanded, onDismissRequest = { expanded = false }) {
            currencies.forEach { currency ->
                DropdownMenuItem(onClick = {
                    onCurrencySelected(currency)
                    expanded = false
                }) {
                    Text(currency)
                }
            }
        }
    }
}
