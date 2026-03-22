# pyre-ignore-all-errors
"""
Currency Exchange Module for Nova
Allows Nova to check currency exchange rates and convert currencies
"""

import asyncio  # type: ignore  # pyre-ignore
import os  # type: ignore  # pyre-ignore
from typing import Dict, Optional  # type: ignore  # pyre-ignore
from datetime import datetime, timedelta  # type: ignore  # pyre-ignore

import aiohttp  # type: ignore  # pyre-ignore

# Exchange API Configuration
def _get_exchange_api_key() -> str:
    return os.getenv("EXCHANGE_API_KEY", "")

EXCHANGE_API_KEY = _get_exchange_api_key()
EXCHANGE_API_URL_V4 = "https://api.exchangerate-api.com/v4/latest/"
EXCHANGE_API_URL_V6 = "https://v6.exchangerate-api.com/v6/{key}/latest/{base}"
FALLBACK_API_URL = "https://api.frankfurter.app/latest"


class CurrencyExchange:
    """Currency exchange and conversion functionality for Nova"""

    def __init__(self):
        self.cache: Dict[str, dict] = {}  # type: ignore  # pyre-ignore
        self.cache_duration = timedelta(hours=1)
        self.last_update: Optional[datetime] = None  # type: ignore  # pyre-ignore

    async def get_exchange_rate(self, from_currency: str, to_currency: str) -> str:  # type: ignore  # pyre-ignore
        """Get exchange rate between two currencies"""
        from_currency = from_currency.upper()
        to_currency = to_currency.upper()

        rates = await self._fetch_rates(from_currency)
        if not rates:
            return f"❌ Could not fetch exchange rates for {from_currency}"

        rate = rates.get(to_currency)
        if not rate:
            available = ", ".join(list(rates.keys())[:10]) + "..."  # type: ignore  # pyre-ignore
            return f"❌ Currency {to_currency} not found. Available: {available}"

        return f"💱 **Exchange Rate**\n\n1 {from_currency} = {rate:.4f} {to_currency}\n\n_Last updated: {self.last_update.strftime('%Y-%m-%d %H:%M') if self.last_update else 'Unknown'}_"  # type: ignore  # pyre-ignore

    async def convert_currency(self, amount: float, from_currency: str, to_currency: str) -> str:  # type: ignore  # pyre-ignore
        """Convert amount from one currency to another"""
        from_currency = from_currency.upper()
        to_currency = to_currency.upper()

        rates = await self._fetch_rates(from_currency)
        if not rates:
            return f"❌ Could not fetch exchange rates for {from_currency}"

        rate = rates.get(to_currency)
        if not rate:
            return f"❌ Currency {to_currency} not found."

        converted = amount * rate
        return f"💱 **Currency Conversion**\n\n{amount:,.2f} {from_currency} = {converted:,.2f} {to_currency}\n\n_Rate: 1 {from_currency} = {rate:.4f} {to_currency}_"

    async def get_all_rates(self, base_currency: str = "USD") -> str:  # type: ignore  # pyre-ignore
        """Get all exchange rates for a base currency"""
        base_currency = base_currency.upper()
        rates = await self._fetch_rates(base_currency)

        if not rates:
            return f"❌ Could not fetch exchange rates for {base_currency}"

        # Show top currencies
        major_currencies = ["EUR", "GBP", "JPY", "CNY", "AUD", "CAD", "CHF", "SEK", "NZD", "SGD"]
        lines = [f"💱 **Exchange Rates - {base_currency}**\n"]

        for curr in major_currencies:
            if curr in rates and curr != base_currency:
                lines.append(f"1 {base_currency} = {rates[curr]:.4f} {curr}")  # type: ignore  # pyre-ignore

        lines.append(f"\n_Total currencies available: {len(rates)}_")
        lines.append(f"_Last updated: {self.last_update.strftime('%Y-%m-%d %H:%M') if self.last_update else 'Unknown'}_")  # type: ignore  # pyre-ignore

        return "\n".join(lines)

    async def _fetch_rates(self, base: str) -> Optional[Dict[str, float]]:  # type: ignore  # pyre-ignore
        """Fetch exchange rates from API"""
        # Check cache
        if base in self.cache:
            cache_time = self.cache[base].get("timestamp")
            if cache_time and datetime.now() - cache_time < self.cache_duration:
                return self.cache[base].get("rates")

        # Try primary API
        async with aiohttp.ClientSession() as session:
            try:
                api_key = os.getenv("EXCHANGE_API_KEY", "") or EXCHANGE_API_KEY
                
                if api_key:
                    url = EXCHANGE_API_URL_V6.format(key=api_key, base=base)
                else:
                    url = f"{EXCHANGE_API_URL_V4}{base}"
                    
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status == 200:
                        data = await response.json()
                        # v6 uses conversion_rates, v4 uses rates
                        rates = data.get("conversion_rates") or data.get("rates", {})
                        self.cache[base] = {
                            "rates": rates,
                            "timestamp": datetime.now()
                        }
                        self.last_update = datetime.now()
                        return rates
            except Exception:
                pass

            # Try fallback API
            try:
                url = f"{FALLBACK_API_URL}?from={base}"
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status == 200:
                        data = await response.json()
                        rates = data.get("rates", {})
                        self.cache[base] = {
                            "rates": rates,
                            "timestamp": datetime.now()
                        }
                        self.last_update = datetime.now()
                        return rates
            except Exception:
                pass

        return None  # type: ignore  # pyre-ignore

    async def get_crypto_price(self, crypto: str, currency: str = "USD") -> str:  # type: ignore  # pyre-ignore
        """Get cryptocurrency price"""
        crypto = crypto.lower()
        currency = currency.upper()

        # Map common names
        crypto_map = {
            "bitcoin": "bitcoin",
            "btc": "bitcoin",
            "ethereum": "ethereum",
            "eth": "ethereum",
            "solana": "solana",
            "sol": "solana",
            "cardano": "cardano",
            "ada": "cardano",
        }

        coin_id = crypto_map.get(crypto, crypto)

        async with aiohttp.ClientSession() as session:
            try:
                url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies={currency.lower()}"
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status == 200:
                        data = await response.json()
                        price_data = data.get(coin_id, {})
                        price = price_data.get(currency.lower())
                        if price:
                            return f"💰 **{crypto.upper()} Price**\n\n1 {crypto.upper()} = {price:,.2f} {currency}\n\n_Source: CoinGecko_"
            except Exception:
                pass

        return f"❌ Could not fetch price for {crypto}. Try: bitcoin, ethereum, solana, etc."


# Global instance
exchange = CurrencyExchange()


# Tool functions for Nova to use
async def get_exchange_rate(from_curr: str, to_curr: str, user_id: str = "unknown") -> str:  # type: ignore  # pyre-ignore
    """Get exchange rate between two currencies"""
    return await exchange.get_exchange_rate(from_curr, to_curr)


async def convert_currency(amount: float, from_curr: str, to_curr: str, user_id: str = "unknown") -> str:  # type: ignore  # pyre-ignore
    """Convert currency amount"""
    return await exchange.convert_currency(amount, from_curr, to_curr)


async def get_rates(base: str = "USD", user_id: str = "unknown") -> str:  # type: ignore  # pyre-ignore
    """Get all exchange rates for base currency"""
    return await exchange.get_all_rates(base)


async def get_crypto(crypto: str, currency: str = "USD", user_id: str = "unknown") -> str:  # type: ignore  # pyre-ignore
    """Get cryptocurrency price"""
    return await exchange.get_crypto_price(crypto, currency)

