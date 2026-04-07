import requests
import pandas as pd
from constant import KHELOMORE_URL, KHELOMORE_HEADERS

class KMO:
    def __init__(self, url=KHELOMORE_URL, headers=KHELOMORE_HEADERS):
        self.url = url
        self.headers = headers
        self.courts = {
            "Court_1": 7700,
            "Court_2": 7699,
            "Court_3": 7701,
            "Court_4": 7702
        }

    def block_timeslot(self, date, startTime, endTime, courtName, name):
        courtId = self.courts.get(courtName)
        blockreason = f"playo {name}"
        payload = {
            "operationName": "bulkBlockSlot",
            "variables": {
                "input": [
                    {
                        "startDate": date,
                        "startTime": startTime,
                        "endDate": date,
                        "endTime": endTime,
                        "propertyId": courtId,
                        "day": [],
                        "blockSlotCount": 0,
                        "repeatWeekCount": 1
                    }
                ],
                "blockreason": blockreason
            },
            "query": "mutation bulkBlockSlot($input: [BulkBlockDto]!, $blockreason: String!) {\n  bulkBlockSlot(input: $input, blockreason: $blockreason) {\n    message\n    code\n    data\n  }\n}"
        }
        response = requests.post(self.url, headers=self.headers, json=payload)
        return response.json()

    def unblock_timeslot(self, timeSlotId):
        payload = {
            "operationName": "unblockBulkTimeSlot",
            "variables": {
                "timeSlotId": timeSlotId
            },
            "query": "mutation unblockBulkTimeSlot($timeSlotId: [Int]) {\n  unblockBulkTimeSlot(timeSlotId: $timeSlotId) {\n    message\n    code\n    data\n  }\n}"
        }
        response = requests.post(self.url, headers=self.headers, json=payload)
        return response.json()

    def get_timeslots(self, date, courtName):
        courtId = self.courts.get(courtName)
        payload = {
            "operationName": "fetchAllSlotByVenue",
            "variables": {
                "propertyIds": [courtId],
                "venueId": 2299,
                "date": date,
                "type": None
            },
            "query": """query fetchAllSlotByVenue($propertyIds: [Int], $venueId: Int!, $date: String!, $type: String) {
                fetchAllSlotByVenue(propertyIds: $propertyIds, venueId: $venueId, date: $date, type: $type) {
                    message
                    code
                    status
                    data {
                        grandTotal
                        venueName
                        status
                        isReAllocatedBooking
                        bookingId
                        bookingDate
                        bookingNumber
                        venueName
                        bookingMode
                        pendingAmount
                        venueType
                        isBulkBooking
                        refundAmount
                        staffName
                        staffEmail
                        multiSlotCount
                        bookedMultiSlotCount
                        blockMultiSlotCount
                        isMultiSlot
                        vasfinaltotal
                        bookingCustomer {
                            email
                            name
                            phone
                            gst
                        }
                        timeslots {
                            timeslotId
                            date
                            startTime
                            endTime
                            duration
                            price
                            discountedPrice
                            propertyId
                            propertyName
                            propertyDimension
                            timeslotPrice
                            timeslotStatus
                            timeslotReason
                            staffName
                            staffEmail
                        }
                        bookingPayments {
                            paymentMode
                            paymentAmount
                            pgOrderId
                            pgTransactionId
                            transactionTime
                            creditAmount
                        }
                        vasProducts {
                            vasProductName
                            vasIsRental
                            vasProductQuantity
                            vasItemSubtotal
                            vasBookedMinutes
                            vasConvFee
                            vasFinalTotal
                            prevtotal
                            prevsubtotal
                        }
                    }
                }
            }"""
        }
        response = requests.post(self.url, headers=self.headers, json=payload)
        return response.json()
    
    def extract_relevant_data(self, date, courtName):

        data = self.get_timeslots(date, courtName)
        if 'errors' in data:
            return None
        # Extract the relevant data path: ["data"]["fetchAllSlotByVenue"]["data"]
        bookings_data = data['data']['fetchAllSlotByVenue']['data']

        # Initialize an empty list to store flattened data
        flattened_data = []

        # Iterate through each booking and its timeslots to flatten the structure
        for booking in bookings_data:
            venue_name = booking.get('venueName')
            booking_status = booking.get('status')
            booking_id = booking.get('bookingId')
            booking_date_time = booking.get('bookingDate')
            booking_number = booking.get('bookingNumber')
            grand_total = booking.get('grandTotal')
            bookingCustomer = booking.get('bookingCustomer') or {}
            customerEmail = bookingCustomer.get('email','') if len(bookingCustomer) > 0 else ''
            customerName = bookingCustomer.get('name','') if len(bookingCustomer) > 0 else ''
            customerPhone = bookingCustomer.get('phone','') if len(bookingCustomer) > 0 else ''


            # Each booking can have multiple timeslots, so iterate through them
            for timeslot in booking.get('timeslots', []):
                flattened_data.append({
                    'venueName': venue_name,
                    'bookingStatus': booking_status,
                    'bookingId': booking_id,
                    'bookingDateTime': booking_date_time,
                    'bookingNumber': booking_number,
                    'grandTotal': grand_total,
                    'customerName' : customerName,
                    'customerPhone' : customerPhone,
                    'timeslotId': timeslot.get('timeslotId'),
                    'timeslotDate': timeslot.get('date'),
                    'startTime': timeslot.get('startTime'),
                    'endTime': timeslot.get('endTime'),
                    'propertyName': timeslot.get('propertyName'),
                    'timeslotStatus': timeslot.get('timeslotStatus'),
                    'timeslotReason': timeslot.get('timeslotReason'),
                    'staffName': timeslot.get('staffName'),
                    'staffEmail': timeslot.get('staffEmail')
                })

        # Create the DataFrame from the flattened data
        if flattened_data:
            df = pd.DataFrame(flattened_data)
            return df
        return pd.DataFrame()