# research_agent/bot.py
import os
from dotenv import load_dotenv
import streamlit as st
from phi.agent import Agent, RunResponse
from phi.tools.duckduckgo import DuckDuckGo
from phi.model.groq import Groq
import requests  # Import requests for fetching news articles
# Import the fetch_trending_articles function
from news import fetch_trending_articles

# Load environment variables from .env file
load_dotenv()
# Set up API keys
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
NEWS_API_KEY = os.getenv("NEWS_API_KEY")  # Add your News API key

# Validate API keys
if not GROQ_API_KEY:
    raise ValueError("Missing required GROQ API key. Please check your .env file.")
if not NEWS_API_KEY:
    raise ValueError("Missing required News API key. Please check your .env file.")

# Initialize Groq model
groq_model = Groq(
    id="llama-3.3-70b-versatile",
    api_key=GROQ_API_KEY
)

def create_search_agent():
    # DuckDuckGo Agent with news functionality
    ddg_agent = Agent(
        tools=[DuckDuckGo()],
        model=groq_model,
        markdown=True,
        description="You are a search agent that helps users find information and news using DuckDuckGo.",
        instructions=[
            "When searching, return results in a structured format.",
            "Each result should include a title, link, and snippet.",
            "Focus on providing accurate and relevant information.",
            "If possible, return results as a list of dictionaries."
        ],
        show_tool_calls=True
    )
    
    return ddg_agent

def search_with_agent(agent, keyword) -> list:
    try:
        run: RunResponse = agent.run(f"Find detailed information and news about: {keyword}")
        
        # Check if run.content is a string (direct response)
        if isinstance(run.content, str):
            return [{
                'title': 'Search Result',
                'link': '',
                'snippet': run.content
            }]
        
        # If it's a dictionary with results
        elif isinstance(run.content, dict) and 'results' in run.content:
            return [{
                'title': item.get('title', 'No title'),
                'link': item.get('link', ''),
                'snippet': item.get('snippet', '')
            } for item in run.content['results']]
        
        # If it's a list of results
        elif isinstance(run.content, list):
            return [{
                'title': item.get('title', 'No title'),
                'link': item.get('link', ''),
                'snippet': item.get('snippet', '')
            } for item in run.content]
        
        else:
            return [{
                'title': 'Search Result',
                'link': '',
                'snippet': str(run.content)
            }]
            
    except Exception as e:
        st.error(f"Search failed: {str(e)}")
        return []

def generate_content_ideas(keywords):
    try:
        content_agent = Agent(
            model=groq_model,
            markdown=True,
            description="You are a creative content idea generator.",
            instructions=[
                "Generate engaging and creative content ideas based on keywords.",
                "Format the output in clear markdown.",
                "Be specific and actionable in your suggestions."
            ]
        )
        
        prompt = f"""Given these keywords: {', '.join(keywords)}
        Generate 5 content ideas that would be interesting and engaging.
        For each idea, provide:
        1. A catchy title
        2. A brief description
        3. At least 3 key points to cover
        
        Format the output in markdown."""
        
        run: RunResponse = content_agent.run(prompt)
        content_ideas = run.content
        
        # Generate LinkedIn post format based on content ideas
        linkedin_posts = []
        facebook_posts = []  # New list for Facebook posts
        for idea in content_ideas.split('\n\n'):  # Assuming each idea is separated by two newlines
            lines = idea.split('\n')
            title = lines[0]  # First line is the title
            description = lines[1]  # Second line is the description
            
            # Extract key points from the remaining lines
            key_points = "\n".join(lines[2:5])  # Assuming the next lines are key points
            
            # Create structured LinkedIn post
            hook_line = f"🚀 *{title}* - Grab attention with this hook!"
            interest_peak = "🔍 Let's dive deeper into this topic!"
            body = f"{description}\n\n*Key Points to Cover:*\n{key_points}\n\nThis is where you expand on the idea and provide valuable insights."
            cta = "👉 What are your thoughts? Share in the comments!"
            hashtags = "#ContentIdeas #LinkedIn #Engagement"
            
            linkedin_post = f"{hook_line}\n\n{interest_peak}\n\n{body}\n\n{cta}\n\n{hashtags}"
            linkedin_posts.append(linkedin_post)

            # Create structured Facebook post with a different style
            facebook_post = f"🌟 *{title}*\n\n{description}\n\n*Key Points:*\n{key_points}\n\n💬 We want to hear from you! What do you think about this topic? Share your thoughts in the comments below!\n\n#Facebook #Community #Engagement"
            facebook_posts.append(facebook_post)
        
        return content_ideas, linkedin_posts, facebook_posts  # Return content ideas, LinkedIn posts, and Facebook posts
    except Exception as e:
        st.error(f"Content generation failed: {str(e)}")
        return "Failed to generate content ideas.", [], []

def fetch_news_articles(keywords):
    articles = []
    for keyword in keywords:
        articles.extend(fetch_trending_articles(NEWS_API_KEY, [keyword.strip()]))
    return articles

# Set up Streamlit page config
st.set_page_config(
    page_title="Research Agent",
    page_icon="🔍",
    layout="wide"
)

# Initialize agent
ddg_agent = create_search_agent()

# Add title and description to the Streamlit app
st.title("Research Agent")
st.write("Enter keywords to search for information and news, and generate content ideas.")

