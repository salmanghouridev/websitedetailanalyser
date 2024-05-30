from flask import Flask, render_template, request
import scrapy
from selenium import webdriver
from scrapy.http import HtmlResponse
from bs4 import BeautifulSoup

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/scrape', methods=['POST'])
def scrape():
    url = request.form['url']

    # Initialize Selenium WebDriver
    driver = webdriver.Chrome()  # You may need to specify the path to your webdriver executable
    driver.get(url)

    # Get the HTML content after JavaScript execution
    html = driver.page_source
    driver.quit()

    # Parse the HTML content using BeautifulSoup
    soup = BeautifulSoup(html, 'html.parser')

    # Extract data from the BeautifulSoup object
    # For example, let's extract all the links on the page
    links = [link.get('href') for link in soup.find_all('a')]

    # You can further process the data as per your requirements
    # For now, let's just return the links
    return render_template('result.html', links=links)

if __name__ == '__main__':
    app.run(debug=True)
