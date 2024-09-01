import requests
import json
import os
import re
from dotenv import load_dotenv

load_dotenv(override=True)

ITEM_URL = "https://www.ubisoft.com/fr-fr/game/rainbow-six/siege/marketplace?route=buy%2Fitem-details&itemId=a1f831aa-b6fd-08ce-13e9-45ab2397d998"

AUTH_TOKEN = os.getenv("AUTH_TOKEN")
SESSION_ID = os.getenv("SESSION_ID")
APP_ID = os.getenv("APP_ID")
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:129.0) Gecko/20100101 Firefox/129.0",
    "Accept": "*/*",
    "Accept-Language": "en-US,en;q=0.5",
    "Content-Type": "application/json",
    "ubi-appid": APP_ID,
    "ubi-sessionid": SESSION_ID,
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "cross-site",
    "authorization": f"ubi_v1 t={AUTH_TOKEN}",
}


def get_item_id_space_id(url):
    re_space_id = re.compile(r"\"activeGameSpaceId\":\"(.*?)\"")

    response = requests.get(url)

    try:
        item_id = url.split("itemId=")[1]
        space_id = re_space_id.search(response.text).group(1)
    except AttributeError:
        return None, None

    return item_id, space_id


def get_market_information(item_id, space_id):
    url = "https://public-ubiservices.ubi.com/v1/profiles/me/uplay/graphql"

    body = [
        {
            "operationName": "GetItemDetails",
            "variables": {
                "spaceId": space_id,
                "itemId": item_id,
            },
            "query": """
                query GetItemDetails(
                    $spaceId: String!
                    $itemId: String!
                ) {
                    game(spaceId: $spaceId) {
                        marketableItem(itemId: $itemId) {
                            item {
                                ...SecondaryStoreItemFragment
                                ...SecondaryStoreItemOwnershipFragment
                            }
                            marketData {
                                ...MarketDataFragment
                            }
                        }
                    }
                }

                fragment SecondaryStoreItemFragment on SecondaryStoreItem {
                    name
                    type
                }

                fragment SecondaryStoreItemOwnershipFragment on SecondaryStoreItem {
                    viewer {
                        meta {
                            isOwned
                        }
                    }
                }

                fragment MarketDataFragment on MarketableItemMarketData {
                    sellStats {
                        paymentItemId
                        lowestPrice
                        highestPrice
                    }
                }
            """,
        }
    ]

    try:
        response = requests.post(url, headers=HEADERS, json=body)
    except UnicodeEncodeError:
        print(
            "[!] There was a problem with the parsing of the auth token. There are invalid characters in your token."
        )
        os._exit(1)

    json_response = response.json()[0]

    if "expired" in json.dumps(json_response) or "INVALID_TICKET" in json.dumps(
        json_response
    ):
        return None, None, None

    name = json_response["data"]["game"]["marketableItem"]["item"]["name"]
    skin_type = json_response["data"]["game"]["marketableItem"]["item"]["type"]
    is_owned = json_response["data"]["game"]["marketableItem"]["item"]["viewer"][
        "meta"
    ]["isOwned"]

    paymentItemId = json_response["data"]["game"]["marketableItem"]["marketData"][
        "sellStats"
    ][0]["paymentItemId"]
    lowest_sell_price = json_response["data"]["game"]["marketableItem"]["marketData"][
        "sellStats"
    ][0]["lowestPrice"]

    print(f"Name: {name}\n" f"Type: {skin_type}\n" f"Is owned: {is_owned}\n")

    return is_owned, paymentItemId, lowest_sell_price


def get_balance():
    url = "https://public-ubiservices.ubi.com/v1/profiles/me/uplay/graphql"

    body = [
        {
            "operationName": "GetBalance",
            "variables": {
                "spaceId": "0d2ae42d-4c27-4cb7-af6c-2099062302bb",
                "itemId": "9ef71262-515b-46e8-b9a8-b6b6ad456c67",
            },
            "query": """
                query GetBalance($spaceId: String!, $itemId: String!) {
                    game(spaceId: $spaceId) {
                        viewer {
                            meta {
                                secondaryStoreItem(itemId: $itemId) {
                                    meta {
                                        quantity
                                    }
                                }
                            }
                        }
                    }
                }
            """,
        }
    ]

    response = requests.post(url, headers=HEADERS, json=body)

    json_response = response.json()[0]

    balance = json_response["data"]["game"]["viewer"]["meta"]["secondaryStoreItem"][
        "meta"
    ]["quantity"]

    return int(balance)


