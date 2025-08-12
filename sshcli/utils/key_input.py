import asyncio
from prompt_toolkit import PromptSession
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.application import Application
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.formatted_text import ANSI

class KeyInput():
    def __init__(self):
        self.history = InMemoryHistory()
        self.session = PromptSession(history=self.history)
    
    async def input(self, msg: str = ""):

        formatted_msg = ANSI(msg)
        return await self.async_input(formatted_msg)
    
    async def async_input(self, msg: str):

        loop = asyncio.get_event_loop()

        text = await loop.run_in_executor(None, self._get_input, msg)
        return text

    def _get_input(self, msg: str):

        return self.session.prompt(msg)


async def main():
    key_input = KeyInput()
    
    while True:
        text = await key_input.input("Enter something: ")
        print(f"You entered: {text}")
        if text.lower() == "exit":
            break


if __name__ == "__main__":
    asyncio.run(main())
