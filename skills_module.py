# pyre-ignore-all-errors
"""
Comprehensive Skills Module for Lily
Adds many advanced capabilities to the AI
"""

import asyncio  # type: ignore  # pyre-ignore
import os  # type: ignore  # pyre-ignore
import re  # type: ignore  # pyre-ignore
import json  # type: ignore  # pyre-ignore
import random  # type: ignore  # pyre-ignore
import hashlib  # type: ignore  # pyre-ignore
from datetime import datetime, timedelta  # type: ignore  # pyre-ignore
from typing import Dict, List, Optional, Any  # type: ignore  # pyre-ignore
from urllib.parse import quote, unquote  # type: ignore  # pyre-ignore

import aiohttp  # type: ignore  # pyre-ignore


class LilySkills:
    """Advanced skills for Lily AI"""

    def __init__(self):
        self.jokes_cache = []
        self.quotes_cache = []
        self.facts_cache = []
        self.last_joke_fetch = None

    # ==================== ENTERTAINMENT ====================

    async def tell_joke(self, category: str = "any") -> str:  # type: ignore  # pyre-ignore
        """Tell a random joke"""
        jokes = {
            "programming": [
                "Why do programmers prefer dark mode? Because light attracts bugs! 🐛",
                "How many programmers does it take to change a light bulb? None, that's a hardware problem! 💡",
                "Why did the programmer quit his job? Because he didn't get arrays! 😄",
                "What's a programmer's favorite place? The Foo Bar! 🍺",
                "Why do Java developers wear glasses? Because they don't C#! 👓",
            ],
            "general": [
                "Why don't scientists trust atoms? Because they make up everything! ⚛️",
                "What do you call a fake noodle? An impasta! 🍝",
                "Why did the scarecrow win an award? He was outstanding in his field! 🌾",
                "What do you call a bear with no teeth? A gummy bear! 🐻",
                "Why did the bicycle fall over? It was two tired! 🚲",
            ],
            "flirty": [
                "Are you a magician? Because whenever I look at you, everyone else disappears! ✨",
                "Do you have a map? I keep getting lost in your eyes! 🗺️",
                "Are you WiFi? Because I'm feeling a connection! 📶",
                "Is your name Google? Because you have everything I've been searching for! 🔍",
                "Are you a camera? Every time I look at you, I smile! 📸",
            ]
        }
        
        category = category.lower() if category != "any" else random.choice(list(jokes.keys()))
        if category not in jokes:
            category = "general"
        
        return f"😄 **Here's a joke for you:**\n\n{random.choice(jokes[category])}"  # type: ignore  # pyre-ignore

    async def get_quote(self, category: str = "inspirational") -> str:  # type: ignore  # pyre-ignore
        """Get an inspirational or themed quote"""
        quotes = {
            "inspirational": [
                "The only way to do great work is to love what you do. - Steve Jobs 💫",
                "Believe you can and you're halfway there. - Theodore Roosevelt 🌟",
                "The future belongs to those who believe in the beauty of their dreams. - Eleanor Roosevelt ✨",
                "Success is not final, failure is not fatal: it is the courage to continue that counts. - Winston Churchill 💪",
                "The best time to plant a tree was 20 years ago. The second best time is now. - Chinese Proverb 🌳",
            ],
            "love": [
                "Love is composed of a single soul inhabiting two bodies. - Aristotle 💕",
                "The best thing to hold onto in life is each other. - Audrey Hepburn 💑",
                "I saw that you were perfect, and so I loved you. Then I saw that you were not perfect and I loved you even more. - Angelita Lim 💝",
                "You are my sun, my moon, and all my stars. - E.E. Cummings 🌟",
                "In all the world, there is no heart for me like yours. In all the world, there is no love for you like mine. - Maya Angelou 💗",
            ],
            "success": [
                "Success usually comes to those who are too busy to be looking for it. - Henry David Thoreau 🏆",
                "Don't be afraid to give up the good to go for the great. - John D. Rockefeller 💼",
                "I find that the harder I work, the more luck I seem to have. - Thomas Jefferson 🍀",
                "Success is not how high you have climbed, but how you make a positive difference to the world. - Roy T. Bennett 🌍",
                "The secret of success is to do the common thing uncommonly well. - John D. Rockefeller Jr. 🔑",
            ]
        }
        
        category = category.lower() if category in quotes else "inspirational"
        return f"📜 **Quote of the moment:**\n\n{random.choice(quotes[category])}"  # type: ignore  # pyre-ignore

    async def get_fun_fact(self) -> str:  # type: ignore  # pyre-ignore
        """Get a random fun fact"""
        facts = [
            "Honey never spoils. Archaeologists have found 3,000-year-old honey in Egyptian tombs that was still edible! 🍯",
            "Octopuses have three hearts, blue blood, and nine brains! 🐙",
            "A day on Venus is longer than a year on Venus! 🌟",
            "Bananas are berries, but strawberries aren't! 🍌",
            "The human brain can generate about 23 watts of power - enough to power a light bulb! 💡",
            "Cows have best friends and get stressed when separated from them! 🐄",
            "The shortest war in history was between Britain and Zanzibar on August 27, 1896. Zanzibar surrendered after 38 minutes! ⚔️",
            "A group of flamingos is called a 'flamboyance'! 🦩",
            "The Eiffel Tower can be 15 cm taller during the summer due to heat expansion! 🗼",
            "Wombat poop is cube-shaped! 💩",
        ]
        return f"🤓 **Did you know?**\n\n{random.choice(facts)}"

    # ==================== UTILITY ====================

    async def calculate(self, expression: str) -> str:  # type: ignore  # pyre-ignore
        """Calculate mathematical expression"""
        try:
            # Safe evaluation - only allow basic math
            allowed_chars = set('0123456789+-*/.() ** % ')
            if not all(c in allowed_chars for c in expression):
                return "❌ Invalid characters in expression. Only numbers and + - * / ** % allowed."
            
            result = eval(expression, {"__builtins__": {}}, {})
            return f"🧮 **Calculation:**\n{expression} = {result}"
        except Exception as e:
            return f"❌ Calculation error: {e}"

    async def roll_dice(self, sides: int = 6, count: int = 1) -> str:  # type: ignore  # pyre-ignore
        """Roll dice"""
        if sides < 1 or sides > 1000:
            return "❌ Dice sides must be between 1 and 1000"
        if count < 1 or count > 100:
            return "❌ Dice count must be between 1 and 100"
        
        rolls = [random.randint(1, sides) for _ in range(count)]
        total = sum(rolls)
        
        if count == 1:
            return f"🎲 Rolled a d{sides}: **{rolls[0]}**"  # type: ignore  # pyre-ignore
        else:
            return f"🎲 Rolled {count}d{sides}:\n{rolls}\n**Total: {total}**"

    async def flip_coin(self) -> str:  # type: ignore  # pyre-ignore
        """Flip a coin"""
        result = random.choice(["Heads", "Tails"])
        emoji = "🟡" if result == "Heads" else "⚪"
        return f"🪙 Coin flip: **{result}** {emoji}"

    async def generate_password(self, length: int = 16, include_symbols: bool = True) -> str:  # type: ignore  # pyre-ignore
        """Generate secure password"""
        import string  # type: ignore  # pyre-ignore
        
        if length < 8 or length > 128:
            return "❌ Password length must be between 8 and 128"
        
        chars = string.ascii_letters + string.digits
        if include_symbols:
            chars += "!@#$%^&*()_+-=[]{}|;:,.<>?"  # type: ignore  # pyre-ignore
        
        password = ''.join(random.choice(chars) for _ in range(length))
        strength = "Strong" if length >= 12 and include_symbols else "Medium"
        
        return f"🔐 **Generated Password** ({strength}):\n`{password}`\n\n_Copy and store securely!_"

    async def shorten_url(self, url: str) -> str:  # type: ignore  # pyre-ignore
        """Shorten URL using is.gd"""
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        try:
            api_url = f"https://is.gd/create.php?format=simple&url={quote(url)}"
            async with aiohttp.ClientSession() as session:
                async with session.get(api_url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status == 200:
                        short_url = await response.text()
                        return f"🔗 **URL Shortened:**\nOriginal: {url}\nShort: {short_url}"
        except Exception as e:
            return f"❌ Could not shorten URL: {e}"

    # ==================== TIME & WEATHER ====================

    async def get_time_in(self, location: str) -> str:  # type: ignore  # pyre-ignore
        """Get time in a specific location"""
        # This would need a timezone API in production
        timezones = {
            "new york": "America/New_York",
            "london": "Europe/London",
            "paris": "Europe/Paris",
            "tokyo": "Asia/Tokyo",
            "sydney": "Australia/Sydney",
            "dubai": "Asia/Dubai",
            "moscow": "Europe/Moscow",
            "beijing": "Asia/Shanghai",
            "mumbai": "Asia/Kolkata",
        }
        
        location_lower = location.lower()
        if location_lower in timezones:
            from datetime import datetime  # type: ignore  # pyre-ignore
            import pytz  # type: ignore  # pyre-ignore
            try:
                tz = pytz.timezone(timezones[location_lower])
                time = datetime.now(tz).strftime("%I:%M %p (%H:%M)")  # type: ignore  # pyre-ignore
                date = datetime.now(tz).strftime("%A, %B %d, %Y")  # type: ignore  # pyre-ignore
                return f"🌍 **Time in {location.title()}:**\n{time}\n{date}"
            except:
                return f"🌍 **Time in {location.title()}:**\nUse online time converter for accurate time"
        
        return f"🌍 Time lookup for '{location}' - consider using worldtimebuddy.com"

    async def countdown_to(self, event: str, date_str: str) -> str:  # type: ignore  # pyre-ignore
        """Create countdown to an event"""
        try:
            # Parse date (expecting format: YYYY-MM-DD)
            target = datetime.strptime(date_str, "%Y-%m-%d")
            now = datetime.now()
            diff = target - now
            
            if diff.days < 0:
                return f"📅 **{event}** already passed!"
            
            days = diff.days
            hours = diff.seconds // 3600
            minutes = (diff.seconds % 3600) // 60
            
            return f"⏰ **Countdown to {event}:**\n{days} days, {hours} hours, {minutes} minutes"
        except:
            return "❌ Use format: YYYY-MM-DD (e.g., 2024-12-25)"

    # ==================== KNOWLEDGE ====================

    async def define_word(self, word: str) -> str:  # type: ignore  # pyre-ignore
        """Get definition of a word"""
        # In production, use a dictionary API
        definitions = {
            "love": "An intense feeling of deep affection. 💕",
            "success": "The accomplishment of an aim or purpose. 🏆",
            "happiness": "The state of being happy. 😊",
            "dream": "A cherished aspiration, ambition, or ideal. ✨",
            "friend": "A person whom one knows and with whom one has a bond of mutual affection. 🤝",
        }
        
        word_lower = word.lower()
        if word_lower in definitions:
            return f"📚 **{word.title()}:**\n{definitions[word_lower]}"  # type: ignore  # pyre-ignore
        
        return f"📚 Definition for '{word}' - check dictionary.com or use an online dictionary API"

    async def translate_text(self, text: str, target_lang: str = "en") -> str:  # type: ignore  # pyre-ignore
        """Simple translation (placeholder - needs actual translation API)"""
        # This is a placeholder - real implementation needs Google Translate API or similar
        return f"🌐 Translation from/to {target_lang.upper()}:\n'${text}'\n\n_(Requires Google Translate API key)_"

    async def analyze_sentiment(self, text: str) -> str:  # type: ignore  # pyre-ignore
        """Simple sentiment analysis"""
        positive_words = ['love', 'great', 'amazing', 'wonderful', 'fantastic', 'happy', 'good', 'best', 'awesome', 'perfect']
        negative_words = ['hate', 'terrible', 'awful', 'bad', 'worst', 'sad', 'angry', 'horrible', 'disgusting']
        
        text_lower = text.lower()
        pos_count = sum(1 for word in positive_words if word in text_lower)
        neg_count = sum(1 for word in negative_words if word in text_lower)
        
        if pos_count > neg_count:
            return f"😊 **Sentiment:** Positive ({pos_count} positive indicators)"
        elif neg_count > pos_count:
            return f"😔 **Sentiment:** Negative ({neg_count} negative indicators)"
        else:
            return f"😐 **Sentiment:** Neutral"

    # ==================== GAMES ====================

    async def play_number_guess(self, guess: int = None, max_num: int = 100) -> str:  # type: ignore  # pyre-ignore
        """Number guessing game"""
        # Store game state would need persistence
        if guess is None:
            return f"🎮 **Number Guessing Game**\nI'm thinking of a number between 1 and {max_num}. What's your guess?\n\nUse: guess number [your guess]"  # type: ignore  # pyre-ignore
        
        return f"🎮 You guessed: {guess}"

    async def play_rps(self, choice: str) -> str:  # type: ignore  # pyre-ignore
        """Rock Paper Scissors game"""
        choices = ["rock", "paper", "scissors"]
        choice = choice.lower()
        
        if choice not in choices:
            return "❌ Choose: rock, paper, or scissors"
        
        bot_choice = random.choice(choices)
        
        # Determine winner
        beats = {"rock": "scissors", "paper": "rock", "scissors": "paper"}
        
        emojis = {"rock": "🪨", "paper": "📄", "scissors": "✂️"}
        
        if choice == bot_choice:
            result = "🤝 It's a tie!"
        elif beats[choice] == bot_choice:  # type: ignore  # pyre-ignore
            result = "🎉 You win!"
        else:
            result = "😄 I win!"
        
        return f"🎮 **Rock Paper Scissors**\nYou: {emojis[choice]} {choice.title()}\nMe: {emojis[bot_choice]} {bot_choice.title()}\n\n{result}"  # type: ignore  # pyre-ignore


# Global instance
lily_skills = LilySkills()


# Tool functions for Lily
async def tell_joke(category: str = "any", user_id: str = "unknown") -> str:  # type: ignore  # pyre-ignore
    return await lily_skills.tell_joke(category)


async def get_quote(category: str = "inspirational", user_id: str = "unknown") -> str:  # type: ignore  # pyre-ignore
    return await lily_skills.get_quote(category)


async def get_fun_fact(user_id: str = "unknown") -> str:  # type: ignore  # pyre-ignore
    return await lily_skills.get_fun_fact()


async def calculate(expression: str, user_id: str = "unknown") -> str:  # type: ignore  # pyre-ignore
    return await lily_skills.calculate(expression)


async def roll_dice(sides: int = 6, count: int = 1, user_id: str = "unknown") -> str:  # type: ignore  # pyre-ignore
    return await lily_skills.roll_dice(sides, count)


async def flip_coin(user_id: str = "unknown") -> str:  # type: ignore  # pyre-ignore
    return await lily_skills.flip_coin()


async def generate_password(length: int = 16, include_symbols: bool = True, user_id: str = "unknown") -> str:  # type: ignore  # pyre-ignore
    return await lily_skills.generate_password(length, include_symbols)


async def play_rps(choice: str, user_id: str = "unknown") -> str:  # type: ignore  # pyre-ignore
    return await lily_skills.play_rps(choice)


async def analyze_sentiment(text: str, user_id: str = "unknown") -> str:  # type: ignore  # pyre-ignore
    return await lily_skills.analyze_sentiment(text)

