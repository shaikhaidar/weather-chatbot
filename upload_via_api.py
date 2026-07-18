import requests

def main():
    csv_path = r"e:\weatherBOT\data\weather.csv"
    url = "http://localhost:8000/api/datasets/upload"
    
    with open(csv_path, 'rb') as f:
        files = {'file': ('weather.csv', f, 'text/csv')}
        print("Uploading dataset to weatherBOT API...")
        response = requests.post(url, files=files)
        
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")

if __name__ == "__main__":
    main()
