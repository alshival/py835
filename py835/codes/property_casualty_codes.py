def update():
    import requests
    from bs4 import BeautifulSoup
    import pandas as pd
    # URL for the Property & Casualty Code Lists
    url = "https://x12.org/codes/property-casualty-code-lists"

    # Send a GET request to fetch the webpage
    response = requests.get(url)
    response.raise_for_status()

    # Parse the webpage content
    soup = BeautifulSoup(response.text, 'html.parser')

    # Find all sections with code lists
    sections = soup.find_all('div', {'class': 'code_list_accordion__code-list-table'})

    # Initialize lists to store the scraped data
    all_data = []

    # Loop through each section to extract codes and descriptions
    for section in sections:
        # Find the table within each section
        table = section.find('table', {'id': 'codelist'})

        if table:
            # Extract all rows from the table
            rows = table.find('tbody').find_all('tr')

            for row in rows:
                columns = row.find_all('td')
                if len(columns) >= 2:
                    code = columns[0].get_text(strip=True)
                    description = columns[1].get_text(strip=True)
                    all_data.append({'Code': code, 'Description': description})

    # Create a pandas DataFrame to store the data
    df = pd.DataFrame(all_data)

    # Save the data to a CSV file
    df.to_csv('property_casualty_codes.csv', index=False)
    print("Data has been scraped and saved to 'property_casualty_codes.csv'")