import os
import requests
import json
from bs4 import BeautifulSoup
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def scrape_trending_products():
    """
    Scrapes ebay daily deals for trending products.
    Returns a list of product titles and links.
    """
    print("Scraping eBay Daily Deals for trending products...")
    url = "https://www.ebay.com/globaldeals"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find item titles
        products = []
        items = soup.select('.dne-itemtile-detail')
        for item in items:
            title_elem = item.select_one('.dne-itemtile-title')
            link_elem = item.select_one('a')
            if title_elem and link_elem:
                title = title_elem.get('title', title_elem.text.strip())
                link = link_elem.get('href', '')
                products.append({"title": title, "link": link})
                
        if not products:
            # Fallback if the selector doesn't match
            print("Fallback scraping...")
            items = soup.find_all('span', class_='ebayui-ellipsis-2')
            for item in items:
                products.append({"title": item.text.strip(), "link": ""})
                
        print(f"Found {len(products)} products.")
        return products[:3] # Return top 3
    except Exception as e:
        print(f"Error scraping eBay: {e}")
        return [{"title": "Sony WH-1000XM5 Wireless Headphones", "link": "#"}] # Hardcode fallback for testing if scraping fails

def get_seo_keywords(product_title):
    """
    Uses Google Autocomplete to find SEO keywords related to the product.
    Returns a list of 3-4 keywords.
    """
    print(f"Researching keywords for: {product_title}...")
    # Clean title for query, take first 3-4 significant words
    words = [w for w in product_title.split() if w.isalnum()]
    query = ' '.join(words[:4]) 
    if not query:
        query = "headphones"
        
    url = f"http://suggestqueries.google.com/complete/search?client=firefox&q={query}"
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        
        data = json.loads(response.text)
        suggestions = data[1] if len(data) > 1 else []
        
        # Filter related terms and restrict to 3-4 keywords
        keywords = [k for k in suggestions if len(k.split()) > 1]
        if not keywords:
            keywords = [f"best {query}", f"buy {query}", f"cheap {query}", f"{query} review"]
            
        selected_keywords = keywords[:4]
        print(f"Found keywords: {selected_keywords}")
        return selected_keywords
    except Exception as e:
        print(f"Error getting keywords: {e}")
        return [f"best {query}", f"buy {query}", f"reviews for {query}"]

def generate_blog_post(product_title, keywords):
    """
    Uses Google Gemini API to write a 150-200 word blog post incorporating keywords.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY environment variable not found.")
        print("Returning mock content for demonstration...")
        return f"""
        <h1>Why You Need {product_title} Today</h1>
        <h2>The Ultimate Buying Guide</h2>
        <p>If you have been searching for <strong>{keywords[0]}</strong>, you are in the right place. {product_title} is currently trending as one of the best options available.</p>
        <p>Shoppers constantly ask about <strong>{keywords[1] if len(keywords) > 1 else 'quality'}</strong> before buying, and this product delivers exceptional performance. Whether you are looking to upgrade your setup or just finding a good deal, this will not disappoint.</p>
        <p>Make sure to read the reviews and search for <strong>{keywords[2] if len(keywords) > 2 else 'discounts'}</strong> to get the best price. Don't wait too long, as best-selling items like this tend to sell out quickly!</p>
        """
        
    print(f"Generating blog post content for: {product_title}...")
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        prompt = f"""
        Act as an expert SEO copywriter. Write a 150-200 word blog post highlighting this product: "{product_title}".
        
        Naturally incorporate these SEO keywords throughout the text: {', '.join(keywords)}.
        
        The content should be engaging, informative, and highly optimized for search engines.
        Do not include markdown wrappers (like ```html), just output raw HTML code suitable to be inserted inside the <body> of an article page.
        Include an <h1> title, an <h2> subtitle, and <p> for paragraphs. Use <strong> for important keywords.
        """
        
        response = model.generate_content(prompt)
        content = response.text.replace('```html', '').replace('```', '').strip()
        print("Successfully generated blog post.")
        return content
    except Exception as e:
        print(f"Error generating content via Gemini API: {e}")
        return None

def publish_to_static_site(product_title, content, index):
    """
    Saves the generated HTML content into a static file inside the output directory.
    """
    if not content:
        print("No content to publish.")
        return
        
    print("Publishing to static site folder...")
    
    # Path inside the script's directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(script_dir, "output")
    os.makedirs(output_dir, exist_ok=True)
    
    # Create safe filename
    safe_title = "".join([c if c.isalnum() else "_" for c in product_title[:20]]).strip("_")
    filename = f"post_{index}_{safe_title}.html"
    filepath = os.path.join(output_dir, filename)
    
    html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SEO Blog: {product_title}</title>
    <style>
        :root {{ --primary: #2563eb; --bg: #f8fafc; --text: #1e293b; }}
        body {{ font-family: 'Inter', system-ui, sans-serif; line-height: 1.6; color: var(--text); background: var(--bg); margin: 0; padding: 20px; }}
        .container {{ max-width: 800px; margin: 40px auto; background: white; padding: 40px; border-radius: 12px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); }}
        h1 {{ color: var(--primary); font-size: 2.2em; margin-top: 0; border-bottom: 2px solid #e2e8f0; padding-bottom: 15px; }}
        h2 {{ color: #475569; font-size: 1.5em; margin-top: 30px; }}
        p {{ margin-bottom: 20px; font-size: 1.1em; }}
        .footer {{ margin-top: 40px; padding-top: 20px; border-top: 1px solid #e2e8f0; text-align: center; font-size: 0.9em; color: #64748b; }}
    </style>
</head>
<body>
    <div class="container">
        {content}
        <div class="footer">
            <p>Auto-generated by AI SEO Blog Creator Pipeline</p>
        </div>
    </div>
</body>
</html>"""

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(html_template)
        
    print(f"Successfully published: {filepath}")

def main():
    print("=========================================")
    print("Starting AI SEO Blog Creator Pipeline...")
    print("=========================================\n")
    
    products = scrape_trending_products()
    if not products:
        print("Could not retrieve products. Exiting.")
        return
        
    # Process only the top 3 products for demonstration
    for idx, product in enumerate(products):
        title = product['title']
        print(f"\n[{idx+1}/{len(products)}] Processing Product: {title[:50]}...")
        
        keywords = get_seo_keywords(title)
        
        content = generate_blog_post(title, keywords)
        
        publish_to_static_site(title, content, idx+1)
        
    print("\n=========================================")
    print("Pipeline completed successfully!")
    print("Check the 'output' directory for the generated blogs.")
    print("=========================================")

if __name__ == "__main__":
    main()
