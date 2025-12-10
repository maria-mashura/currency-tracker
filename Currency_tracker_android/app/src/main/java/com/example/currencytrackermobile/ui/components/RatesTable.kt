package com.example.currencytrackermobile.ui.components

package com.example.currencyapp.ui.components

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.example.currencyapp.network.Rate

@Composable
fun RatesTable(rates: List<Rate>) {
    LazyColumn {
        items(rates) { rate ->
            Row(
                modifier = Modifier.fillMaxWidth().padding(8.dp),
                horizontalArrangement = Arrangement.SpaceBetween
            ) {
                Text(rate.currency)
                Text(rate.buy.toString())
                Text(rate.sell.toString())
            }
        }
    }
}
