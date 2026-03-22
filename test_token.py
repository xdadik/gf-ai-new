# pyre-ignore-all-errors
import asyncio  # type: ignore  # pyre-ignore
from telegram import Bot  # type: ignore  # pyre-ignore

async def main():
    token = "8793304035:AAFpR5hZKUpOaSz1aQUduZRFTMNZCmiUhXk"
    print(f"Testing token: {token}")
    bot = Bot(token)
    me = await bot.get_me()
    print("Bot Name:", me.first_name)
    try:
        # this will throw 409 if the token is being actively polled elsewhere
        updates = await bot.get_updates(timeout=2)
        print("Success! Got updates:", len(updates))
    except Exception as e:
        print("ERROR:", type(e).__name__, "-", e)

if __name__ == "__main__":
    asyncio.run(main())

