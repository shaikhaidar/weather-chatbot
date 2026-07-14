import re

class IntentType:
    GREETING = "GREETING"
    GRAPH_REQUEST = "GRAPH_REQUEST"
    DATA_QUERY = "DATA_QUERY"
    GENERAL_CHAT = "GENERAL_CHAT"

class DecisionEngine:
    @staticmethod
    def determine_intent(user_message: str) -> str:
        """
        Uses fast heuristic/keyword mapping to classify the user's intent.
        This ensures high-performance routing on Edge devices.
        """
        message_lower = user_message.lower().strip()
        
        # 1. Greeting Intent
        greetings = ["hi", "hello", "hey", "good morning", "good evening", "howdy"]
        if message_lower in greetings or any(message_lower.startswith(g + " ") for g in greetings):
            return IntentType.GREETING
            
        # 2. Graph/Plotting Intent
        graph_keywords = ["plot", "graph", "chart", "visualize", "draw"]
        if any(keyword in message_lower for keyword in graph_keywords):
            return IntentType.GRAPH_REQUEST
            
        # 3. Data Query Intent
        data_keywords = ["data", "predict", "temperature", "wind", "humidity", "weather", "rmse", "feature"]
        if any(keyword in message_lower for keyword in data_keywords):
            return IntentType.DATA_QUERY
            
        # 4. Fallback General Chat
        return IntentType.GENERAL_CHAT
