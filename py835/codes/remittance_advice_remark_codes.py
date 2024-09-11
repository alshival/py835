def update():
    import requests
    from bs4 import BeautifulSoup
    import pandas as pd
    # URL for the Remittance Advice Remark Codes
    url = "https://x12.org/codes/remittance-advice-remark-codes"

    # Send a GET request to fetch the webpage
    response = requests.get(url)
    response.raise_for_status()  # Raise an error if the request was unsuccessful

    # Parse the webpage content
    soup = BeautifulSoup(response.text, 'html.parser')

    # Find the table containing the remark codes
    table = soup.find('table', {'id': 'codelist'})  # Adjust the selector to target the correct table

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
    df.to_csv('remittance_advice_remark_codes.csv', index=False)
    print("Data has been scraped and saved to 'remittance_advice_remark_codes.csv'")