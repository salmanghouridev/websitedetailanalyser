import streamlit as st
from flask import Flask, request, jsonify
from flask_cors import CORS
import builtwith
import requests
import socket
import whois
import ssl
from OpenSSL import crypto
from urllib.parse import urlparse
from http.client import HTTPConnection
from bs4 import BeautifulSoup
from geopy.geocoders import Nominatim
import re
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS

def fetch_url(url):
    if not url.startswith(('http://', 'https://')):
        url = 'http://' + url

    response = requests.get(url, allow_redirects=True)
    final_url = response.url
    return final_url, response

def get_domain_info(domain):
    domain_info = whois.whois(domain)
    return {
        'domain_name': domain_info.domain_name,
        'registrar': domain_info.registrar,
        'creation_date': domain_info.creation_date,
        'expiration_date': domain_info.expiration_date,
        'name_servers': domain_info.name_servers
    }

def get_ssl_info(domain):
    context = ssl.create_default_context()
    with context.wrap_socket(socket.socket(), server_hostname=domain) as s:
        s.connect((domain, 443))
        cert = s.getpeercert(True)
        x509 = crypto.load_certificate(crypto.FILETYPE_ASN1, cert)
        return {
            'issuer': dict((key.decode('utf-8'), value.decode('utf-8')) for key, value in x509.get_issuer().get_components()),
            'subject': dict((key.decode('utf-8'), value.decode('utf-8')) for key, value in x509.get_subject().get_components()),
            'version': x509.get_version(),
            'serial_number': x509.get_serial_number(),
            'not_before': x509.get_notBefore().decode('utf-8'),
            'not_after': x509.get_notAfter().decode('utf-8')
        }

def get_performance_metrics(url):
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    driver = webdriver.Chrome(options=chrome_options)
    driver.get(url)
    navigation_start = driver.execute_script("return window.performance.timing.navigationStart")
    load_event_end = driver.execute_script("return window.performance.timing.loadEventEnd")
    page_load_time = (load_event_end - navigation_start) / 1000
    driver.quit()
    return page_load_time

