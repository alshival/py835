def update():
    import requests
    from bs4 import BeautifulSoup
    import pandas as pd
    # URL for the Claim Status Category Codes
    url = "https://x12.org/codes/claim-status-category-codes"

    # Send a GET request to fetch the webpage
    response = requests.get(url)
    response.raise_for_status()  # Raise an error if the request was unsuccessful

    # Parse the webpage content
    soup = BeautifulSoup(response.text, 'html.parser')

    # Find the table containing the claim status category codes
    table = soup.find('table', {'id': 'codelist'})

    # Initialize empty lists to store the data
    codes = []
    descriptions = []

    # Loop through the rows of the table and extract data
    for row in table.find('tbody').find_all('tr'):
        columns = row.find_all('td')
        if len(columns) >= 2:
            code = columns[0].get_text(strip=True)
            description = columns[1].get_text(strip=True)
            codes.append(code)
            descriptions.append(description)

    # Create a pandas DataFrame to store the data
    df = pd.DataFrame({
        'Code': codes,
        'Description': descriptions
    })

    # Save the data to a CSV file
    df.to_csv('claim_status_category_codes.csv', index=False)
    print("Data has been scraped and saved to 'claim_status_category_codes.csv'")