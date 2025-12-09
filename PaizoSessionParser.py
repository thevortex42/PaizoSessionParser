import requests
from bs4 import BeautifulSoup
import lxml
import datetime
import csv
import getpass

# Define constants
OUTPUT_FILE = 'c:\\temp\\PythonPaizoParser.csv'
LOGIN_URL = 'https://paizo.com/organizedPlay/myAccount'
SESSION_URL = 'https://paizo.com/organizedPlay/myAccount/allsessions'
SESSION_TABLE_INDEX = 4
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36'

def login(session):
    """Login and acquire a session cookie"""
    loginPage = session.get(LOGIN_URL)
    
    soup = BeautifulSoup(loginPage.content, 'lxml')
    loginForm = soup.find('form')
    
    #Read hidden input fields
    form_data = {}
    for input_tag in loginForm.find_all('input'):
        name = input_tag.get('name')
        value = input_tag.get('value', '')
        form_data[name] = value

    #Obligatory form fields that are usually created via AJAX
    form_data['AJAX_SUBMIT_BUTTON_NAME'] = 'StandardPageTemplate.0.1.15.11.3.1.3.2.3.3.7.3.2.1.3.1.1.5'
    form_data['p'] = 'v5748aid7tg62'
    
    #Username and Password - TODO: Read from file!
    username = input("Paizo.com email: ")
    password = password = getpass.getpass('Password: ')
    
    form_data['e'] = username
    form_data['zzz'] = password
    
    #Get the URL we need to post the form to
    form_action = loginForm.get('action')
    action_url = requests.compat.urljoin(LOGIN_URL, form_action)
    
    #Add URL parameters
    timestamp = int(datetime.datetime.now().timestamp() * 1000)
    URL_params = '?_u=BrowsePageAjaxSignIn&' + str(timestamp)
    action_url += URL_params
    
    #Post the Data to the Login URL
    
    response = requests.post(action_url, data=form_data)
    
    session.cookies.update(response.cookies)
    
    return response.status_code
    
def getSessions(session):
    """Get the session list"""
    print("Page 1")
    sessionList = session.get(SESSION_URL)
    soup = BeautifulSoup(sessionList.content, 'lxml')
    sessionTable = soup.find_all('table')[SESSION_TABLE_INDEX]
    
    sessionListParsed = parseSessionTable(sessionTable)
    
    #Loop trough more pages
    i = 2
    while soup.find('a', string='next >'):
        print("Page "+str(i))
        i = i+1
        nextPage = soup.find('a', string='next >')['href']
        nextPageUrl = requests.compat.urljoin(LOGIN_URL, nextPage)
        sessionList = session.get(nextPageUrl)
        soup = BeautifulSoup(sessionList.content, 'lxml')
        sessionTable = soup.find_all('table')[SESSION_TABLE_INDEX]
        sessionListParsed += parseSessionTable(sessionTable)
        
    return sessionListParsed

def parseSessionTable(table):
    
    new_table = []
    
    for row in table.find_all('tr'):
        #print(row)
        new_row = dict(date='', gm='', scenario='', scenarioLink='', points='', eventId='', eventName='', eventSession='', player='', character='', faction='', prestige='', gmSession='')
        column_marker = 0
        columns = row.find_all('td')
        
        #Filter out rows that don't start with a timestamp
        if not columns or columns[0].time is None:
            continue
        
        #Parse data from valid rows
        new_row['date'] = columns[0].time['datetime'][:10]
        new_row['gm'] = columns[1].get_text().strip()
        new_row['scenario'] = columns[2].get_text().strip()
        if columns[2].a:
            new_row['scenarioLink'] = columns[2].a['href']
        #TBD: Parse Points
        #new_row['points'] = columns[3].get_text().strip()
        new_row['eventId'] = columns[4].get_text().strip()
        new_row['eventName'] = columns[5].get_text().strip()
        new_row['eventSession'] = columns[6].get_text().strip()
        new_row['player'] = columns[7].get_text().strip()
        new_row['character'] = columns[8].get_text().strip()
        new_row['faction'] = columns[9].get_text().strip()
        new_row['prestige'] = columns[10].get_text().strip()
        if columns[10].get_text().find('GM') != -1:
            new_row['gmSession'] = True
        new_row['prestige'] = columns[10].get_text().replace('GM','').strip()

        new_table.append(new_row)
    
    return new_table
    
def main():
    #Initialize Session
    session = requests.Session()
    
    print("Logging in")
    
    loginForm = login(session)
    if (loginForm == 200):
        print("Login successful")
        
    print("Getting Session List")
    sessionTable = getSessions(session)
    
    print('Exporting results to '+OUTPUT_FILE)
    
    with open(OUTPUT_FILE, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=list(sessionTable[0]))
        writer.writeheader()
        for line in sessionTable:
            writer.writerow(line)

if __name__ == "__main__":
    main()
