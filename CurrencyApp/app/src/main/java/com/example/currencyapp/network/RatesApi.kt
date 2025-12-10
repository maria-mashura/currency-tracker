package com.example.currencyapp.network

import retrofit2.http.GET

interface RatesApi {
    @GET("nbu/rates")
    suspend fun getNbuRates(): List<Rate>

    @GET("banks/rates")
    suspend fun getBankRates(): List<Rate>
}
