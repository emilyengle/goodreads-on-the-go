from flask import Flask, request
from rauth.service import OAuth1Session
from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse
import os
import xml.etree.ElementTree as ET

app = Flask(__name__)
global book_ids
book_ids = []

@app.route("/sms", methods=['GET', 'POST'])
def handle_incoming_sms():
    body = request.form['Body']

    key = os.environ.get('GOODREADS_API_KEY')
    session = get_goodreads_session(key)

    resp = MessagingResponse()

    if 'add' in body.lower():
        response = handle_new_query(body, key, session)
        resp.message(response)
        return str(resp)
    else:
        response = handle_book_to_add(body, session)
        resp.message(response)
        return str(resp)

# Handle "add [title]" message by sending search results back to user
def handle_new_query(msg, key, session):
    title = msg[4:]
    search_results = get_search_results(session, key, title)

    resp_msg = parse_search_results(search_results)
    return resp_msg

# Handle "[number]" message with user specifying book to add to list
def handle_book_to_add(msg, session):
    if not book_ids:
        return 'Please search for a book by texting \'add [title]\''

    add_url = 'https://www.goodreads.com/shelf/add_to_shelf.xml'
    add_data = {'name': 'to-read', 'book_id': book_ids[int(msg) - 1]}
    add_response = session.post(add_url, add_data)

    if add_response.status_code != 201:
        return 'Your book could not be added.'
    else:
        global book_ids
        book_ids = []
        return 'Book added!'

# Set up Goodreads session to make calls to their api
def get_goodreads_session(key):
    secret = os.environ.get('GOODREADS_API_SECRET')

    access_token = os.environ.get('GOODREADS_ACCESS_TOKEN')
    access_token_secret = os.environ.get('GOODREADS_ACCESS_TOKEN_SECRET')

    session = OAuth1Session(
        consumer_key=key,
        consumer_secret=secret,
        access_token=access_token,
        access_token_secret=access_token_secret
    )

    return session

# Query Goodreads for search results given title
def get_search_results(session, key, title):
    search_url = 'https://www.goodreads.com/search/index.xml'
    search_data = {'q': title, 'key': key}
    search_response = session.post(search_url, search_data)
    root = ET.fromstring(search_response.content)
    return root

# Parse search results and format response message for user
def parse_search_results(root):
    counter = 1
    global book_ids
    book_ids = []
    resp_msg = 'Your search results: '
    for result in root.iter('work'):
        book = result.find('best_book')
        if book is not None:
            id = book.find('id').text
            title = book.find('title').text
            author = book.find('author').find('name').text
            pub_year = result.find('original_publication_year').text
            resp_msg += '\n %s - %s by %s, %s' % (str(counter), title, author, pub_year)
            book_ids.append(id)
            counter += 1
            if counter >= 10:
                break
    resp_msg += '\n\nText back the number of the book to add to your list.'
    return resp_msg

if __name__ == "__main__":
    app.run(debug=True)
