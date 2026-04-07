import requests
import pandas as pd
from constant import PLAYO_BOOKING_URL, PLAYO_ADD_URL, PLAYO_AVAILABILITY, PLAYO_HEADERS, PLAYO_CANCEL_URL

class PlayoO:
    def __init__(self, booking_url=PLAYO_BOOKING_URL, add_url=PLAYO_ADD_URL, availability_url=PLAYO_AVAILABILITY, headers=PLAYO_HEADERS):
        self.booking_url = booking_url
        self.add_url = add_url
        self.availability_url = availability_url
        self.cancel_url = PLAYO_CANCEL_URL
        self.headers = headers
        self.courts = {
            "Court_1": {"courtId": 27534, "courtName": "Court 1"},
            "Court_2": {"courtId": 27535, "courtName": "Court 2"},
            "Court_3": {"courtId": 27536, "courtName": "Court 3"},
            "Court_4": {"courtId": 27537, "courtName": "Court 4"}
        }

    def cancel_booking(self, bookingId):
        payload = {
            "bookingId":bookingId,
            "patternBookingId":None,
            "cancelRemarks":"",
            "playoCancelRemarks":"",
            "refundMode":"cash",
            "refundType":2,
            "transactionData":{"type":-1,"mode":1},
            "sendSMS":False
            }

        response = requests.post(self.cancel_url, headers=self.headers, json=payload)
        return response.json()

    def book_timeslot(self, date, startTime, endTime, courtName, name, pricefloat):
        price = round(pricefloat)

        add_to_cart_response = self.add_to_cart(courtName, date, startTime, endTime, price)
        if add_to_cart_response.get("requestStatus") != 1:
            return {"status": "error", "message": "Failed to add to cart"}

        payload2 = {
            "coupon": None,
            "toBeRegistered": False,
            "memberId": None,
            "nonMemberId": 3004325,
            "paymentMode": "No Pay",
            "bookingRemarks": "",
            "totalPaidAmount": 0,
            "grossAmount": 0,
            "clubDiscount": 0,
            "credits": 0,
            "customerDetails": {
                "name": 'KM '+name,
                "countryCode": "+91",
                "mobile": "000000000",
                "email": "",
                "additionalInfo": "",
                "company": "",
                "uniqueId": ""
            },
            "isPatternBooking": False,
            "patternBookingData": {},
            "transactionData": {
                "type": 1,
                "mode": 0
            },
            "sendSMS": False,
            "sendPaymentLink": False
        }

        response = requests.post(self.booking_url, headers=self.headers, json=payload2)
        return response.json()

    def add_to_cart(self, CourtName, date, startTime, endTime, price):
        court = self.courts.get(CourtName)
        if not court:
            raise ValueError("Invalid court name provided.")

        payload1 = {"slotDuration":"01:00:00","slot":{"activityId":14183,"activityType":0,"count":1,"courtId":court["courtId"],"courtName":court["courtName"],"courtBrothers":[],"slotDate":date,"slotTime":startTime,"endTime":endTime,"available":1,"blocked":False,"blockingId":None,"price":0,"slotDiscount":{}}}
        response = requests.post(self.add_url, headers=self.headers, json=payload1)
        return response.json()

    def get_availability(self, date):
        payload = {
            "activityIds": [14183],
            "activityStartDate": str(date),
            "activityEndDate": str(date),
            "customerStatus": 0
        }
        response = requests.post(self.availability_url, headers=self.headers, json=payload)
        return response.json()
    
    def extract_relevant_data(self, date, courtName):
        response = self.get_availability(date)
        if response.get("requestStatus") != 1:
            return {"status": "error", "message": "Failed to fetch availability"}

        # Extract court-wise data
        courts = response.get("data", [])
        rows = []

        for court in courts:
            court_id = court.get("courtId")
            court_name = court.get("courtName")
            for slot in court.get("slots", []):
                rows.append({
                    "courtId": court_id,
                    "courtName": court_name,
                    "slotTime": slot.get("slotTime"),
                    "endTime": slot.get("endTime"),
                    "status": slot.get("status"),
                    "available": slot.get("available"),
                    "blocked": slot.get("blocked"),
                    "bookingId": slot.get("bookingId"),
                    "customerName": slot.get("customerName"),
                    "paymentPending": slot.get("paymentPending"),
                    "price": slot.get("price", None)  # Only exists for available slots
                })

        # Create a pandas DataFrame
        df_slots = pd.DataFrame(rows)


        if not df_slots.empty:
            # Filter by courtName if provided
            if courtName:
                courtID = self.courts.get(courtName, {}).get("courtId")
                df_slots = df_slots[df_slots['courtId'] == courtID]
            return df_slots
        return pd.DataFrame()
    
    def extract_all_data(self, date):
        response = self.get_availability(date)
        if response.get("requestStatus") != 1:
            return {"status": "error", "message": "Failed to fetch availability"}

        # Extract court-wise data
        courts = response.get("data", [])
        rows = []

        for court in courts:
            court_id = court.get("courtId")
            court_name = court.get("courtName")
            for slot in court.get("slots", []):
                rows.append({
                    "courtId": court_id,
                    "courtName": court_name,
                    "slotTime": slot.get("slotTime"),
                    "endTime": slot.get("endTime"),
                    "status": slot.get("status"),
                    "available": slot.get("available"),
                    "blocked": slot.get("blocked"),
                    "bookingId": slot.get("bookingId"),
                    "customerName": slot.get("customerName"),
                    "paymentPending": slot.get("paymentPending"),
                    "price": slot.get("price", None)  # Only exists for available slots
                })

        # Create a pandas DataFrame
        df_slots = pd.DataFrame(rows)


        if not df_slots.empty:
            return df_slots
        return pd.DataFrame()