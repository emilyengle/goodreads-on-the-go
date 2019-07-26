import sys, os
import xml.etree.ElementTree as ET
from rauth.service import OAuth1Service, OAuth1Session
from termcolor import colored

key = os.environ.get('GOODREADS_API_KEY')
secret = os.environ.get('GOODREADS_API_SECRET')

access_token = os.environ.get('GOODREADS_ACCESS_TOKEN')
access_token_secret = os.environ.get('GOODREADS_ACCESS_TOKEN_SECRET')

if access_token and access_token_secret:
    session = OAuth1Session(
        consumer_key=key,
        consumer_secret=secret,
        access_token=access_token,
        access_token_secret=access_token_secret
    )
    print colored('Authorization successful; continuing.', 'green')
else:
    # Authorize new user
    goodreads = OAuth1Service(
        consumer_key=key,
        consumer_secret=secret,
        name='goodreads',
        request_token_url='https://www.goodreads.com/oauth/request_token',
        authorize_url='https://www.goodreads.com/oauth/authorize',
        access_token_url='https://www.goodreads.com/oauth/access_token',
        base_url='https://www.goodreads.com'
    )

    request_token, request_token_secret = goodreads.get_request_token(header_auth=True)
    authorize_url = goodreads.get_authorize_url(request_token)
    print 'Visit this to authorize: ', authorize_url

    raw_input('Press enter to continue once you authorize... ')

    try:
        session = goodreads.get_auth_session(request_token, request_token_secret)
        print colored('Authorization successful; continuing.', 'green')
    except:
        print colored('Authorization failed; try again.', 'red')
        sys.exit()

# Find book for user
continue_adding = True
while continue_adding:
    title = raw_input('Enter title of book you want to read: ')
    search_url = 'https://www.goodreads.com/search/index.xml'
    search_data = {'q': title, 'key': key}
    search_response = session.post(search_url, search_data)

    # Parse and display search results
    root = ET.fromstring(search_response.content)
    results_count = root.find('search').find('total-results').text
    results_displayed = root.find('search').find('results-end').text
    print "\nFound %s results; displaying first %s below." % (results_count, results_displayed)
    counter = 1
    book_ids = []
    for result in root.iter('work'):
        book = result.find('best_book')
        if book is not None:
            id = book.find('id').text
            title = book.find('title').text
            author = book.find('author').find('name').text
            pub_year = result.find('original_publication_year').text
            print str(counter), '- ', colored(title, 'blue'), "by %s, %s" % (author, pub_year)
            book_ids.append(id)
            counter += 1

    # Add book to user's To Read shelf
    book_to_add = raw_input('\nEnter number of book to add to shelf: ')
    add_url = 'https://www.goodreads.com/shelf/add_to_shelf.xml'
    add_data = {'name': 'to-read', 'book_id': book_ids[int(book_to_add) - 1]}
    add_response = session.post(add_url, add_data)
    if add_response.status_code != 201:
        raise StandardError('Book cannot be added to shelf.')
    else:
        print colored('Book added!', 'green')

    # Prompt to add another book or exit
    input = raw_input('Add another book? (y/n): ')
    continue_adding = True if input.lower() == 'y' else False
