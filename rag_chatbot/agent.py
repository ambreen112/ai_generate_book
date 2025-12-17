"""
RAG Agent using OpenRouter for chat completion with strict instructions to use retrieve tool first.
"""
import os
from openai import OpenAI
from vector_store import retrieve
from dotenv import load_dotenv
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize OpenRouter client for chat
openrouter_client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY")
)

def run_agent(question: str, selected_text: str = ""):
    """
    Run the RAG agent with the given question and optional selected text.
    The agent is instructed to always call the retrieve function first.

    Args:
        question (str): The question to answer
        selected_text (str): Optional selected text from the book (highest priority context)

    Returns:
        dict: The agent's response
    """
    # Prepare the system prompt with strict instructions
    system_prompt = """You are a helpful assistant for a book. You must ALWAYS:
    1. FIRST call the retrieve tool to get relevant context from the book
    2. Prioritize any selected_text provided by the user
    3. Use ONLY the retrieved context to answer questions
    4. NEVER hallucinate or make up information
    5. Always provide sources for the information you use in your answers
    6. If the context doesn't contain the answer, clearly state that the information is not in the knowledge base"""

    # Prepare messages for the chat
    messages = [
        {"role": "system", "content": system_prompt}
    ]

    # Include selected text if provided
    if selected_text and selected_text.strip():
        messages.append({
            "role": "user",
            "content": f"Selected text (HIGHEST PRIORITY): {selected_text}\n\nQuestion: {question}"
        })
    else:
        messages.append({
            "role": "user",
            "content": f"Question: {question}"
        })

    try:
        # Call OpenRouter with function calling enabled
        response = openrouter_client.chat.completions.create(
            model="openai/gpt-4o-mini",  # Using GPT-4o-mini as requested
            messages=messages,
            tools=[{
                "type": "function",
                "function": {
                    "name": "retrieve",
                    "description": "Retrieve relevant documents from the vector store based on the query and selected text. Always call this first before answering.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "The main question to search for"},
                            "selected_text": {"type": "string", "description": "Optional selected/highlighted text from the book (higher priority)"}
                        },
                        "required": ["query"]
                    }
                }
            }],
            tool_choice="required",  # Force the model to use the retrieve tool
            temperature=0.1,
            max_tokens=1000
        )

        # Extract the tool call from the response
        tool_calls = response.choices[0].message.tool_calls
        if tool_calls:
            for tool_call in tool_calls:
                if tool_call.function.name == "retrieve":
                    # Parse the arguments
                    import json
                    args = json.loads(tool_call.function.arguments)

                    # Call the retrieve function
                    context = retrieve(args.get("query", question), args.get("selected_text", selected_text))

                    # Now create a final response based on the retrieved context
                    final_messages = [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": f"Question: {question}"},
                        {"role": "assistant", "content": f"Retrieved context: {context}"},
                        {"role": "user", "content": "Based on the retrieved context, please answer the original question."}
                    ]

                    final_response = openrouter_client.chat.completions.create(
                        model="openai/gpt-4o-mini",
                        messages=final_messages,
                        temperature=0.1,
                        max_tokens=1000
                    )

                    answer = final_response.choices[0].message.content
                    return {
                        "answer": answer,
                        "sources": extract_sources(context)
                    }
        else:
            # If no tool call was made, return an error message
            return {
                "answer": "I was unable to retrieve relevant information from the book. The assistant did not call the retrieve function as expected.",
                "sources": []
            }

    except Exception as e:
        logger.error(f"Error in agent: {e}")
        return {
            "answer": f"I'm sorry, but I encountered an error processing your request: {str(e)}",
            "sources": []
        }

def extract_sources(context: str) -> list:
    """
    Extract sources from the context string.

    Args:
        context (str): The context string containing sources

    Returns:
        list: List of source filenames
    """
    if "Sources:" in context and "]" in context:
        try:
            sources_str = context.split("Sources:")[1].strip()
            if sources_str.startswith("[") and "]" in sources_str:
                sources_str = sources_str.split("[")[1].split("]")[0]
            sources = [s.strip().strip("'\"") for s in sources_str.split(",") if s.strip()]
            return sources
        except:
            pass

    # Alternative: look for [Source: filename] patterns
    import re
    source_matches = re.findall(r'\[Source: ([^\]]+)\]', context)
    return list(set(source_matches))  # Remove duplicates

if __name__ == "__main__":
    # Test run of the agent
    test_question = "What are the key concepts in this book?"
    test_selected_text = ""  # Example of how selected text would be passed

    print("Testing the agent with a sample question...")
    response = run_agent(test_question, test_selected_text)
    print(f"Response: {response}")