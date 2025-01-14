import streamlit as st
from selenium import webdriver
from selenium.webdriver.common.by import By
import time
import json
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

# Set up Chrome WebDriver for Selenium
chrome_options = webdriver.ChromeOptions()
chrome_options.add_experimental_option("detach", True)

# Load JSON files
with open("categorized_reviews.json", "r") as file:
    categorized_data = json.load(file)

with open("reviewsData.json", "r") as file:
    original_reviews = json.load(file)

with open("sentiment_reviews.json", "r" , encoding= "utf-8") as file:
    sentiment_data = json.load(file)

food_comments = categorized_data.get("food_comments", [])
staff_comments = categorized_data.get("staff_comments", [])
positive_comments = sentiment_data.get("positive_comments", [])
negative_comments = sentiment_data.get("negative_comments", [])


st.set_page_config(page_title="Restaurant Review Dashboard", page_icon="🍽️", layout="wide")

# CSS
st.markdown(
    """
    <style>
        .food-comments {
            background-color: #003049; /* Food comments section background */
            padding: 10px;
            border-radius: 25px;
            color: white;
            margin-bottom: 15px;
        }
        .staff-comments {
            background-color: #14213d; /* Staff comments section background */
            padding: 10px;
            border-radius: 25px;
            color: white;
            margin-bottom: 15px;
        }
        .customer-reviews {
            background-color: #f4a261; /* Customer reviews section background */
            padding: 10px;
            border-radius: 25px;
            color: black;
            margin-bottom: 15px; /* Add space between reviews */
        }
        .sentiment-analysis {
            background-color: #f4a261; /* Sentiment analysis section background */
            padding: 10px;
            border-radius: 25px;
            color: black;
            margin-bottom: 15px; /* Add space between reviews */
        }
        .review-heading {
            font-size: 1.2em;
            font-weight: bold;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("🟥 North Square Restaurant Review Dashboard")
st.subheader("Explore Reviews and Comments")

# Selection bar
view_option = st.selectbox("Select View", options=["Customer Reviews", "Food/Staff Comments" , "Scrap Reviews" , "Sentiment Analysis"])

# Search bar
search_term = st.text_input("🔎 Search for a word in the comments:", placeholder="Type a word...")

def clean_comment(comment, prefix_to_remove):
    """Remove a specific prefix from the comment if it exists."""
    if comment.startswith(prefix_to_remove):
        return comment[len(prefix_to_remove):].strip()
    return comment

def filter_comments(comments, search_term):
    """Filter comments based on the search term."""
    if not search_term:
        return comments
    return [comment for comment in comments if search_term.lower() in comment.lower()]
def highlight_keywords(comment):
    """Highlight specific keywords in the comment."""
    comment = comment.replace("food", '<span style="color:red;">food</span>')
    comment = comment.replace("staff", '<span style="color:yellow;">staff</span>')
    comment = comment.replace("service", '<span style="color:yellow;">service</span>')
    return comment

def parse_date(date_str):
    """Convert various date formats to a standard datetime object."""
    try:
        if isinstance(date_str, datetime):
            return date_str  
        if "Dined on" in date_str:
            return datetime.strptime(date_str.replace("Dined on ", "").strip(), "%B %d, %Y")
        elif "day ago" in date_str or "days ago" in date_str:
            days_ago = int(date_str.split()[1])
            return datetime.now() - timedelta(days=days_ago)
        else:
            raise ValueError(f"Unknown date format: {date_str}")
    except Exception as e:
        return None

def scrape_reviews(url):
    """Scrape reviews from the OpenTable restaurant page."""
    driver = webdriver.Chrome(options=chrome_options)
    reviews_data = []

    try:
        driver.get(url)
        time.sleep(2)

        # Scraping Name
        restaurant_name = driver.find_element(By.XPATH, '//*[@id="mainContent"]/div/div[2]/div[1]/section[1]/div[1]/div/div[1]/h1')
        name = restaurant_name.text

        # Review , Rating and Dates Scrapping
        for page in range(1, 10):
            driver.get(f"{url}&page={page}")
            time.sleep(2)

            reviews = driver.find_elements(By.XPATH, '//*[@id="restProfileReviewsContent"]/li/div/div[2]/span[1]')
            ratings = driver.find_elements(By.XPATH, '//*[@id="restProfileReviewsContent"]/li/div/ol/li[1]/span')
            dates = driver.find_elements(By.XPATH, '//*[@id="restProfileReviewsContent"]/li/div/div[1]/p')

            for i in range(min(10, len(reviews))):
                review_text = reviews[i].text
                rating_text = ratings[i].text
                date_text = dates[i].text

                if review_text and rating_text and date_text:
                    reviews_data.append({
                        "Review": review_text,
                        "Rating": rating_text, 
                        "Date": date_text
                    })
    except Exception as e:
        st.error(f"Error while scraping data: {e}")
    finally:
        driver.quit()

    return reviews_data

def filter_reviews_by_search(data, search_term):
    """Filter reviews or comments based on the search term."""
    if not search_term:
        return data
    return [item for item in data if search_term.lower() in item["review"]["Review"].lower()]

if view_option == "Customer Reviews":
    st.header("📋 Customer Reviews")
    filtered_reviews = [
        review for review in original_reviews
        if search_term.lower() in review["Review"].lower() or search_term.lower() in review["Date"].lower()
    ]
    if filtered_reviews:
        for review in filtered_reviews:
            st.markdown(
                f"""
                <div class="customer-reviews">
                    <span class="review-heading">Review:</span> {review['Review']}<br>
                    <span class="review-heading">Rating:</span> {'⭐' * int(review['Rating'])}<br>
                    <span class="review-heading">Date:</span> 📅 {review['Date']}
                </div>
                """,
                unsafe_allow_html=True,
            )
    else:
        st.write("No reviews found matching your search term.")
elif view_option == "Food/Staff Comments":
    col1, col2 = st.columns(2)

    filtered_food_comments = filter_comments(food_comments, search_term)
    filtered_staff_comments = filter_comments(staff_comments, search_term)

    with col1:
        st.header("🍔 Food Comments") 
        if filtered_food_comments:
            for comment in filtered_food_comments:
                if "please provide the review" in comment.lower():
                    continue  # Skip irrelevant 
                cleaned_comment = clean_comment(comment, "Here are the comments about food quality:\n\n*")
                highlighted_comment = highlight_keywords(cleaned_comment)
                st.markdown(f'<div class="food-comments">{highlighted_comment}</div>', unsafe_allow_html=True)
        else:
            st.write("No food comments found matching your search term.")

    with col2:
        st.header("🧹 Staff Comments")
        if filtered_staff_comments:
            for comment in filtered_staff_comments:
                if "please provide the review" in comment.lower():
                    continue  # Skip irrelevant
                cleaned_comment = clean_comment(comment, "Here are the comments about staff/service:\n\n*")
                highlighted_comment = highlight_keywords(cleaned_comment)
                st.markdown(f'<div class="staff-comments">{highlighted_comment}</div>', unsafe_allow_html=True)
        else:
            st.write("No staff comments found matching your search term.")
elif view_option == "Sentiment Analysis":
    st.header("🔍 Sentiment Analysis of Reviews")
    col1, col2 = st.columns(2)

    filtered_positive = filter_reviews_by_search(positive_comments, search_term)
    filtered_negative = filter_reviews_by_search(negative_comments, search_term)

    with col1 :
        st.subheader("✅ Positive Comments")
        if filtered_positive:
            for comment in filtered_positive:
                st.markdown(
                    f"""
                    <div class="sentiment-analysis">
                        <span class="review-heading">Review:</span> {comment["review"]["Review"]}<br>
                        <span class="review-heading">Analysis:</span> {comment["analysis"]}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        else:
            st.write("No positive comments found matching your search term.")

    with col2:
        st.subheader("❌ Negative Comments")
        if filtered_negative:
            for comment in filtered_negative:
                st.markdown(
                    f"""
                    <div class="sentiment-analysis">
                        <span class="review-heading">Review:</span> {comment["review"]["Review"]}<br>
                        <span class="review-heading">Analysis:</span> {comment["analysis"]}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        else:
            st.write("No negative comments found matching your search term.")
else:
    st.title("Restaurant Review Scraper & Rating Trends")
    st.subheader("Analyze rating trends from reviews 📝")

    competitor_link = st.text_input("Enter OpenTable link:")

    if competitor_link:
        st.write(f"Scraping reviews from: {competitor_link}")
        
        # Scrape reviews and save to JSON
        reviews = scrape_reviews(competitor_link)
        with open("secondrestaurantreviews.json", "w") as json_file:
            json.dump(reviews, json_file, indent=4, default=str)

        st.success(f"Successfully scraped {len(reviews)} reviews.")
        st.json(reviews[:5])


        # Load and process reviews
        with open("reviewsData.json", "r") as json_file:
            data1 = json.load(json_file)
        with open("secondrestaurantreviews.json", "r") as json_file:
            data2 = json.load(json_file)

    # Convert data to DataFrames
        data1 = data1[:90]
        df1 = pd.DataFrame(data1)
        df2 = pd.DataFrame(data2)

        df1['Date'] = df1['Date'].apply(parse_date) 
        df2['Date'] = df2['Date'].apply(parse_date) 

        # Drop invalid dates
        df1 = df1.dropna(subset=['Date'])
        df2 = df2.dropna(subset=['Date'])

        # Sort data by Date
        df1.sort_values(by='Date', inplace=True)
        df2.sort_values(by='Date', inplace=True)


        # Plot time-series graph
        st.subheader("Time-Series Rating Trends for Both Datasets 📈")
        plt.figure(figsize=(12, 6))
        plt.plot(df1['Date'], df1['Rating'], marker='o', label='Dataset 1 (reviewsData.json)', color='blue')
        plt.plot(df2['Date'], df2['Rating'], marker='x', label='Dataset 2 (Scraped Data)', color='red')
        plt.xlabel('Date')
        plt.ylabel('Rating')
        plt.title('Rating Trends Over Time')
        plt.legend()
        st.pyplot(plt)

        st.write("Dataset 1 (reviewsData.json):", df1.head())
        st.write("Dataset 2 (Scraped Data):", df2.head())
        
    else:
        st.write("Please enter a valid OpenTable restaurant link to start scraping.")


st.write("---")
st.info("The dashboard displays customer reviews or categorized comments or scraps reviews based on your selection.")
