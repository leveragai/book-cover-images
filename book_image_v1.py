import os
import requests
import base64
from dotenv import load_dotenv

load_dotenv()

AZURE_ENDPOINT = "https://lever-mgvt2xmr-swedencentral.services.ai.azure.com/openai/deployments/FLUX-1.1-pro/images/generations"
AZURE_API_KEY = os.getenv("BFL_API_KEY")
API_VERSION = "2025-04-01-preview"

OUTPUT_FOLDER = "generated_book_covers"
os.makedirs(OUTPUT_FOLDER, exist_ok=True)


def summarize_book():
    """Generate ~100-word summary of Rich Dad Poor Dad."""
    return (
        """
        Thinking, Fast and Slow explores how the human mind operates using two distinct systems: the fast, intuitive, automatic System 1, and the slow, deliberate, analytical System 2. Daniel Kahneman reveals how these systems shape judgments, decisions, biases, and everyday thinking. Through decades of research in psychology and behavioral economics, he explains cognitive shortcuts, illusions, and errors that influence choices without our awareness. The book encourages readers to question their assumptions, recognize mental traps, and make more informed decisions. It blends science and storytelling to provide deep insight into how people think and why they often misjudge situations.
        """

    )


def generate_book_cover(summary_text, title="Rich Dad Poor Dad"):
    if not AZURE_API_KEY:
        print("❌ Error: AZURE_API_KEY is not set.")
        return

    headers = {
        "Content-Type": "application/json",
        "api-key": AZURE_API_KEY
    }

    url = f"{AZURE_ENDPOINT}?api-version={API_VERSION}"

    # --- Image Prompt ---
    prompt = f"""
    Using this text:

"Kiyosaki's educated but financially struggling biological father (poor dad) and his friend's wealthy entrepreneur father (rich dad). The book challenges conventional wisdom about money, emphasizing that wealth comes from financial literacy and asset building, not just high income. Kiyosaki advocates for entrepreneurship, real estate investing, and understanding cash flow over accumulating possessions. Key lessons include the importance of passive income, business ownership, and thinking like an investor rather than an employee. The book inspired millions to reconsider their approach to money and financial independence."

Generate explainer illustration in clean editorial vector style.
Vertical 3 by 2 layout.
Title: Rich dad poor dad
Analyze the meaning, tone, and domain of the given title, then automatically classify it into the best matching visual category among the following 14 styles and strictly apply the corresponding rules:
 
 
Generate a bold, simple scene made of large geometric vector shapes that visually represents the core idea of the book.
Use a single strong metaphor or symbolic moment.
Avoid small icons or decorative clutter.
Forms must be solid, crisp, and immediately readable.
Soft gradients and minimal grain texture may be used to add depth while keeping the vector look clean.
 
Color palette automatically adapts to the thematic category of the book:
Personal Growth → warm soft tones
Business Strategy → structured warm neutrals with dark accents
Marketing → bright high contrast warm colors
Sales → warm reds with deep navy
Startups → blue dominant tones with warm highlights
Psychology → purple blue with subtle warm accents
Sociology → natural greens and earth tones
Biographies → soft natural colors, stylized portrait or silhouette
History → earth tones with deep blues
Religious → soft earth tones with golden light
Spirituality → warm mystical hues
Philosophy → neutral tones with strong contrast
Language Learning → warm friendly tones
Children’s Books → bright playful colors and rounded shapes
 
The composition should be clean, balanced, and built around one clear metaphor.
No realism.
No extra symbols.
Only the title as text.

"""

    payload = {
        "prompt": prompt,
        "output_format": "png",
        "n": 1,
        "size": "1024x1024"
    }

    print(f"🎨 Generating book cover for: {title}...")

    try:
        response = requests.post(url, headers=headers, json=payload)

        if response.status_code == 200:
            result = response.json()

            if "data" in result and len(result["data"]) > 0:
                item = result["data"][0]
                filename = "rich_dad_poor_dad_cover.png"
                filepath = os.path.join(OUTPUT_FOLDER, filename)

                # Base64 mode
                if "b64_json" in item:
                    image_data = base64.b64decode(item["b64_json"])
                    with open(filepath, "wb") as f:
                        f.write(image_data)
                    print(f"✅ Saved book cover to: {filepath}")

                # URL mode
                elif "url" in item:
                    img_response = requests.get(item["url"])
                    with open(filepath, "wb") as f:
                        f.write(img_response.content)
                    print(f"✅ Saved book cover to: {filepath}")
            else:
                print("⚠️ Success but no data returned from API.")

        else:
            print(f"❌ API Error {response.status_code}")
            print(response.text)

    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    summary = summarize_book()
    print("📚 Summary Generated:\n", summary)
    generate_book_cover(summary)
