"""TUI interface for MSProf Agent using Textual."""

import asyncio
from typing import Any

from rich.markdown import Markdown as RichMarkdown
from rich.align import Align
from rich.console import RenderableType
from rich.text import Text
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, VerticalScroll, Vertical
from textual.reactive import reactive
from textual.screen import Screen
from textual.widgets import (
    Button,
    Footer,
    Header,
    Input,
    Label,
    LoadingIndicator,
    Static,
    TextArea,
)
from textual.binding import Binding

from .agent import Agent
from .config import config_manager


class MessageWidget(Container):
    """Widget to display a chat message."""
    
    DEFAULT_CSS = """
    MessageWidget {
        layout: horizontal;
        height: auto;
        margin-bottom: 1;
        padding: 0 1;
    }
    
    .gutter {
        width: 3;
        color: $accent;
        text-style: bold;
    }

    .content-container {
        width: 1fr;
        height: auto;
    }

    .header-row {
        layout: horizontal;
        height: 1;
        width: 100%;
        margin-bottom: 0;
    }

    .role-label {
        color: $text-muted;
        text-style: bold;
        width: 1fr;
    }

    .actions {
        width: auto;
        display: none;  /* Hidden by default, could toggle on click/hover if supported */
    }
    
    MessageWidget:hover .actions {
        display: block;
    }

    .action-btn {
        background: transparent;
        border: none;
        color: $text-muted;
        min-width: 6;
        height: 1;
        padding: 0;
        margin-left: 1;
    }
    
    .action-btn:hover {
        color: $accent;
        text-style: bold;
        background: transparent;
    }

    .content-area {
        height: auto;
        min-height: 1;
        color: $text;
    }
    
    #render {
        height: auto;
    }
    
    .raw-editor {
        height: auto;
        max-height: 20;
        border: solid $accent;
    }
    
    .hidden {
        display: none;
    }

    /* Role specific styles */
    .user-gutter { color: $accent; }
    .assistant-gutter { color: $success; }
    .tool-gutter { color: $warning; }
    .system-gutter { color: $secondary; }
    """
    
    def __init__(self, role: str, content: str, **kwargs: Any):
        self.role = role
        self.content = content
        super().__init__(**kwargs)
    
    def compose(self) -> ComposeResult:
        # Determine icon
        icon = "•"
        if self.role == "user":
            icon = ">"
        elif self.role == "tool":
            icon = "🔧"
        elif self.role == "system":
            icon = "!"
            
        gutter_class = f"{self.role}-gutter"
        
        yield Label(icon, classes=f"gutter {gutter_class}")
        
        with Container(classes="content-container"):
            # Header with hidden actions
            with Horizontal(classes="header-row"):
                # yield Label(self.role.title(), classes="role-label")
                yield Static(" ", classes="role-label") # Spacer mostly, keeping it minimal
                with Horizontal(classes="actions"):
                    yield Button("Copy", id="copy-btn", classes="action-btn")
                    yield Button("Raw", id="raw-btn", classes="action-btn")
            
            # Content
            yield Static(RichMarkdown(self.content), id="render", classes="content-area")
            yield TextArea(self.content, id="raw", read_only=True, classes="raw-editor hidden")

    def update_content(self, content: str) -> None:
        """Update the message content."""
        self.content = content
        self.query_one("#render", Static).update(RichMarkdown(content))
        self.query_one("#raw", TextArea).text = content

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "copy-btn":
            self.app.copy_to_clipboard(self.content)
            self.app.notify("Copied to clipboard", severity="information")
        elif event.button.id == "raw-btn":
            render_widget = self.query_one("#render", Static)
            raw_widget = self.query_one("#raw", TextArea)
            btn = event.button
            
            if "hidden" in raw_widget.classes:
                raw_widget.remove_class("hidden")
                render_widget.add_class("hidden")
                btn.label = "View"
            else:
                raw_widget.add_class("hidden")
                render_widget.remove_class("hidden")
                btn.label = "Raw"


