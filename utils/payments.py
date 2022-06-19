from coinbase_commerce.client import Client


class Payment:
    def __init__(self):
        self.client = Client(api_key="84bf74fb-e49a-4f08-b1df-17a0c58694e3")
        self._get_all_charges()

    def _get_all_charges(self):
        return list(self.client.charge.list_paging_iter())

    def get(self, charge_id):
        for chrg in self._get_all_charges():
            if chrg["id"] == charge_id:
                return self.client.charge.retrieve(charge_id)
        return None

    def create(self, price):
        return self.client.charge.create(name="AC KeyGen Access",
                                         description="Payment for continued use of AC Product's KeyGen Access",
                                         pricing_type="fixed_price",
                                         local_price={
                                             "amount": str(price),
                                             "currency": "USD"
                                         },
                                         requested_info=["name", "email"])


if __name__ == "__main__":
    payment = Payment()
    charge = payment.get("42d78173-dac4-42c9-ad3d-d2ebcfc5cca9")
    print(charge)
