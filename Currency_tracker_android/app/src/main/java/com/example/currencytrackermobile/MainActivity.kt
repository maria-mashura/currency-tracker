package com.example.currencyapp

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import com.example.currencyapp.network.APIClient
import com.example.currencyapp.ui.MainScreen
import com.example.currencyapp.viewmodel.RatesViewModel

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        // Создаем API клиент
        val api = APIClient.create()

        // Создаем ViewModel
        val viewModel = RatesViewModel(api)

        // Загружаем данные
        viewModel.loadRates()

        // Отображаем Compose экран
        setContent {
            MainScreen(viewModel)
        }
    }
}
