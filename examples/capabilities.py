import requests
from bs4 import BeautifulSoup

def google_search(query, num_results=10):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    url = f"https://www.google.com/search?q={query.replace(' ', '+')}&num={num_results}"
    
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        raise Exception(f"Erreur lors de la requête : {response.status_code}")
    
    soup = BeautifulSoup(response.text, "html.parser")
    results = []
    
    for result in soup.select(".tF2Cxc"):
        title = result.select_one("h3").text if result.select_one("h3") else None
        link = result.select_one("a")["href"] if result.select_one("a") else None
        description = result.select_one(".VwiC3b").text if result.select_one(".VwiC3b") else None
        
        if title and link:
            results.append({"title": title, "link": link, "description": description})
    
    return results


def get_page_content(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        raise Exception(f"Erreur lors de la requête : {response.status_code}")
    
    # extract text from HTML
    soup = BeautifulSoup(response.text, "html.parser")
    for script in soup(["script", "style"]):
        script.extract()
    return soup.get_text()