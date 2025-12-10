package com.example.currencytrackermobile.ui.components

package com.example.currencyapp.ui.components

import androidx.compose.material.*
import androidx.compose.runtime.*
import androidx.compose.foundation.layout.Box

@Composable
fun BankFilter(selectedBank: String, onBankSelected: (String) -> Unit) {
    var expanded by remember { mutableStateOf(false) }
    val banks = listOf("NBU", "PrivatBank", "MonoBank")

    Box {
        Button(onClick = { expanded = true }) {
            Text(selectedBank)
        }
        DropdownMenu(expanded = expanded, onDismissRequest = { expanded = false }) {
            banks.forEach { bank ->
                DropdownMenuItem(onClick = {
                    onBankSelected(bank)
                    expanded = false
                }) {
                    Text(bank)
                }
            }
        }
    }
}
