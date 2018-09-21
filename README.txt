This small project was done as entry test for python weekend course conducted by Kiwi.

It allows user to search for flights using Kiwi API via command line interface.
There is also booking confirmation fuctionality implemented, however using mock kiwi
endpoint, so no flights could be truly booked. Search is done using production
endpoint so all flight details are real.

User can specifiy following arguments as input to the script:

mandatory:
--date 17/09/2018           Departure date
--flight_from PRG           IATA code of departure airport
--to LGW                    IATA code of arrival airport

optional:
--one_way or --returning 5  one way or returning flight with number of days to stay, default is one way
--cheapest or --fastest     search for cheapest or fastest flight, default is cheapest
--direct                    search only for direct flights
--bags 1                    specify number of big luggage, default is 0

example of usage:
flight_booking.py --date 17/09/2018 --flight_from PRG --to LGW --returning 5 --fastest --direct --bags 1

- will search for returning fastest flight to stay 5 days in destination, only direct routes,
from Prague airport to London Gatwick with one big luggage
