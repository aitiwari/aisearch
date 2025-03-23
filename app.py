import streamlit as st
from duckduckgo_search import DDGS
from bs4 import BeautifulSoup
import requests
from youtube_transcript_api import YouTubeTranscriptApi
from groq import Groq
import re
from urllib.parse import urlparse

# Predefined News Sources (Domain names only)
# Predefined News Sources (Domain names only)
NEWS_SOURCES = {
    "General News": [
        "reuters.com", "apnews.com", "bbc.com", "nytimes.com",
        "theguardian.com", "wsj.com", "npr.org", "aljazeera.com",
        "washingtonpost.com", "dw.com", "cnn.com",
        "indianexpress.com", "hindustantimes.com", "thehindu.com",
        "ndtv.com", "timesofindia.indiatimes.com", "aajtak.intoday.in"
    ],
    "Technology": [
        "techcrunch.com", "theverge.com", "wired.com", "cnet.com",
        "arstechnica.com", "engadget.com", "gizmodo.com",
        "mashable.com", "mit.edu/technologyreview", "pcworld.com",
        "gadgets360.com", "tech2.firstpost.com", "beebom.com",
        "91mobiles.com", "smartprix.com", "varindia.com"
    ],
    "Artificial Intelligence": [
        "openai.com", "deepmind.com", "venturebeat.com",
        "analyticsindiamag.com", "aibusiness.com", 
        "syncedreview.com", "therundown.ai", 
        "thebatch.ai", "analyticsvidhya.com"
    ],
    "Business/Finance": [
        "bloomberg.com", "fortune.com", "cnbc.com",
        "financialpost.com", "economist.com", 
        "investopedia.com", "forbes.com",
        "economictimes.indiatimes.com", "business-standard.com",
        "moneycontrol.com"
    ],
    "Science": [
        "nature.com", "sciencemag.org", 
        "sciencedaily.com", 
        "nationalgeographic.com",
        "space.com", 
        "livescience.com",
        "scientificamerican.com"
    ],
    "Entertainment": [
        "variety.com", 
        "hollywoodreporter.com",
        "deadline.com",
        "ew.com",
        "billboard.com",
        "rollingstone.com",
        "vulture.com",
        "koimoi.com", "bollywoodhungama.com", "hindustantimes.com/entertainment"
    ]
}


# Set up page config
st.set_page_config(
    page_title="AI Research Assistant+",
    page_icon="🔍",
    layout="centered"
)

# Helper functions
def is_youtube_url(url):
    youtube_patterns = [
        r'^https?://(www\.)?youtube\.com/watch\?v=([^&]+)',
        r'^https?://youtu\.be/([^?]+)'
    ]
    return any(re.search(pattern, url) for pattern in youtube_patterns)

def extract_video_id(url):
    if 'youtube.com/watch' in url:
        return url.split('v=')[-1].split('&')[0]
    elif 'youtu.be/' in url:
        return url.split('/')[-1].split('?')[0]
    return None

def get_domain(url):
    parsed = urlparse(url)
    return parsed.netloc.replace("www.", "")

# Sidebar configurations
with st.sidebar:
    st.title("Configuration")
    groq_api_key = st.text_input("Enter Groq API Key:", type="password")
    groq_model = st.selectbox(
        "Choose Groq Model:",
        ["llama-3.3-70b-versatile", "qwen-qwq-32b", "deepseek-r1-distill-qwen-32b"]
    )
    search_type = st.radio(
        "Select Search Type:",
        ["Web Search", "YouTube Search", "News Search", "Image Search"]
    )
    
    # News Source Selection
    if search_type == "News Search":
        selected_categories = st.multiselect(
            "Select News Categories:",
            list(NEWS_SOURCES.keys()),
            default=["General News"],
            help="Choose news categories to search from"
        )
        
        sub_sites = []
        if selected_categories:
            # Create a flattened list of all sites from selected categories
            all_sites = []
            for category in selected_categories:
                all_sites.extend(NEWS_SOURCES[category])
            
            # Remove duplicates while preserving order
            seen = set()
            unique_sites = [site for site in all_sites if not (site in seen or seen.add(site))]
            
            sub_sites = st.multiselect(
                "Select specific sites:",
                options=unique_sites,
                help="Choose specific news websites to include"
            )
            
        
    if search_type == "Image Search":
        num_images = st.number_input(
            "Number of Images to Search",
            min_value=1,
            max_value=20,
            value=6,
            help="Choose how many images you want to search (1-20)"
        )