class ChatWelcomeBanner(Static):
    """Small welcome banner in chat."""
    
    DEFAULT_CSS = """
    ChatWelcomeBanner {
        border: solid $accent;
        padding: 1 2;
        margin: 1 0 2 0;
        background: $surface;
        color: $text;
        height: auto;
        width: 100%;
    }
    """
    
    def render(self) -> str:
        return "✱ MSProf Agent initialized. How can I help you?"


class CustomFooter(Static):
    """Custom footer with shortcuts."""
    
    DEFAULT_CSS = """
    CustomFooter {
        dock: bottom;
        height: 1;
        width: 100%;
        background: $surface;
        color: $text-muted;
        padding: 0 1; 
    }
    """
    
    def render(self) -> str:
        return "! for bash mode • / for commands • tab to undo • ⏎ for newline"


class ChatArea(VerticalScroll):
    """Area to display chat messages."""
    
    DEFAULT_CSS = """
    ChatArea {
        scrollbar-gutter: stable;
    }
    """
    
    def compose(self) -> ComposeResult:
        # We start empty now, message added upon initialization
        yield from []
    
    async def add_message(self, role: str, content: str) -> MessageWidget:
        """Add a message to the chat area."""
        widget = MessageWidget(role, content)
        await self.mount(widget)
        widget.scroll_visible()
        return widget


class InputArea(Container):
    """Area for user input."""
    
    DEFAULT_CSS = """
    InputArea {
        height: auto;
        min-height: 3;
        margin: 1 0;
        border: solid #6e7a8e;
        padding: 0;
        background: $surface;
    }
    
    InputArea:focus-within {
        border: solid $accent;
    }
    
    .input-row {
        align-vertical: middle;
        height: auto;
    }
    
    .prompt-label {
        width: 2;
        padding-left: 1;
        color: $accent;
        text-style: bold;
        align-vertical: middle;
    }
    
    Input {
        width: 1fr;
        background: transparent;
        border: none;
        padding: 0 1;
        height: 1;
    }
    
    Input:focus {
        border: none;
    }
    """
    
    def compose(self) -> ComposeResult:
        with Horizontal(classes="input-row"):
            yield Label(">", classes="prompt-label")
            yield Input(placeholder='Type your message...', id="message-input")


class WelcomeScreen(Screen):
    """Full screen welcome page."""
    
    CSS = """
    WelcomeScreen {
        align: center middle;
        background: $background;
    }
    
    .welcome-container {
        width: 80%;
        height: auto;
        align: center middle;
    }
    
    .welcome-box {
        border: solid $accent;
        padding: 1 2;
        width: auto;
        color: $text;
        background: $surface;
        margin-bottom: 2;
    }
    
    .ascii-art {
        color: $accent;
        text-align: center;
        margin-bottom: 4;
        width: 100%;
    }
    
    .continue-text {
        color: $text-muted;
        text-align: left;
    }
    
    .key-highlight {
        color: $text;
        text-style: bold;
    }
    """
    
    BINDINGS = [
        Binding("enter", "continue", "Continue"),
    ]
    
    def compose(self) -> ComposeResult:
        ascii_text = """
███    ███  ██████  ██████  ██████   ██████  ██████
████  ████ ██      ██   ██ ██   ██ ██    ██ ██
██ ████ ██ ███████ ██████  ██████  ██    ██ █████
██  ██  ██      ██ ██      ██   ██ ██    ██ ██
██      ██ ██████  ██      ██   ██  ██████  ██

       █████   ██████  ███████ ███    ██ ████████
      ██   ██ ██       ██      ████   ██    ██   
      ███████ ██   ███ █████   ██ ██  ██    ██   
      ██   ██ ██    ██ ██      ██  ██ ██    ██   
      ██   ██  ██████  ███████ ██   ████    ██   
        """
        
        with Vertical(classes="welcome-container"):
            yield Label("✱ Welcome to MSProf Agent", classes="welcome-box")
            yield Static(ascii_text, classes="ascii-art")
            
            t = Text.from_markup("Press [bold white]Enter[/bold white] to continue")
            yield Label(t, classes="continue-text")
            
    def action_continue(self) -> None:
        self.app.push_screen(ChatScreen())


