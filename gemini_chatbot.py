import os
import google.generativeai as genai
from typing import List, Dict
from dotenv import load_dotenv
import warnings

# Suppress the FutureWarning about google.generativeai deprecation
warnings.filterwarnings('ignore', category=FutureWarning, module='google.generativeai')

# Load environment variables from .env file
load_dotenv()

class GeminiChatbot:
    def __init__(self, api_key: str = None):
        """
        Initialize the Gemini chatbot.
        
        Args:
            api_key: Your Gemini API key. If not provided, it will look for GEMINI_API_KEY in environment variables.
        """
        if api_key is None:
            api_key = os.getenv('GEMINI_API_KEY')
            if api_key is None:
                raise ValueError("API key must be provided or set in GEMINI_API_KEY environment variable")
        
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('models/gemini-2.5-flash')
        self.chat = self.model.start_chat(history=[])
        self.conversation_history: List[Dict[str, str]] = []
    
    def send_message(self, message: str) -> str:
        """
        Send a message to the chatbot and get a response.
        
        Args:
            message: The user's message
            
        Returns:
            The chatbot's response
        """
        try:
            response = self.chat.send_message(message)
            response_text = response.text
            
            # Store in conversation history
            self.conversation_history.append({
                'role': 'user',
                'content': message
            })
            self.conversation_history.append({
                'role': 'assistant',
                'content': response_text
            })
            
            return response_text
        except Exception as e:
            return f"Error: {str(e)}"
    
    def get_history(self) -> List[Dict[str, str]]:
        """Get the conversation history."""
        return self.conversation_history
    
    def clear_history(self):
        """Clear the conversation history and start a new chat."""
        self.chat = self.model.start_chat(history=[])
        self.conversation_history = []
        print("Conversation history cleared!")


def main():
    """Main function to run the chatbot in terminal."""
    print("=" * 50)
    print("Gemini Chatbot")
    print("=" * 50)
    print("Type 'quit' or 'exit' to end the conversation")
    print("Type 'clear' to clear conversation history")
    print("Type 'history' to view conversation history")
    print("=" * 50)
    
    # Initialize chatbot
    try:
        # You can pass your API key here directly or set it as an environment variable
        # chatbot = GeminiChatbot(api_key="YOUR_API_KEY_HERE")
        chatbot = GeminiChatbot()
    except ValueError as e:
        print(f"\n{e}")
        print("\nPlease either:")
        print("1. Set GEMINI_API_KEY environment variable")
        print("2. Or edit this file and pass your API key directly to GeminiChatbot()")
        return
    
    print("\nChatbot is ready! Start chatting...\n")
    
    # Chat loop
    while True:
        # Get user input
        user_input = input("You: ").strip()
        
        # Check for exit commands
        if user_input.lower() in ['quit', 'exit']:
            print("\nGoodbye! 👋")
            break
        
        # Check for clear command
        if user_input.lower() == 'clear':
            chatbot.clear_history()
            continue
        
        # Check for history command
        if user_input.lower() == 'history':
            history = chatbot.get_history()
            if not history:
                print("\nNo conversation history yet.\n")
            else:
                print("\n--- Conversation History ---")
                for entry in history:
                    role = "You" if entry['role'] == 'user' else "Bot"
                    print(f"{role}: {entry['content']}\n")
                print("--- End of History ---\n")
            continue
        
        # Skip empty messages
        if not user_input:
            continue
        
        # Get response from chatbot
        response = chatbot.send_message(user_input)
        print(f"Bot: {response}\n")


if __name__ == "__main__":
    main()