# Initialize Groq client

with st.sidebar:
    # API key input for Groq
    st.session_state["GROQ_API_KEY"] = st.text_input("GROQ API Key", type="password")
    st.sidebar.markdown("🔑 [Get Groq API Key](https://console.groq.com/keys)")
   
   
   # Initialize Groq client
if st.session_state["GROQ_API_KEY"]:            
    client = Groq(api_key=st.session_state["GROQ_API_KEY"])
else :
    client = Groq(api_key=os.environ.get("GROQ_API_KEY", st.secrets.get("GROQ_API_KEY", "sk-your-key")))
    
#client = Groq(api_key=groq_api_key) if groq_api_key else None

# Main app
st.title("🔍 AI Research Assistant+")
st.caption("Powered by DuckDuckGo, YouTube, News, and Groq")

# Session state management
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Dynamic input configuration
input_placeholders = {
    "Web Search": "Enter your research query...",
    "YouTube Search": "Enter YouTube URL...",
    "News Search": "Enter news topic...",
    "Image Search": "Describe images to search..."
}
user_query = st.chat_input(input_placeholders[search_type])

def process_content(content, query, model):
    return client.chat.completions.create(
        messages=[
            {"role": "system", "content": "You are a research assistant. Analyze and summarize this content:"},
            {"role": "user", "content": f"Query: {query}\nContent: {content}"}
        ],
        model=model,
    )