class ChatScreen(Screen):
    """Main chat interface."""
    
    BINDINGS = [
        Binding("ctrl+c", "quit", "Quit", show=False),
        Binding("ctrl+l", "clear", "Clear Chat", show=False),
    ]
    
    def compose(self) -> ComposeResult:
        with Container(id="main-container"):
            with ChatArea(id="chat-area"):
                pass
            yield InputArea()
        yield CustomFooter()

    async def on_mount(self) -> None:
        """Called when screen is mounted."""
        # Check if agent is already initialized in app
        agent = self.app.agent
        
        # We can trigger a small welcome message in the chat
        chat_area = self.query_one("#chat-area", ChatArea)
        
        if agent.is_initialized:
            chat_area.mount(ChatWelcomeBanner())
        else:
            # If not initialized (should not happen if we init in app.on_mount, but just in case)
            await chat_area.add_message("system", agent.error_message)

        # Focus input
        self.query_one("#message-input", Input).focus()

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "message-input":
            await self.send_message()
            
    async def send_message(self) -> None:
        app: MSProfApp = self.app
        if app.is_processing:
            return
            
        input_widget = self.query_one("#message-input", Input)
        message = input_widget.value.strip()
        
        if not message:
            return
            
        # Commands
        if message.lower() in ["/exit", "/quit", ":q"]:
            app.exit()
            return
        if message.lower() == "/clear":
            self.action_clear()
            input_widget.value = ""
            return
        
        input_widget.value = ""
        chat_area = self.query_one("#chat-area", ChatArea)
        await chat_area.add_message("user", message)
        chat_area.scroll_end(animate=False)
        
        if not app.agent.is_initialized:
             await chat_area.add_message("system", app.agent.error_message or "Agent not initialized")
             return

        app.is_processing = True
        try:
            # Add a placeholder for the assistant's response
            current_message_widget = await chat_area.add_message("assistant", "⠋ Thinking...")
            chat_area.scroll_end(animate=False)
            
            response_text = ""
            buffer = ""
            update_interval = 0.05
            last_update = 0
            import time

            async for chunk in app.agent.chat_stream(message):
                # If this is the start of the response, clear the "Thinking..." text
                if not response_text:
                    response_text = chunk
                    buffer = "" # Reset buffer
                    current_message_widget.update_content(response_text)
                    last_update = time.time()
                    continue
                
                buffer += chunk
                response_text += chunk
                
                # Throttle updates
                current_time = time.time()
                if current_time - last_update > update_interval:
                    current_message_widget.update_content(response_text)
                    buffer = ""
                    last_update = current_time
                    await asyncio.sleep(0)
            
            # Final update
            if buffer:
                 current_message_widget.update_content(response_text)
                 
        except Exception as e:
            await chat_area.add_message("system", f"Error: {e}")
        finally:
            app.is_processing = False

    def action_clear(self) -> None:
        self.app.agent.clear_history()
        chat_area = self.query_one("#chat-area", ChatArea)
        chat_area.remove_children()
        chat_area.mount(ChatWelcomeBanner())
        chat_area.run_worker(self._add_system_message(chat_area, "Chat history cleared."))

    async def _add_system_message(self, chat_area: ChatArea, message: str) -> None:
        await chat_area.add_message("system", message)


class MSProfApp(App):
    """MSProf Agent TUI Application."""
    
    CSS = """
    /* Theme Variables */
    $accent: #d08770;
    $success: #a3be8c;
    $warning: #ebcb8b;
    $secondary: #88c0d0;
    $background: #1e1e1e;
    $surface: #262626;
    $text: #eceff4;
    $text-muted: #6e7a8e;
    
    Screen {
        background: $background;
        color: $text;
    }
    
    #main-container {
        width: 100%;
        height: 1fr;
        padding: 1 4;
    }
    
    #chat-area {
        height: 1fr;
        margin-bottom: 1;
    }
    """
    
    def __init__(self, **kwargs: Any):
        self.agent = Agent()
        self.is_processing = False
        super().__init__(**kwargs)
        
    async def on_mount(self) -> None:
        # Initialize agent centrally
        await self.agent.initialize()
        # Push welcome screen
        self.push_screen(WelcomeScreen())


def run_tui() -> None:
    """Run the TUI application."""
    app = MSProfApp()
    app.run()
