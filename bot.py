# research_agent/bot.py
import os
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # Continue without dotenv functionality
    pass
import streamlit as st
from phi.agent import Agent, RunResponse
from phi.tools.duckduckgo import DuckDuckGo
from phi.tools.serper import Serper
from phi.tools.google import Google
from phi.tools.browser import Browser
from phi.llm.groq import Groq

# Initialize Streamlit page
st.set_page_config(
    page_title="Research Agent",
    page_icon="🔍",
    layout="wide",
)

# Add styling
st.markdown("""
<style>
.main {
    background-color: #f5f7f9;
}
.stApp {
    max-width: 1200px;
    margin: 0 auto;
}
.stTextInput > div > div > input {
    border-radius: 8px;
}
.stButton > button {
    border-radius: 8px;
    background-color: #4CAF50;
    color: white;
    font-weight: bold;
}
</style>
""", unsafe_allow_html=True)

st.title("🔍 Research Agent")
st.markdown("Your AI-powered research assistant. Ask any question to get comprehensive answers with sources.")

# Initialize session state for conversation history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Get API keys
groq_api_key = os.getenv("GROQ_API_KEY")
serper_api_key = os.getenv("SERPER_API_KEY")
google_api_key = os.getenv("GOOGLE_API_KEY")
google_cse_id = os.getenv("GOOGLE_CSE_ID")

# API key inputs for user
with st.sidebar:
    st.header("API Keys")
    user_groq_api_key = st.text_input("Groq API Key", value=groq_api_key if groq_api_key else "", type="password")
    user_serper_api_key = st.text_input("Serper API Key (Optional)", value=serper_api_key if serper_api_key else "", type="password")
    user_google_api_key = st.text_input("Google API Key (Optional)", value=google_api_key if google_api_key else "", type="password")
    user_google_cse_id = st.text_input("Google CSE ID (Optional)", value=google_cse_id if google_cse_id else "", type="password")
    
    st.markdown("---")
    st.markdown("### Research Settings")
    search_engine = st.selectbox(
        "Search Engine",
        ["DuckDuckGo", "Serper", "Google"],
        index=0
    )
    
    num_results = st.slider("Number of search results", min_value=3, max_value=10, value=5)
    browse_results = st.checkbox("Browse search results for more details", value=True)
    
    model = st.selectbox(
        "LLM Model",
        ["llama3-70b-8192", "llama3-8b-8192", "mixtral-8x7b-32768", "gemma-7b-it"],
        index=0
    )

# Function to create the agent
def create_research_agent():
    # Set up search tool based on selection
    if search_engine == "DuckDuckGo":
        search_tool = DuckDuckGo(num_results=num_results)
    elif search_engine == "Serper" and user_serper_api_key:
        search_tool = Serper(api_key=user_serper_api_key, num_results=num_results)
    elif search_engine == "Google" and user_google_api_key and user_google_cse_id:
        search_tool = Google(api_key=user_google_api_key, cse_id=user_google_cse_id, num_results=num_results)
    else:
        # Fallback to DuckDuckGo if API keys are missing
        search_tool = DuckDuckGo(num_results=num_results)
    
    tools = [search_tool]
    
    # Add browser tool if selected
    if browse_results:
        tools.append(Browser())
    
    # Create agent with Groq LLM
    llm = Groq(model=model, api_key=user_groq_api_key) if user_groq_api_key else None
    
    agent = Agent(
        tools=tools,
        llm=llm,
        system_prompt="""You are an expert research assistant, designed to help users find comprehensive answers to their questions 
        by searching the internet, analyzing search results, and providing relevant information.
        
        When given a question, you will:
        1. Search for the most relevant and recent information
        2. Browse pages when necessary to get detailed information
        3. Synthesize your findings into a well-structured answer
        4. Provide sources for all information in your response
        5. Be objective, thorough, and helpful
        
        Always cite your sources with the full URL in [text](URL) format at the end of your response.
        If you're unable to find information, admit what you don't know and suggest alternative approaches.
        """
    )
    
    return agent

# User input
user_query = st.chat_input("What would you like to research?")

if user_query:
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": user_query})
    with st.chat_message("user"):
        st.markdown(user_query)
    
    # Create agent and get response
    if not user_groq_api_key:
        assistant_response = "Please provide a Groq API key in the sidebar to use the research agent."
    else:
        with st.chat_message("assistant"):
            with st.spinner("Researching your question..."):
                try:
                    agent = create_research_agent()
                    response_container = st.empty()
                    full_response = ""
                    
                    # Process agent response in streaming fashion
                    for chunk in agent.run_stream(user_query):
                        if isinstance(chunk, RunResponse):
                            full_response = chunk.response
                            response_container.markdown(full_response)
                    
                    assistant_response = full_response
                except Exception as e:
                    st.error(f"Error: {str(e)}")
                    assistant_response = f"Sorry, I encountered an error while researching: {str(e)}"
    
    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": assistant_response})

# Footer
st.markdown("---")
st.markdown("Powered by Phi, Groq, and various search tools.")