if user_query:
    st.session_state.messages.append({"role": "user", "content": user_query})
    
    with st.chat_message("user"):
        st.markdown(user_query)

    try:
        if search_type == "Web Search":
            # Web Search Processing
            with st.spinner("🌐 Searching web..."):
                with DDGS() as ddgs:
                    results = [r for r in ddgs.text(user_query, max_results=4)]

            if results:
                with st.expander("📄 Web Results", expanded=False):
                    for i, result in enumerate(results, 1):
                        st.write(result)
                        st.subheader(f"Result {i}: {result['title']}")
                        st.caption(result['href'])
                        st.write(result['body'])
                        st.divider()

                with st.spinner("🧹 Scraping content..."):
                    all_content = []
                    for result in results:
                        try:
                            response = requests.get(result['href'], timeout=10)
                            soup = BeautifulSoup(response.text, 'html.parser')
                            page_text = ' '.join(p.get_text() for p in soup.find_all('p'))
                            all_content.append(page_text[:2000])
                        except:
                            continue
                    
                    combined_content = '\n\n'.join(all_content)[:12000]

                with st.expander("📃 Full Content", expanded=False):
                    st.write(combined_content)

                if client and combined_content:
                    with st.spinner("🧠 Generating summary..."):
                        response = process_content(combined_content, user_query, groq_model)
                        summary = response.choices[0].message.content
                        st.session_state.messages.append({"role": "assistant", "content": summary})
                        with st.chat_message("assistant"):
                            st.markdown(summary)
                
        elif search_type == "YouTube Search":
            # YouTube Processing
            if not is_youtube_url(user_query):
                assistant_response = "Please provide a valid YouTube URL"
                st.session_state.messages.append({"role": "assistant", "content": assistant_response})
                with st.chat_message("assistant"):
                    st.markdown(assistant_response)
            else:
                video_id = extract_video_id(user_query)
                if video_id:
                    with st.spinner("🎥 Processing video..."):
                        try:
                            transcript = YouTubeTranscriptApi.get_transcript(video_id)
                            transcript_text = ' '.join([t['text'] for t in transcript])[:10000]
                            
                            with st.expander("📜 Transcript", expanded=False):
                                st.write(transcript_text)

                            if client:
                                with st.spinner("🧠 Summarizing..."):
                                    response = process_content(transcript_text, "Summarize this video:", groq_model)
                                    summary = response.choices[0].message.content
                                    st.session_state.messages.append({"role": "assistant", "content": summary})
                                    with st.chat_message("assistant"):
                                        st.markdown(summary)
                        except Exception as e:
                            st.error(f"Error processing video: {str(e)}")

        elif search_type == "News Search":
            if not selected_categories:
                st.error("Please select at least one news category in the sidebar")
                st.stop()

            # Get selected news domains
            selected_domains = []
            for category in selected_categories:
                selected_domains.extend(NEWS_SOURCES[category])

            # News Search Processing
            with st.spinner("📰 Searching news..."):
                user_query = user_query +"in category " +  str( selected_domains) + str(sub_sites)
                with DDGS() as ddgs:
                    results = [r for r in ddgs.text(user_query, max_results=4)]

            if results:
                with st.expander("📄 Web Results", expanded=False):
                    for i, result in enumerate(results, 1):
                        st.write(result)
                        st.subheader(f"Result {i}: {result['title']}")
                        st.caption(result['href'])
                        st.write(result['body'])
                        st.divider()

                with st.spinner("🧹 Scraping content..."):
                    all_content = []
                    for result in results:
                        try:
                            response = requests.get(result['href'], timeout=10)
                            soup = BeautifulSoup(response.text, 'html.parser')
                            page_text = ' '.join(p.get_text() for p in soup.find_all('p'))
                            all_content.append(page_text[:2000])
                        except:
                            continue
                    
                    combined_content = '\n\n'.join(all_content)[:12000]

                with st.expander("📃 Full Content", expanded=False):
                    st.write(combined_content)

                if client and combined_content:
                    with st.spinner("🧠 Generating summary..."):
                        user_query = user_query + "Provide with source"
                        response = process_content(combined_content, user_query, groq_model)
                        summary = response.choices[0].message.content
                        st.session_state.messages.append({"role": "assistant", "content": summary})
                        with st.chat_message("assistant"):
                            st.markdown(summary)

        elif search_type == "Image Search":
            # Image Search Processing
            with st.chat_message("assistant"):
                with st.spinner(f"🖼️ Searching for {num_images} images..."):
                    try:
                        with DDGS() as ddgs:
                            image_results = [r for r in ddgs.images(user_query, max_results=num_images)]
                    except Exception as e:
                        image_results = []
                        st.error(f"Image search failed: {str(e)}")

                    valid_images = []
                    if image_results:
                        # Validate images and collect downloadable links
                        with st.spinner("🔍 Verifying image links..."):
                            for result in image_results:
                                try:
                                    response = requests.head(result['image'], timeout=5)
                                    if response.status_code == 200:
                                        valid_images.append(result)
                                except:
                                    continue

                    if valid_images:
                        with st.expander(f"📸 Image Results ({len(valid_images)} found)", expanded=True):
                            cols = st.columns(3)
                            for i, result in enumerate(valid_images):
                                with cols[i%3]:
                                    st.image(
                                        result['image'],
                                        caption=f"{result['title'][:50]}"
                                    )
                                    # Download button
                                    st.markdown(
                                        f"[⬇️ Download]({result['image']}) | " +
                                        f"[Source]({result['url']})",
                                        unsafe_allow_html=True
                                    )
                        
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": f"Found {len(valid_images)}/{num_images} images for: {user_query}"
                        })
                        st.markdown(f"**Found {len(valid_images)} valid images for:** _{user_query}_")
                        st.markdown("ℹ️ Click the expander to view images with download links")
                        
                    else:
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": f"❌ No images found for: {user_query}"
                        })
                        st.markdown(f"**No images found for:** _{user_query}_")
                        st.markdown("Please try a different search query")
                        

    except Exception as e:
        st.error(f"Error: {str(e)}")

# Enhanced dark mode styling
# Theme-adaptive styling
st.markdown("""
<style>
    /* Base styles that adapt to theme */
    .stApp {
        background-color: var(--background-color);
        color: var(--text-color);
    }
    
    .stChatInput textarea {
        color: var(--text-color) !important;
    }
    
    .stRadio > div > label > div {
        color: var(--text-color) !important;
    }
    
    /* Theme-aware expander styling */
    .stExpander {
        background-color: var(--secondary-background-color);
        border-color: var(--border-color) !important;
    }
    
    .stExpander .streamlit-expanderHeader {
        color: var(--text-color);
    }
    
    /* Image styling */
    .stImage > img {
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    /* Theme-aware link colors */
    a {
        color: var(--link-text-color) !important;
    }
    
    /* Adaptive scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: var(--secondary-background-color);
    }
    
    ::-webkit-scrollbar-thumb {
        background: var(--primary-color);
        border-radius: 4px;
    }
</style>
""", unsafe_allow_html=True)