def create_buy_order(item_id: str, space_id: str, payment_item_id: str, price: int):
    url = "https://public-ubiservices.ubi.com/v1/profiles/me/uplay/graphql"

    body = [
        {
            "operationName": "CreateBuyOrder",
            "variables": {
                "spaceId": space_id,
                "tradeItems": [{"itemId": item_id, "quantity": 1}],
                "paymentProposal": {
                    "paymentItemId": payment_item_id,
                    "price": price,
                },
            },
            "query": """
                mutation CreateBuyOrder($spaceId: String!, $tradeItems: [TradeOrderItem!]!, $paymentProposal: PaymentItem!) {
                    createBuyOrder(
                        spaceId: $spaceId
                        tradeItems: $tradeItems
                        paymentProposal: $paymentProposal
                    ) {
                        trade {
                            ...TradeFragment
                            __typename
                        }
                        __typename
                    }
                }

                fragment TradeFragment on Trade {
                    id
                    tradeId
                    state
                    category
                    createdAt
                    expiresAt
                    lastModifiedAt
                    failures
                    tradeItems {
                        id
                        item {
                            ...SecondaryStoreItemFragment
                            ...SecondaryStoreItemOwnershipFragment
                            __typename
                        }
                        __typename
                    }
                    payment {
                        id
                        item {
                            ...SecondaryStoreItemQuantityFragment
                            __typename
                        }
                        price
                        transactionFee
                        __typename
                    }
                    paymentOptions {
                        id
                        item {
                            ...SecondaryStoreItemQuantityFragment
                            __typename
                        }
                        price
                        transactionFee
                        __typename
                    }
                    paymentProposal {
                        id
                        item {
                            ...SecondaryStoreItemQuantityFragment
                            __typename
                        }
                        price
                        __typename
                    }
                    viewer {
                        meta {
                            id
                            tradesLimitations {
                                ...TradesLimitationsFragment
                                __typename
                            }
                            __typename
                        }
                        __typename
                    }
                    __typename
                }

                fragment SecondaryStoreItemFragment on SecondaryStoreItem {
                    id
                    assetUrl
                    itemId
                    name
                    tags
                    type
                    viewer {
                        meta {
                            id
                            isReserved
                            __typename
                        }
                        __typename
                    }
                    __typename
                }

                fragment SecondaryStoreItemOwnershipFragment on SecondaryStoreItem {
                    viewer {
                        meta {
                            id
                            isOwned
                            quantity
                            __typename
                        }
                        __typename
                    }
                    __typename
                }

                fragment SecondaryStoreItemQuantityFragment on SecondaryStoreItem {
                    viewer {
                        meta {
                            id
                            quantity
                            __typename
                        }
                        __typename
                    }
                    __typename
                }

                fragment TradesLimitationsFragment on UserGameTradesLimitations {
                    id
                    buy {
                        resolvedTransactionCount
                        resolvedTransactionPeriodInMinutes
                        activeTransactionCount
                        __typename
                    }
                    sell {
                        resolvedTransactionCount
                        resolvedTransactionPeriodInMinutes
                        activeTransactionCount
                        resaleLocks {
                            itemId
                            expiresAt
                            __typename
                        }
                        __typename
                    }
                    __typename
                }
            """,
        }
    ]

    response = requests.post(url, headers=HEADERS, json=body)

    json_response = response.json()[0]

    state = json_response["data"]["createBuyOrder"]["trade"]["state"]

    tradeId = json_response["data"]["createBuyOrder"]["trade"]["tradeId"]

    if state == "Created":
        print(f"Trying to buy item for {price} credits.", end="\r", flush=True)
        return tradeId

    return False