def get_website_details(url):
    details = {}
    recommendations = []

    try:
        final_url, response = fetch_url(url)
        parsed_url = urlparse(final_url)
        domain = parsed_url.netloc

        details['url'] = final_url
        try:
            details['technologies'] = builtwith.builtwith(final_url)
        except Exception as e:
            details['technologies'] = {'error': str(e)}

        try:
            details['ip_address'] = socket.gethostbyname(domain)
        except Exception as e:
            details['ip_address'] = {'error': str(e)}

        try:
            details['speed'] = response.elapsed.total_seconds()
            if details['speed'] > 2:
                recommendations.append("Consider optimizing your website's speed. The page load time is over 2 seconds.")
        except Exception as e:
            details['speed'] = {'error': str(e)}

        try:
            details['domain_info'] = get_domain_info(domain)
        except Exception as e:
            details['domain_info'] = {'error': str(e)}

        try:
            soup = BeautifulSoup(response.text, 'html.parser')

            # Scrape contact information
            contact_info = {}
            contact_elements = soup.find_all(['p', 'span', 'div'])
            for element in contact_elements:
                text = element.get_text().strip()
                if re.match(r'[\w\s]*phone[\w\s]*:?\s*(\+?\d[\d\s\-()+]*)', text, re.IGNORECASE):
                    contact_info['phone'] = re.search(r'(\+?\d[\d\s\-()+]*)', text).group(1)
                elif re.match(r'[\w\s]*email[\w\s]*:?\s*([\w\.-]+@[\w\.-]+)', text, re.IGNORECASE):
                    contact_info['email'] = re.search(r'([\w\.-]+@[\w\.-]+)', text).group(1)
                elif re.match(r'[\w\s]*address[\w\s]*:?\s*(.*)', text, re.IGNORECASE):
                    contact_info['address'] = re.search(r'(.*)', text).group(1)

            details['contact_info'] = contact_info

            # Scrape email addresses
            email_addresses = re.findall(r'[\w\.-]+@[\w\.-]+', response.text)
            details['email_addresses'] = email_addresses

            js_scripts = re.findall(r'<script.*?>(.*?)</script>', response.text, re.DOTALL)
            api_requests = [call[1] for script in js_scripts for call in re.findall(r'fetch\((["\'])(.*?)\1\)', script)]
            details['api_requests'] = api_requests

            link_redirects = sum(1 for link in soup.find_all('a', href=True) if requests.get(url + link['href'], allow_redirects=True).history)
            details['link_redirects'] = link_redirects

            if not soup.title or len(soup.title.text) < 10 or len(soup.title.text) > 70:
                recommendations.append("Ensure your website has a title tag with a length between 10 and 70 characters.")
            if not soup.find('meta', attrs={'name': 'description'}):
                recommendations.append("Consider adding a meta description tag for better SEO.")
            if not all(img.get('alt') for img in soup.find_all('img')):
                recommendations.append("Ensure all images have alt text for better accessibility and SEO.")
            if not soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
                recommendations.append("Consider adding heading tags (h1-h6) for better content structure and accessibility.")
        except Exception as e:
            details['api_requests'] = {'error': str(e)}
            details['link_redirects'] = {'error': str(e)}

        try:
            conn = HTTPConnection(domain)
            conn.request('HEAD', parsed_url.path)
            res = conn.getresponse()
            details['http_headers'] = dict(res.getheaders())

            security_headers = ['Content-Security-Policy', 'X-Content-Type-Options', 'X-Frame-Options', 'X-XSS-Protection', 'Strict-Transport-Security']
            for header in security_headers:
                if header not in details['http_headers']:
                    recommendations.append(f"Consider adding the {header} header for better security.")
        except Exception as e:
            details['http_headers'] = {'error': str(e)}

        if final_url.startswith('https://'):
            try:
                details['ssl_info'] = get_ssl_info(domain)
            except Exception as e:
                details['ssl_info'] = {'error': str(e)}

        try:
            geolocator = Nominatim(user_agent="website_details_app")
            location = geolocator.geocode(details['ip_address'])
            if location:
                details['geolocation'] = {
                    'latitude': location.latitude,
                    'longitude': location.longitude,
                    'address': location.address
                }
        except Exception as e:
            details['geolocation'] = {'error': str(e)}

        try:
            details['page_load_time'] = get_performance_metrics(final_url)
        except Exception as e:
            details['page_load_time'] = {'error': str(e)}

        try:
            soup = BeautifulSoup(response.text, 'html.parser')
            viewport_meta = soup.find('meta', attrs={'name': 'viewport'})
            if not viewport_meta:
                recommendations.append("Consider adding a viewport meta tag for better mobile responsiveness.")
        except Exception as e:
            details['mobile_friendliness'] = {'error': str(e)}

    except Exception as e:
        details['error'] = str(e)

    details['recommendations'] = recommendations
    return details

# Streamlit part
st.title('Website Details Fetcher')

url = st.text_input('Enter URL')

if st.button('Get Details'):
    with st.spinner('Fetching details...'):
        website_details = get_website_details(url)
        
        if 'error' in website_details:
            st.error(website_details['error'])
        else:
            st.subheader('URL')
            st.write(website_details.get('url', 'N/A'))
            
            st.subheader('IP Address')
            st.write(website_details.get('ip_address', 'N/A'))
            
            st.subheader('Technologies')
            st.write(website_details.get('technologies', 'N/A'))
            
            st.subheader('Domain Info')
            st.write(website_details.get('domain_info', 'N/A'))
            
            st.subheader('SSL Info')
            st.write(website_details.get('ssl_info', 'N/A'))
            
            st.subheader('Performance')
            st.write(f"Page Load Time: {website_details.get('page_load_time', 'N/A')} seconds")
            
            st.subheader('Recommendations')
            st.write('\n'.join(website_details.get('recommendations', [])))
            
            st.subheader('Contact Info')
            st.write(website_details.get('contact_info', 'N/A'))
            
            st.subheader('Email Addresses')
            st.write(website_details.get('email_addresses', 'N/A'))
            
            st.subheader('API Requests')
            st.write(website_details.get('api_requests', 'N/A'))
            
            st.subheader('Link Redirects')
            st.write(website_details.get('link_redirects', 'N/A'))
            
            st.subheader('HTTP Headers')
            st.write(website_details.get('http_headers', 'N/A'))
            
            st.subheader('Geolocation')
            st.write(website_details.get('geolocation', 'N/A'))
            
            st.subheader('Mobile Friendliness')
            st.write(website_details.get('mobile_friendliness', 'N/A'))