# Create input field for keywords
keywords_input = st.text_area("Enter keywords (one per line)", height=100)
max_results = st.slider("Maximum results", min_value=1, max_value=10, value=5)

if st.button("Start Research"):
    if keywords_input:
        keywords = [k.strip() for k in keywords_input.split('\n') if k.strip()]
        
        with st.spinner('Searching and generating content ideas...'):
            # Create tabs for different results
            search_tab, ideas_tab, news_tab, linkedin_tab, instagram_tab, facebook_tab = st.tabs(["Search Results", "Content Ideas", "News Articles", "LinkedIn Posts", "Instagram Posts", "Facebook Posts"])
            
            # Perform searches
            search_results = []
            for keyword in keywords:
                with st.status(f"Searching for: {keyword}") as status:
                    st.write("Searching DuckDuckGo for information and news...")
                    ddg_results = search_with_agent(ddg_agent, keyword)
                    search_results.extend(ddg_results[:max_results])
                    
                    status.update(label="Search completed!", state="complete")

            # Display search results in the first tab
            with search_tab:
                if not search_results:
                    st.warning("No results found.")
                else:
                    for idx, result in enumerate(search_results, 1):
                        with st.container():
                            st.markdown(f"### Result {idx}")
                            title = result.get('title', 'No title')
                            link = result.get('link', '')
                            snippet = result.get('snippet', '')
                            
                            if title and title != 'No title':
                                st.markdown(f"{title}")
                            if link:
                                st.markdown(f"🔗 [{link}]({link})")
                            if snippet:
                                st.markdown(f"{snippet}")
                            st.divider()

            # Generate and display content ideas in the second tab
            with ideas_tab:
                content_ideas, linkedin_posts, facebook_posts = generate_content_ideas(keywords)
                st.markdown(content_ideas)

            # Display LinkedIn posts in the new LinkedIn tab
            with linkedin_tab:
                for idx, post in enumerate(linkedin_posts):
                    st.markdown(f"### LinkedIn Post {idx + 1}")
                    
                    # Display the LinkedIn post
                    st.markdown(post)
                    
                    # Create an editable text area for the LinkedIn post
                    edited_post = st.text_area(f"Edit LinkedIn Post {idx + 1}", value=post, height=200)
                    
                    # Button to save the edited post
                    if st.button(f"Save Changes for Post {idx + 1}"):
                        linkedin_posts[idx] = edited_post  # Update the post with the edited content
                        st.success(f"Post {idx + 1} updated successfully!")
                    
                    st.divider()

            # New section for Instagram posts
            with instagram_tab:
                for idx, idea in enumerate(content_ideas.split('\n\n')):  # Assuming each idea is separated by two newlines
                    lines = idea.split('\n')
                    title = lines[0]  # First line is the title
                    description = lines[1]  # Second line is the description
                    key_points = "\n".join(lines[2:5])  # Assuming the next lines are key points

                    # Create structured Instagram post with a more engaging style
                    instagram_post = f"✨ *{title}*\n\n{description}\n\n*Key Highlights:*\n{key_points}\n\n📸 Don't forget to tag us in your posts! #Instagram #ContentIdeas #Inspiration"
                    st.markdown(f"### Instagram Post {idx + 1}")
                    st.markdown(instagram_post)

                    # Create an editable text area for the Instagram post
                    edited_instagram_post = st.text_area(f"Edit Instagram Post {idx + 1}", value=instagram_post, height=200)

                    # Button to save the edited post
                    if st.button(f"Save Changes for Instagram Post {idx + 1}"):
                        st.success(f"Instagram Post {idx + 1} updated successfully!")

            # New section for Facebook posts
            with facebook_tab:
                for idx, post in enumerate(facebook_posts):
                    st.markdown(f"### Facebook Post {idx + 1}")
                    
                    # Display the Facebook post
                    st.markdown(post)
                    
                    # Create an editable text area for the Facebook post
                    edited_facebook_post = st.text_area(f"Edit Facebook Post {idx + 1}", value=post, height=200)
                    
                    # Button to save the edited post
                    if st.button(f"Save Changes for Facebook Post {idx + 1}"):
                        facebook_posts[idx] = edited_facebook_post  # Update the post with the edited content
                        st.success(f"Facebook Post {idx + 1} updated successfully!")
                    
                    st.divider()

            # Fetch and display news articles in the third tab
            with news_tab:
                news_articles = fetch_news_articles(keywords)
                if not news_articles:
                    st.warning("No news articles found.")
                else:
                    for idx, article in enumerate(news_articles, 1):
                        with st.container():
                            st.markdown(f"### News Article {idx}")
                            title = article.get('title', 'No title')
                            description = article.get('description', 'No description')
                            source = article.get('source', {}).get('name', 'Unknown Source')
                            published_at = article.get('publishedAt', 'No date provided')
                            url = article.get('url', '')

                            # Display the information
                            st.markdown(f"**Title:** {title}")
                            st.markdown(f"**Description:** {description}")
                            st.markdown(f"**Source:** {source}")
                            st.markdown(f"**Published At:** {published_at}")
                            if url:
                                st.markdown(f"[Read more here]({url})")
                            st.divider()
    else:
        st.error("Please enter at least one keyword")

# Add footer with information
st.markdown("---")
st.markdown("Built with Streamlit, Phi Framework, and Groq")
