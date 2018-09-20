import requests # used for handling http requests
import argparse # used for handling user inputs to the script
from sys import exit # used to terminate script on connection exception
from functools import wraps # used to create decorator for handling exceptions on request functions

# decorator that is used on FlightBooker class functions that handle http requests
# cathing connection and http exceptions
def handling_request(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            f_outcome = f(*args, **kwargs)
        except requests.exceptions.HTTPError as e:
            print(e)
            exit(1)
        except requests.exceptions.ConnectionError:
            print("Failed to establish connection, check your internet settings and try again")
            exit(1)
        except requests.exceptions.Timeout:
            print("Connection timed out")
            exit(1)

        return f_outcome

    return decorated_function

class InputHandler(argparse.ArgumentParser):
    # wrapper class around argparse.ArgumentParser handling all input parameters
    # to the script
    def __init__(self):
        super().__init__()

        self.add_argument('--date', help='Specify departure date in "dd/mm/YYYY" format',
                            type=str, required=True)
        self.add_argument('--flight_from', help='Specify departure airport IATA code',
                            type=str, required=True)
        self.add_argument('--to', help='Specify destination airport IATA code',
                            type=str, required=True)

        trip_type = self.add_mutually_exclusive_group()
        trip_type.add_argument('--one_way', help='Search only for one-way ticket, default option',
                                action='store_true', default=True)
        trip_type.add_argument('--returning', help='Specify number of nights to stay in destination',
                            type=int)

        trip_priority = self.add_mutually_exclusive_group()
        trip_priority.add_argument('--cheapest', help='Search for cheapest flight',
                                    action='store_true')
        trip_priority.add_argument('--fastest', help='Search for fastest flight',
                                    action='store_true')

        self.add_argument('--direct', help='Use if want to search only for direct flights',
                            action='store_true', default=False)

        self.add_argument('--bags', help='Specify how many big luggage you will carry, default is 0',
                            type=int, default=0)

        self.args = self.parse_args()

        # setting cheapest to true if fastest wasn't selected - making cheapest as a default
        if not self.args.fastest:
            self.args.cheapest = True

        # setting one_way to true if returning wasn't selected - making one-way as a default
        if not self.args.returning:
            self.args.one_way = True

class FlightBooker():
    # class handling request and performing all search and booking functions
    # is initialized with parsed input arguments handled by InputHandler class,
    # user details, search and booking uri
    def __init__(self, input_config, search_uri, booking_uri, user_details):
        self.search_uri = search_uri
        self.booking_uri = booking_uri
        self.user_details = user_details
        self.input_config = input_config
        self.flight_filter = self.set_filter()
        self.flight_to_book = None

    def set_filter(self):
        # Configures search query filter based on input arguments
        fly_from = self.input_config.flight_from
        fly_to = self.input_config.to
        date_from = self.input_config.date
        date_to = self.input_config.date
        partner = 'picky'
        direct_flights = 1 if self.input_config.direct else 0
        one_for_city = 1 if self.input_config.cheapest else 0 # this parameter is narrowing down the returend flight to one cheapest per city
        flight_type = 'round' if self.input_config.returning else 'oneway'
        days_in_destination = self.input_config.returning

        return {
                'flyFrom': fly_from,
                'to': fly_to,
                'dateFrom': date_from,
                'dateTo': date_to,
                'partner': partner,
                'directFlights': direct_flights,
                'oneforcity': one_for_city,
                'typeFlight': flight_type,
                'daysInDestinationFrom': days_in_destination,
                'daysInDestinationTo': days_in_destination
            }

    def handle_booking(self):
        # main fucntion that handles the flight search and booking
        self.search_message()
        flights_data = self.get_flights()

        if flights_data:
            self.flight_to_book = self.search_flight(flights_data)
            self.show_flight_details()
            self.proceed_with_booking()

        else:
            print("No suitable flights were found based on your criteria")

    def search_message(self):
        flight_priority = 'cheapest' if self.input_config.cheapest else 'fastest'
        message = f"Searching for {flight_priority}, {self.flight_filter['typeFlight']} flight, from {self.flight_filter['flyFrom']} to {self.flight_filter['to']}"
        print(message)

    @handling_request
    def get_flights(self):
        # performs get request on flight search endpoint returning found flights data
        r = requests.get(self.search_uri, params=self.flight_filter)
        r.raise_for_status()

        if r.status_code == 200:
            return r.json()['data']

    def search_flight(self, flights_data):
        # function that search for most suitable flight based on input criteria
        # if there is only one flight returned it means it is also the cheapest
        # and fastest
        if len(flights_data) == 1:
            return flights_data[0]
        # else search for cheapest flight if cheapest criteria was selected
        elif self.input_config.cheapest:
            return self.find_cheapest_flight(flights_data)
        #else search for fastest flight
        else:
            return self.find_fastest_flight(flights_data)

    @staticmethod
    def find_fastest_flight(flights_data):
        # iterates over all fligts comparing flight duration and returns shortest flight
        fastest_flight = flights_data[0]
        min_duration = fastest_flight['duration']['total']
        for flight in flights_data[1:]:
            flight_duration = flight['duration']['total']
            if flight_duration < min_duration:
                min_duration = flight_duration
                fastest_flight = flight

        return fastest_flight

    @staticmethod
    def find_cheapest_flight(flights_data):
        # iterates over all fligts comparing price and returns cheapest flight
        cheapest_flight = flights_data[0]
        min_price = cheapest_flight['price']
        for flight in flights_data[1:]:
            flight_price = flight['price']
            if flight_price < min_price:
                min_price = flight_price
                cheapest_flight = flight

        return cheapest_flight

    def show_flight_details(self):
        # prints details of the flight to be booked
        print("")
        if not self.flight_to_book:
            print("No suitable flight was found")
        else:
            print(f"Flight from: {self.flight_to_book['flyFrom']}")
            print(f"To: {self.flight_to_book['flyTo']}")
            print(f"Price: {self.flight_to_book['price']} EUR")
            print(f"Flight duration: {self.flight_to_book['fly_duration']}")
            if self.input_config.returning:
                print(f"Return duration: {self.flight_to_book['return_duration']}")

    def proceed_with_booking(self):
        # asks user to confirm booking and completes it
        print("")
        choice = ''
        while choice.lower() not in ('y', 'n'):
            choice = input("Do you wish to book the flight? y/n: ")
            if choice.lower() == 'y':
                self.book_flight()
            elif choice.lower() == 'n':
                print("Flight wasn't booked")

    @handling_request
    def book_flight(self):
        # sends post request to booking endpoint and confirms user with booking
        # id of the flight
        headers = {'Content-Type': 'application/json'}

        # booking data structure with prefilled info, completing passengers details
        # number of bags and booking token from the class parameters
        booking_data = {
                "lang":"en",
                "bags": self.input_config.bags,
                "passengers":[ self.user_details ],
                "locale":"en",
                "currency":"gbp",
                "customerLoginID":"unknown",
                "customerLoginName":"unknown",
                "booking_token": self.flight_to_book['booking_token'],
                "affily":"affil_id",
                "booked_at":"affil_id",
                }

        print("")
        print(f"Booking flight with {booking_data['bags']} bags")

        r = requests.post(self.booking_uri, data=booking_data, headers=headers)
        r.raise_for_status()

        if r.status_code in (200, 201):
            data = r.json()
            print(f"Your flight was booked, booking id: {data['booking_id']}")

if __name__ == '__main__':

    # production kiwi endpoint for flight search
    search_uri = 'https://api.skypicker.com/flights'
    # mock kiwi endooint for flight booking, if produciton endpoint would to be used
    # check flights step veryfying actual flight price and availability will have to
    # be implemented prior to booking the flight
    booking_uri = 'https://private-anon-7a22d853a6-skypickerbookingapi1.apiary-mock.com/api/v0.1/save_booking?v=2'
    # test user details, in production like scenario it would probably come
    # from user profile/form completed on the webpage
    test_user = {
          "name": "test",
          "surname": "test",
          "title": "ms",
          "phone": "+44 45662344432",
          "birthday": 326246400,
          "expiration": 1760054400,
          "cardno": "XXXXXXXX",
          "nationality": "CZ",
          "email": "email.address@gmail.com",
          "category": "adults",
          }

    input_handler = InputHandler()
    flight_booker = FlightBooker(input_handler.args, search_uri, booking_uri, test_user)
    flight_booker.handle_booking()
