package com.example.currencyapp.network

data class Rate(
    val currency: String,
    val buy: Double,
    val sell: Double,
    val date: String
)
