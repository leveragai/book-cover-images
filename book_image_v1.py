import streamlit as st
import os
import requests
import base64
from dotenv import load_dotenv
from datetime import datetime
import io
from PIL import Image

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="Book Cover Generator",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main {
        padding: 0;
    }
    .stTitle {
        color: #2c3e50;
        font-size: 2.5rem;
        font-weight: bold;
        margin-bottom: 1rem;
    }
    .subtitle {
        color: #34495e;
        font-size: 1.1rem;
        margin-bottom: 2rem;
    }
    .prompt-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1rem;
        border-radius: 5px;
        margin-bottom: 1rem;
    }
    .prompt-info {
        background-color: #e7f3ff;
        border-left: 4px solid #2196F3;
        padding: 1rem;
        margin-bottom: 1rem;
        border-radius: 4px;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if "generated_images" not in st.session_state:
    st.session_state.generated_images = []
if "api_key_valid" not in st.session_state:
    st.session_state.api_key_valid = False
if "current_prompt" not in st.session_state:
    st.session_state.current_prompt = ""

# Constants
AZURE_ENDPOINT = "https://lever-mgvt2xmr-swedencentral.services.ai.azure.com/openai/deployments/FLUX-1.1-pro/images/generations"
API_VERSION = "2025-04-01-preview"

# Sidebar
with st.sidebar:
    st.title("⚙️ Settings")
    
    # API Key management
    st.subheader("API Configuration")
    api_key = st.text_input(
        "Azure API Key",
        type="password",
        help="Enter your BFL_API_KEY from Azure",
        placeholder="sk-..."
    )
    
    if api_key:
        st.session_state.api_key_valid = True
        st.success("✅ API Key loaded")
    else:
        api_key = os.getenv("BFL_API_KEY")
        if api_key:
            st.session_state.api_key_valid = True
            st.info("✅ Using environment variable")
        else:
            st.warning("⚠️ No API key found")
    
    st.divider()
    
    # Image settings
    st.subheader("Image Settings")
    
    image_size = st.selectbox(
        "Image Size",
        ["1024x1024", "1024x576", "1280x1920"],
        help="Choose the aspect ratio for your book cover"
    )
    
    num_images = st.slider(
        "Number of Variations",
        min_value=1,
        max_value=4,
        value=1,
        help="Generate multiple variations (more = longer processing)"
    )
    
    output_format = st.selectbox(
        "Output Format",
        ["png", "jpeg"],
        help="Image format for download"
    )
    
    st.divider()
    
    # About
    st.subheader("About")
    st.markdown("""
    ### Book Cover Generator
    
    Generate stunning AI-powered book covers using Azure's FLUX model.
    
    **Features:**
    - Fully editable prompts
    - Auto-generate suggestions
    - Custom book titles & descriptions
    - Instant preview
    - Download in PNG/JPEG
    - History & batch generation
    
    **Technologies:**
    - Streamlit
    - Azure OpenAI (FLUX-1.1-pro)
    - Python
    """)

# Main content
col1, col2 = st.columns([2, 1])

with col1:
    st.markdown("# 📚 Book Cover Generator")
    st.markdown("*Create stunning book covers powered by AI*")

with col2:
    # Stats
    if st.session_state.generated_images:
        st.metric("Covers Generated", len(st.session_state.generated_images))

st.divider()

# Two-column layout for input
col_input1, col_input2 = st.columns(2)

with col_input1:
    st.subheader("📖 Book Details")
    
    book_title = st.text_input(
        "Book Title *",
        placeholder="e.g., Rich Dad Poor Dad",
        help="The main title that will appear on the cover"
    )
    
    book_category = st.selectbox(
        "Book Category *",
        [
            "Personal Growth",
            "Business Strategy",
            "Marketing",
            "Sales",
            "Startups",
            "Psychology",
            "Sociology",
            "Biographies",
            "History",
            "Religious",
            "Spirituality",
            "Philosophy",
            "Language Learning",
            "Children's Books"
        ],
        help="Select the category for thematic color palette"
    )

with col_input2:
    st.subheader("✍️ Book Summary")
    
    book_summary = st.text_area(
        "Book Summary *",
        placeholder="Describe what your book is about. This helps the AI create a relevant cover design.",
        height=150,
        help="A detailed description of your book's content, themes, and key ideas."
    )

st.divider()

# Advanced options
with st.expander("🎨 Advanced Customization"):
    col_adv1, col_adv2 = st.columns(2)
    
    with col_adv1:
        style_preference = st.multiselect(
            "Style Preferences",
            [
                "Vector",
                "Geometric",
                "Minimalist",
                "Bold",
                "Elegant",
                "Modern",
                "Classic",
                "Abstract"
            ],
            default=["Vector", "Geometric", "Minimalist"],
            help="Select multiple styles for the cover design"
        )
    
    with col_adv2:
        color_preference = st.multiselect(
            "Color Tone",
            [
                "Warm",
                "Cool",
                "Neutral",
                "Vibrant",
                "Pastel",
                "Bold"
            ],
            default=["Warm"],
            help="Choose the color tone for your cover"
        )
    
    custom_prompt_addition = st.text_area(
        "Additional Prompt Instructions (Optional)",
        placeholder="Add any specific requirements or style preferences...",
        height=80
    )

st.divider()

# Build prompt function
def build_prompt(title, summary, category, styles, colors, additional):
    """Build the complete prompt for image generation"""
    
    category_rules = {
        "Personal Growth": "warm soft tones",
        "Business Strategy": "structured warm neutrals with dark accents",
        "Marketing": "bright high contrast warm colors",
        "Sales": "warm reds with deep navy",
        "Startups": "blue dominant tones with warm highlights",
        "Psychology": "purple blue with subtle warm accents",
        "Sociology": "natural greens and earth tones",
        "Biographies": "soft natural colors, stylized portrait or silhouette",
        "History": "earth tones with deep blues",
        "Religious": "soft earth tones with golden light",
        "Spirituality": "warm mystical hues",
        "Philosophy": "neutral tones with strong contrast",
        "Language Learning": "warm friendly tones",
        "Children's Books": "bright playful colors and rounded shapes"
    }
    
    styles_str = ", ".join(styles) if styles else "Vector, Geometric, Minimalist"
    colors_str = ", ".join(colors) if colors else "Warm"
    color_palette = category_rules.get(category, "warm soft tones")
    
    prompt = f"""Create a professional book cover illustration for: "{title}"

Book Category: {category}
Book Summary: {summary}

Design Requirements:
- Style: {styles_str}
- Color Tone: {colors_str}
- Color Palette: {color_palette}
- Layout: Vertical (3 by 2 ratio)
- Format: Clean editorial vector style

Composition Rules:
- Use large, bold geometric vector shapes
- Create one clear metaphor that represents the book's core idea
- Keep forms solid, crisp, and immediately readable
- Avoid small icons or decorative clutter
- Use soft gradients and minimal grain texture for depth
- Include title at bottom: "{title}"
- No realism - pure vector design

{f'Additional Requirements: {additional}' if additional else ''}

Generate a visually striking, professional book cover that immediately communicates the book's theme and appeals to the target audience."""
    
    return prompt

# ============================================================================
# EDITABLE PROMPT SECTION - MAIN FEATURE
# ============================================================================

st.markdown("""
<div class="prompt-header">
    <h2>🤖 AI Prompt Editor</h2>
    <p>Edit the prompt below to customize your cover design. The prompt is sent directly to the AI.</p>
</div>
""", unsafe_allow_html=True)

# Info box
st.markdown("""
<div class="prompt-info">
    <strong>💡 Tip:</strong> The prompt below controls exactly what the AI creates. Edit keywords, add instructions, or completely rewrite it. Click "Auto-Generate" to rebuild from your book details.
</div>
""", unsafe_allow_html=True)

# Auto-generate button and prompt together
col_prompt_button, col_prompt_space = st.columns([1, 4])

with col_prompt_button:
    if st.button("🔄 Auto-Generate Prompt", use_container_width=True):
        if book_title and book_summary:
            auto_prompt = build_prompt(
                book_title,
                book_summary,
                book_category,
                style_preference,
                color_preference,
                custom_prompt_addition
            )
            st.session_state.current_prompt = auto_prompt
            st.rerun()
        else:
            st.error("Enter title & summary first")

# MAIN EDITABLE PROMPT TEXT AREA
# This is where users actually edit the prompt
user_prompt = st.text_area(
    "Prompt (Editable) *",
    value=st.session_state.current_prompt,
    height=400,
    placeholder="""Enter or edit your prompt here. Example:

Create a professional book cover for "Book Title"
- Style: Vector, geometric shapes
- Colors: Warm tones - oranges, golds
- Show: A symbolic metaphor for the book's theme
- Include: Bold title text at bottom
- No photographs or realistic images
- Professional and modern look""",
    help="This is the actual prompt sent to the AI. Edit it to customize your cover design.",
    key="main_prompt_editor"
)

# Update session state with user's edits
st.session_state.current_prompt = user_prompt

# Quick action buttons below prompt
col_action1, col_action2, col_action3, col_action4 = st.columns(4)

with col_action1:
    if st.button("📋 Copy Prompt", use_container_width=True):
        st.info("✅ Select text above and press Ctrl+C (or Cmd+C on Mac)")

with col_action2:
    if st.button("🗑️ Clear Prompt", use_container_width=True):
        st.session_state.current_prompt = ""
        st.rerun()

with col_action3:
    if st.button("📥 Load Template", use_container_width=True):
        template = """Create a professional book cover for: "{TITLE}"

Key Visual Elements:
- [Describe main visual element]
- [Describe secondary element]
- [Describe background]

Style & Colors:
- Style: [Vector/Realistic/Illustration/Abstract]
- Primary Colors: [Color 1, Color 2, Color 3]
- Tone: [Professional/Creative/Modern/Classic]

Text:
- Title: "{TITLE}" - [Size/Position/Style]
- Subtitle: [If applicable]

Additional Notes:
- [Any special requirements]
- [Avoid: List what to avoid]
- [Target audience: Who will see this?]"""
        st.session_state.current_prompt = template
        st.rerun()

with col_action4:
    if st.button("✨ Generate", use_container_width=True):
        st.session_state.generate_now = True

st.divider()

# Character count
prompt_length = len(st.session_state.current_prompt)
col_char1, col_char2 = st.columns([3, 1])

with col_char1:
    st.caption(f"Prompt length: {prompt_length} characters")

with col_char2:
    if prompt_length > 2000:
        st.warning("⚠️ Prompt may be long")
    elif prompt_length > 500:
        st.success("✅ Good length")
    else:
        st.info("ℹ️ Add more details")

st.divider()

# ============================================================================
# GENERATE SECTION
# ============================================================================

col_button1, col_button2, col_button3 = st.columns(3)

with col_button1:
    generate_button = st.button(
        "🎨 Generate Cover",
        use_container_width=True,
        type="primary",
        key="main_generate"
    )

with col_button2:
    if st.session_state.generated_images:
        clear_button = st.button(
            "🗑️ Clear History",
            use_container_width=True
        )
    else:
        clear_button = False

with col_button3:
    st.info(f"⏱️ Processing: ~30-60 seconds")

# Handle generation
if generate_button or st.session_state.get("generate_now", False):
    st.session_state.generate_now = False
    
    if not st.session_state.api_key_valid and not api_key:
        st.error("❌ Please provide an Azure API Key")
    elif not book_title or not st.session_state.current_prompt:
        st.error("❌ Please enter Book Title and Prompt")
    else:
        progress_bar = st.progress(0)
        status_text = st.empty()
        result_container = st.container()
        
        try:
            # Use the current editable prompt
            prompt = st.session_state.current_prompt
            
            headers = {
                "Content-Type": "application/json",
                "api-key": api_key if api_key else os.getenv("BFL_API_KEY")
            }
            
            url = f"{AZURE_ENDPOINT}?api-version={API_VERSION}"
            
            # Generate images
            generated_this_batch = []
            
            for i in range(num_images):
                status_text.text(f"🎨 Generating image {i+1}/{num_images}...")
                progress_bar.progress((i) / num_images)
                
                payload = {
                    "prompt": prompt,
                    "output_format": output_format,
                    "n": 1,
                    "size": image_size
                }
                
                response = requests.post(url, headers=headers, json=payload, timeout=120)
                
                if response.status_code == 200:
                    result = response.json()
                    
                    if "data" in result and len(result["data"]) > 0:
                        item = result["data"][0]
                        
                        # Handle base64 or URL
                        if "b64_json" in item:
                            image_data = base64.b64decode(item["b64_json"])
                        elif "url" in item:
                            img_response = requests.get(item["url"])
                            image_data = img_response.content
                        else:
                            raise ValueError("No image data in response")
                        
                        generated_this_batch.append({
                            "image": image_data,
                            "title": book_title,
                            "category": book_category,
                            "timestamp": datetime.now(),
                            "size": image_size,
                            "summary": book_summary,
                            "prompt": prompt
                        })
                    else:
                        st.error(f"❌ No data returned for image {i+1}")
                else:
                    st.error(f"❌ API Error {response.status_code}: {response.text[:200]}")
            
            progress_bar.progress(100)
            status_text.text("✅ Generation complete!")
            
            # Display results
            if generated_this_batch:
                st.session_state.generated_images.extend(generated_this_batch)
                
                with result_container:
                    st.success(f"✅ Generated {len(generated_this_batch)} cover(s)")
                    
                    # Display in grid
                    cols = st.columns(min(len(generated_this_batch), 2))
                    
                    for idx, img_data in enumerate(generated_this_batch):
                        with cols[idx % len(cols)]:
                            st.image(img_data["image"], use_container_width=True)
                            
                            col_down1, col_down2 = st.columns(2)
                            
                            with col_down1:
                                st.download_button(
                                    label=f"⬇️ Download {idx+1}",
                                    data=img_data["image"],
                                    file_name=f"{book_title.lower().replace(' ', '_')}_{idx+1}.{output_format}",
                                    mime=f"image/{output_format}",
                                    use_container_width=True
                                )
                            
                            with col_down2:
                                st.info(f"Generated: {img_data['timestamp'].strftime('%H:%M:%S')}")
        
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")
            st.info("💡 Make sure your API key is valid and you have sufficient credits")

# Clear history
if clear_button:
    st.session_state.generated_images = []
    st.success("✅ History cleared")
    st.rerun()

st.divider()

# Display history
if st.session_state.generated_images:
    st.subheader("📚 Generation History")
    
    # Filter options
    col_filter1, col_filter2 = st.columns(2)
    
    with col_filter1:
        filter_category = st.multiselect(
            "Filter by Category",
            sorted(set([img["category"] for img in st.session_state.generated_images])),
            help="Filter history by book category"
        )
    
    with col_filter2:
        sort_order = st.selectbox(
            "Sort by",
            ["Newest First", "Oldest First"],
            help="Sort generation history"
        )
    
    # Filter and sort
    filtered_images = st.session_state.generated_images
    
    if filter_category:
        filtered_images = [img for img in filtered_images if img["category"] in filter_category]
    
    if sort_order == "Oldest First":
        filtered_images = sorted(filtered_images, key=lambda x: x["timestamp"])
    else:
        filtered_images = sorted(filtered_images, key=lambda x: x["timestamp"], reverse=True)
    
    if filtered_images:
        # Display in gallery
        cols_per_row = 4
        for i in range(0, len(filtered_images), cols_per_row):
            cols = st.columns(cols_per_row)
            
            for col_idx, col in enumerate(cols):
                img_idx = i + col_idx
                
                if img_idx < len(filtered_images):
                    img_data = filtered_images[img_idx]
                    
                    with col:
                        st.image(img_data["image"], use_container_width=True)
                        st.caption(f"📖 {img_data['title']}")
                        st.caption(f"🏷️ {img_data['category']}")
                        st.caption(f"⏰ {img_data['timestamp'].strftime('%H:%M')}")
                        
                        with st.expander("📝 View Details"):
                            st.markdown("**Summary:**")
                            st.write(img_data['summary'])
                            st.markdown("**Prompt:**")
                            st.code(img_data['prompt'], language="text")
                            
                            # Button to load this prompt
                            if st.button(f"📥 Load This Prompt", key=f"load_prompt_{img_idx}"):
                                st.session_state.current_prompt = img_data['prompt']
                                st.rerun()
                        
                        st.download_button(
                            label="⬇️ Download",
                            data=img_data["image"],
                            file_name=f"{img_data['title'].lower().replace(' ', '_')}.{output_format}",
                            mime=f"image/{output_format}",
                            use_container_width=True,
                            key=f"download_{img_idx}"
                        )
    else:
        st.info("No covers match the selected filters")

st.divider()

# Footer
st.markdown("""
---
<div style='text-align: center'>
    <p><small>📚 Book Cover Generator | Powered by Azure FLUX API | Made with Streamlit</small></p>
</div>
""", unsafe_allow_html=True)
