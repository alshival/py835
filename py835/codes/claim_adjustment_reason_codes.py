def update_codes():
    import requests
    from bs4 import BeautifulSoup
    import pandas as pd

    # URL for the Claim Adjustment Reason Codes
    url = "https://x12.org/codes/claim-adjustment-reason-codes"  # Update this to the correct URL if needed

    # Send a GET request to fetch the webpage
    response = requests.get(url)
    response.raise_for_status()  # Raise an error if the request was unsuccessful

    # Parse the webpage content
    soup = BeautifulSoup(response.text, 'html.parser')

    # Find the table containing the reason codes
    table = soup.find('table', {'id': 'codelist'})  # Adjust the selector to target the table

    # Initialize empty lists to store the data
    codes = []
    descriptions = []

    # Loop through the rows of the table and extract data
    for row in table.find('tbody').find_all('tr'):  # Loop through the table rows
        columns = row.find_all('td')
        if len(columns) >= 2:
            code = columns[0].get_text(strip=True)
            description = columns[1].get_text(strip=True)
            # Handle extra information like Start Date or Last Modified
            description = description.split("Start")[0].strip()  # Remove extra date info
            codes.append(code)
            descriptions.append(description)

    # Create a pandas DataFrame to store the data
    df = pd.DataFrame({
        'Code': codes,
        'Description': descriptions
    })

    # Save the data to a CSV file
    df.to_csv('claim_adjustment_reaspon_codes.csv',index=False)
