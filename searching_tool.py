import webbrowser
from urllib.parse import quote_plus

n_signs = 250

def open_search(query: str, engine: str = "duckduckgo"):
    q = " ".join(query.split())          
    q = q[:n_signs]                         
    q = f"\"{q}\""                       

    encoded = quote_plus(q)

    if engine == "google":
        url = f"https://www.google.com/search?q={encoded}"
    elif engine == "bing":
        url = f"https://www.bing.com/search?q={encoded}"
    else:  
        url = f"https://duckduckgo.com/?q={encoded}"

    webbrowser.open(url)

open_search("Składowa elektryczna i magnetyczna fali indukują się wzajemnie – zmieniające się pole elektryczne wytwarza zmieniające się pole magnetyczne, a z kolei zmieniające się pole magnetyczne wytwarza zmienne pole elektryczne. ")