def cancel_order(space_id: str, trade_id: str):
    url = "https://public-ubiservices.ubi.com/v1/profiles/me/uplay/graphql"

    body = [
        {
            "operationName": "CancelOrder",
            "variables": {
                "spaceId": space_id,
                "tradeId": trade_id,
            },
            "query": """
                mutation CancelOrder($spaceId: String!, $tradeId: String!) {
                    cancelOrder(spaceId: $spaceId, tradeId: $tradeId) {
                        trade {
                            ...TradeFragment
                            __typename
                        }
                        __typename
                    }
                }

                fragment TradeFragment on Trade {
                    id
                    tradeId
                    state
                    category
                    createdAt
                    expiresAt
                    lastModifiedAt
                    failures
                    tradeItems {
                        id
                        item {
                            ...SecondaryStoreItemFragment
                            ...SecondaryStoreItemOwnershipFragment
                            __typename
                        }
                        __typename
                    }
                    payment {
                        id
                        item {
                            ...SecondaryStoreItemQuantityFragment
                            __typename
                        }
                        price
                        transactionFee
                        __typename
                    }
                    paymentOptions {
                        id
                        item {
                            ...SecondaryStoreItemQuantityFragment
                            __typename
                        }
                        price
                        transactionFee
                        __typename
                    }
                    paymentProposal {
                        id
                        item {
                            ...SecondaryStoreItemQuantityFragment
                            __typename
                        }
                        price
                        __typename
                    }
                    viewer {
                        meta {
                            id
                            tradesLimitations {
                                ...TradesLimitationsFragment
                                __typename
                            }
                            __typename
                        }
                        __typename
                    }
                    __typename
                }

                fragment SecondaryStoreItemFragment on SecondaryStoreItem {
                    id
                    assetUrl
                    itemId
                    name
                    tags
                    type
                    viewer {
                        meta {
                            id
                            isReserved
                            __typename
                        }
                        __typename
                    }
                    __typename
                }

                fragment SecondaryStoreItemOwnershipFragment on SecondaryStoreItem {
                    viewer {
                        meta {
                            id
                            isOwned
                            quantity
                            __typename
                        }
                        __typename
                    }
                    __typename
                }

                fragment SecondaryStoreItemQuantityFragment on SecondaryStoreItem {
                    viewer {
                        meta {
                            id
                            quantity
                            __typename
                        }
                        __typename
                    }
                    __typename
                }

                fragment TradesLimitationsFragment on UserGameTradesLimitations {
                    id
                    buy {
                        resolvedTransactionCount
                        resolvedTransactionPeriodInMinutes
                        activeTransactionCount
                        __typename
                    }
                    sell {
                        resolvedTransactionCount
                        resolvedTransactionPeriodInMinutes
                        activeTransactionCount
                        resaleLocks {
                            itemId
                            expiresAt
                            __typename
                        }
                        __typename
                    }
                    __typename
                }
                """,
        }
    ]

    response = requests.post(url, headers=HEADERS, json=body)

    json_response = response.json()[0]

    code = json_response["errors"][0]["extensions"]["code"]

    if code == "1830":
        print("Failed to cancel order. Trade not found.")
        return False

    return True


def main():
    item_id, space_id = get_item_id_space_id(ITEM_URL)

    if item_id is None or space_id is None:
        print("Failed to retrieve item and space IDs.")
        return

    is_owned, paymentItemId, lowest_sell_price = get_market_information(
        item_id, space_id
    )

    if is_owned is None and paymentItemId is None and lowest_sell_price is None:
        print(
            "[!] Failed to retrieve market information. Authorization is expired. Please replace your tokens in .env file."
        )
        return

    if is_owned:
        print("You already own this item.")
        return

    balance = get_balance()

    if balance < lowest_sell_price:
        print("Insufficient funds.")
        return

    price = int(lowest_sell_price - lowest_sell_price * 0.5)

    if price < 120:
        price = 120

    trade_id = create_buy_order(item_id, space_id, paymentItemId, price)

    while trade_id:
        cancel = cancel_order(space_id, trade_id)

        if not cancel:
            print("Failed to cancel order. Stopping.")
            return

        if price == lowest_sell_price:
            print(f"Lowest sell price reached ({lowest_sell_price} credits). Stopping.")
            return

        trade_id = create_buy_order(item_id, space_id, paymentItemId, price + 1)

        price += 1

    print()
    print(f"Successfully purchased item for {price} credits.")


if __name__ == "__main__":
    main()
