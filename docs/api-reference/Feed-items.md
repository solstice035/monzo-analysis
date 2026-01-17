## Introduction

> **API endpoint**

> Examples in this documentation are written using [httpie](https://github.com/jkbrzt/httpie) for clarity.
> 
> To install `httpie` on macOS run `brew install httpie`

The Monzo API is designed to be a predictable and intuitive interface for interacting with users' accounts. We offer both a REST API and webhooks.

The [Developers category](https://community.monzo.com/c/developers) on our forum is the place to get help with our API, discuss ideas, and show off what you build.

## Authentication

The Monzo API implements [OAuth 2.0](http://oauth.net/2/) to allow users to log in to applications without exposing their credentials. The process involves several steps:

1.  [**Acquire**](https://docs.monzo.com/#acquire-an-access-token) an access token, and optionally a refresh token
2.  [**Use**](https://docs.monzo.com/#authenticating-requests) the access token to make authenticated requests
3.  If you were issued a refresh token: [**refresh**](https://docs.monzo.com/#refreshing-access) the access token when it expires

Before you begin, you will need to create a client in the [developer tools](https://developers.monzo.com/).

### Client confidentiality

Clients are designated either confidential or non-confidential.

-   **Confidential** clients keep their client secret hidden. For example, a server-side app that never exposes its secret to users.
-   **Non-confidential** clients cannot keep their client secret hidden. For example, client-side apps that store their client secret on the user's device, where it could be intercepted.
    
    Non-confidential clients are not issued refresh tokens.
    

## Acquire an access token

Acquiring an access token is a three-step process:

1.  [Redirect the user](https://docs.monzo.com/#redirect-the-user-to-monzo) to Monzo to authorise your app
2.  [Monzo redirects the user](https://docs.monzo.com/#monzo-redirects-back-to-your-app) back to your app with an authorization code
3.  [Exchange](https://docs.monzo.com/#exchange-the-authorization-code) the authorization code for an access token.

_This access token doesn't have any permissions until your user has approved access to their data in the Monzo app._

### Redirect the user to Monzo

```
<span>"https://auth.monzo.com/?
    client_id=</span><span>$client_id</span><span>&amp;
    redirect_uri=</span><span>$redirect_uri</span><span>&amp;
    response_type=code&amp;
    state=</span><span>$state_token</span><span>"</span>
```

Send the user to Monzo in a web browser, where they will log in and grant access to their account.

##### URL arguments

| Parameter | Description |
| --- | --- |
| `client_id`  
Required | Your client ID. |
| `redirect_uri`  
Required | A URI to which users will be redirected after authorising your app. |
| `response_type`  
Required | Must be set to `code`. |
| `state` | An unguessable random string used to protect against [cross-site request forgery attacks](https://www.owasp.org/index.php/Cross-Site_Request_Forgery_(CSRF)). |

### Monzo redirects back to your app

```
<span>"https://your.example.com/oauth/callback?
    code=</span><span>$authorization_code</span><span>&amp;
    state=</span><span>$state_token</span><span>"</span>
```

If the user allows access to their account, Monzo redirects them back to your app.

##### URL arguments

| Parameter | Description |
| --- | --- |
| `code` | A temporary authorization code which will be exchanged for an access token in the next step. |
| `state` | The same string you provided as `state` when sending the user to Monzo. If this value differs from what you sent, you **must** abort the authentication process. |

```
<span>$ </span>http <span>--form</span> POST <span>"https://api.monzo.com/oauth2/token"</span> <span>\</span>
    <span>"grant_type=authorization_code"</span> <span>\</span>
    <span>"client_id=</span><span>$client_id</span><span>"</span> <span>\</span>
    <span>"client_secret=</span><span>$client_secret</span><span>"</span> <span>\</span>
    <span>"redirect_uri=</span><span>$redirect_uri</span><span>"</span> <span>\</span>
    <span>"code=</span><span>$authorization_code</span><span>"</span>
```

```
<span>{</span><span>
    </span><span>"access_token"</span><span>:</span><span> </span><span>"access_token"</span><span>,</span><span>
    </span><span>"client_id"</span><span>:</span><span> </span><span>"client_id"</span><span>,</span><span>
    </span><span>"expires_in"</span><span>:</span><span> </span><span>21600</span><span>,</span><span>
    </span><span>"refresh_token"</span><span>:</span><span> </span><span>"refresh_token"</span><span>,</span><span>
    </span><span>"token_type"</span><span>:</span><span> </span><span>"Bearer"</span><span>,</span><span>
    </span><span>"user_id"</span><span>:</span><span> </span><span>"user_id"</span><span>
</span><span>}</span><span>
</span>
```

When you receive an authorization code, exchange it for an access token. The resulting access token is tied to both your client and an individual Monzo user, and is valid for several hours.

##### Request arguments

| Parameter | Description |
| --- | --- |
| `grant_type`  
Required | This must be set to `authorization_code` |
| `client_id`  
Required | The client ID you received from Monzo. |
| `client_secret`  
Required | The client secret which you received from Monzo. |
| `redirect_uri`  
Required | The URL in your app where users were sent after authorisation. |
| `code`  
Required | The authorization code you received when the user was redirected back to your app. |

## Authenticating requests

```
<span>$ </span>http <span>"https://api.monzo.com/ping/whoami"</span> <span>\</span>
    <span>"Authorization: Bearer </span><span>$access_token</span><span>"</span>
```

```
<span>{</span><span>
    </span><span>"authenticated"</span><span>:</span><span> </span><span>true</span><span>,</span><span>
    </span><span>"client_id"</span><span>:</span><span> </span><span>"client_id"</span><span>,</span><span>
    </span><span>"user_id"</span><span>:</span><span> </span><span>"user_id"</span><span>
</span><span>}</span><span>
</span>
```

**All** requests must be authenticated with an access token supplied in the `Authorization` header using the `Bearer` scheme. Your client may only have _one_ active access token at a time, per user. Acquiring a new access token will invalidate any other token you own for that user.

To get information about an access token, you can call the `/ping/whoami` endpoint.

## Refreshing access

```
<span>$ </span>http <span>--form</span> POST <span>"https://api.monzo.com/oauth2/token"</span> <span>\</span>
    <span>"grant_type=refresh_token"</span> <span>\</span>
    <span>"client_id=</span><span>$client_id</span><span>"</span> <span>\</span>
    <span>"client_secret=</span><span>$client_secret</span><span>"</span> <span>\</span>
    <span>"refresh_token=</span><span>$refresh_token</span><span>"</span>
```

```
<span>{</span><span>
    </span><span>"access_token"</span><span>:</span><span> </span><span>"access_token_2"</span><span>,</span><span>
    </span><span>"client_id"</span><span>:</span><span> </span><span>"client_id"</span><span>,</span><span>
    </span><span>"expires_in"</span><span>:</span><span> </span><span>21600</span><span>,</span><span>
    </span><span>"refresh_token"</span><span>:</span><span> </span><span>"refresh_token_2"</span><span>,</span><span>
    </span><span>"token_type"</span><span>:</span><span> </span><span>"Bearer"</span><span>,</span><span>
    </span><span>"user_id"</span><span>:</span><span> </span><span>"user_id"</span><span>
</span><span>}</span><span>
</span>
```

To limit the window of opportunity for attackers in the event an access token is compromised, access tokens expire after a number of hours. To gain long-lived access to a user's account, it's necessary to "refresh" your access when it expires using a refresh token. Only ["confidential" clients](https://tools.ietf.org/html/rfc6749#section-2.1) are issued refresh tokens – "public" clients must ask the user to re-authenticate.

Refreshing an access token will invalidate the previous token, if it is still valid. Refreshing is a one-time operation.

##### Request arguments

| Parameter | Description |
| --- | --- |
| `grant_type`  
Required | Should be `refresh_token`. |
| `client_id`  
Required | Your client ID. |
| `client_secret`  
Required | Your client secret. |
| `refresh_token`  
Required | The refresh token received along with the original access token. |

## Log Out

```
<span>$ </span>http <span>--form</span> POST <span>"https://api.monzo.com/oauth2/logout"</span> <span>\</span>
    <span>"Authorization: Bearer </span><span>$access_token</span><span>"</span>
```

While access tokens do expire after a number of hours, you may wish to invalidate the token instantly at a specific time such as when a user chooses to log out of your application.

Once invalidated, the user must go through the authentication process again. You will not be able to refresh the access token.

Endpoints which enumerate objects support time-based and cursor-based pagination.

##### Request arguments

| Parameter | Description |
| --- | --- |
| `limit`  
Optional | Limits the number of results per-page.  
Default: 30  
Maximum: 100. |
| `since`  
Optional | An RFC 3339-encoded timestamp.  
eg.`2009-11-10T23:00:00Z`  
…or an object id.  
eg. `tx_00008zhJ3kE6c8kmsGUKgn` |
| `before`  
Optional | An RFC 3339 encoded-timestamp  
`2009-11-10T23:00:00Z` |

## Expanding objects

Some objects contain the id of another object in their response. To save a round-trip, some of these objects can be expanded inline with the `expand[]` argument, which is repeatable. Objects that can be expanded are noted in individual endpoint documentation.

## Accounts

Accounts represent a store of funds, and have a list of transactions.

## List accounts

Returns a list of accounts owned by the currently authorised user.

```
<span>$ </span>http <span>"https://api.monzo.com/accounts"</span> <span>\</span>
    <span>"Authorization: Bearer </span><span>$access_token</span><span>"</span>
```

```
<span>{</span><span>
    </span><span>"accounts"</span><span>:</span><span> </span><span>[</span><span>
        </span><span>{</span><span>
            </span><span>"id"</span><span>:</span><span> </span><span>"acc_00009237aqC8c5umZmrRdh"</span><span>,</span><span>
            </span><span>"description"</span><span>:</span><span> </span><span>"Peter Pan's Account"</span><span>,</span><span>
            </span><span>"created"</span><span>:</span><span> </span><span>"2015-11-13T12:17:42Z"</span><span>
        </span><span>}</span><span>
    </span><span>]</span><span>
</span><span>}</span><span>
</span>
```

To filter by either prepaid or current account, add `account_type` as a url parameter. Valid `account_type`s are `uk_retail`, `uk_retail_joint`.

```
<span>$ </span>http <span>"https://api.monzo.com/accounts"</span> <span>\</span>
    <span>"Authorization: Bearer </span><span>$access_token</span><span>"</span> <span>\</span>
    <span>account_type</span><span>==</span>uk_retail
```

## Balance

Retrieve information about an account's balance.

## Read balance

```
<span>$ </span>http <span>"https://api.monzo.com/balance"</span> <span>\</span>
    <span>"Authorization: Bearer </span><span>$access_token</span><span>"</span> <span>\</span>
    <span>"account_id==</span><span>$account_id</span><span>"</span>
```

```
<span>{</span><span>
    </span><span>"balance"</span><span>:</span><span> </span><span>5000</span><span>,</span><span>
    </span><span>"total_balance"</span><span>:</span><span> </span><span>6000</span><span>,</span><span>
    </span><span>"currency"</span><span>:</span><span> </span><span>"GBP"</span><span>,</span><span>
    </span><span>"spend_today"</span><span>:</span><span> </span><span>0</span><span>
</span><span>}</span><span>
</span>
```

Returns balance information for a specific account.

##### Request arguments

| Parameter | Description |
| --- | --- |
| `account_id`  
Required | The id of the account. |

##### Response arguments

| Parameter | Description |
| --- | --- |
| `balance` | The currently available balance of the account, as a 64bit integer in minor units of the currency, eg. pennies for GBP, or cents for EUR and USD. |
| `total_balance` | The sum of the currently available balance of the account and the combined total of all [the user's pots](https://monzo.com/docs/#list-pots). |
| `currency` | The ISO 4217 currency code. |
| `spend_today` | The amount spent from this account today (considered from approx 4am onwards), as a 64bit integer in minor units of the currency. |

## Pots

A pot is a place to keep some money separate from the main spending account.

## List pots

```
<span>$ </span>http <span>"https://api.monzo.com/pots"</span> <span>\</span>
    <span>"current_account_id==</span><span>$account_id</span><span>"</span> <span>\</span>
    <span>"Authorization: Bearer </span><span>$access_token</span><span>"</span>
```

```
<span>{</span><span>
  </span><span>"pots"</span><span>:</span><span> </span><span>[</span><span>
    </span><span>{</span><span>
      </span><span>"id"</span><span>:</span><span> </span><span>"pot_0000778xxfgh4iu8z83nWb"</span><span>,</span><span>
      </span><span>"name"</span><span>:</span><span> </span><span>"Savings"</span><span>,</span><span>
      </span><span>"style"</span><span>:</span><span> </span><span>"beach_ball"</span><span>,</span><span>
      </span><span>"balance"</span><span>:</span><span> </span><span>133700</span><span>,</span><span>
      </span><span>"currency"</span><span>:</span><span> </span><span>"GBP"</span><span>,</span><span>
      </span><span>"created"</span><span>:</span><span> </span><span>"2017-11-09T12:30:53.695Z"</span><span>,</span><span>
      </span><span>"updated"</span><span>:</span><span> </span><span>"2017-11-09T12:30:53.695Z"</span><span>,</span><span>
      </span><span>"deleted"</span><span>:</span><span> </span><span>false</span><span>
    </span><span>}</span><span>
  </span><span>]</span><span>
</span><span>}</span><span>
</span>
```

Returns a list of pots owned by the currently authorised user that are associated with the specified account.

## Deposit into a pot

```
<span>$ </span>http <span>--form</span> PUT <span>"https://api.monzo.com/pots/</span><span>$pot_id</span><span>/deposit"</span> <span>\</span>
    <span>"Authorization: Bearer </span><span>$access_token</span><span>"</span> <span>\</span>
    <span>"source_account_id=</span><span>$account_id</span><span>"</span> <span>\</span>
    <span>"amount=</span><span>$amount</span><span>"</span> <span>\</span>
    <span>"dedupe_id=</span><span>$dedupe_id</span><span>"</span>
```

Move money from an account owned by the currently authorised user into one of their pots.

```
<span>{</span><span>
    </span><span>"id"</span><span>:</span><span> </span><span>"pot_00009exampleP0tOxWb"</span><span>,</span><span>
    </span><span>"name"</span><span>:</span><span> </span><span>"Wedding Fund"</span><span>,</span><span>
    </span><span>"style"</span><span>:</span><span> </span><span>"beach_ball"</span><span>,</span><span>
    </span><span>"balance"</span><span>:</span><span> </span><span>550100</span><span>,</span><span>
    </span><span>"currency"</span><span>:</span><span> </span><span>"GBP"</span><span>,</span><span>
    </span><span>"created"</span><span>:</span><span> </span><span>"2017-11-09T12:30:53.695Z"</span><span>,</span><span>
    </span><span>"updated"</span><span>:</span><span> </span><span>"2018-02-26T07:12:04.925Z"</span><span>,</span><span>
    </span><span>"deleted"</span><span>:</span><span> </span><span>false</span><span>
</span><span>}</span><span>
</span>
```

##### Request arguments

| Parameter | Description |
| --- | --- |
| `source_account_id`  
Required | The id of the account to withdraw from. |
| `amount`  
Required | The amount to deposit, as a 64bit integer in minor units of the currency, eg. pennies for GBP, or cents for EUR and USD. |
| `dedupe_id`  
Required | A unique string used to de-duplicate deposits. Ensure this remains static between retries to ensure only one deposit is created. |

##### Response arguments

| Parameter | Description |
| --- | --- |
| `id` | The pot id. |
| `name` | The pot name. |
| `style` | The pot background image. |
| `balance` | The new pot balance. |
| `currency` | The pot currency. |
| `created` | When this pot was created. |
| `updated` | When this pot was last updated. |
| `deleted` | Whether this pot is deleted. The API will be updated soon to not return deleted pots. |

## Withdraw from a pot

```
<span>$ </span>http <span>--form</span> PUT <span>"https://api.monzo.com/pots/</span><span>$pot_id</span><span>/withdraw"</span> <span>\</span>
    <span>"Authorization: Bearer </span><span>$access_token</span><span>"</span> <span>\</span>
    <span>"destination_account_id=</span><span>$account_id</span><span>"</span> <span>\</span>
    <span>"amount=</span><span>$amount</span><span>"</span> <span>\</span>
    <span>"dedupe_id=</span><span>$dedupe_id</span><span>"</span>
```

Move money from a pot owned by the currently authorised user into one of their accounts.

```
<span>{</span><span>
    </span><span>"id"</span><span>:</span><span> </span><span>"pot_00009exampleP0tOxWb"</span><span>,</span><span>
    </span><span>"name"</span><span>:</span><span> </span><span>"Flying Lessons"</span><span>,</span><span>
    </span><span>"style"</span><span>:</span><span> </span><span>"blue"</span><span>,</span><span>
    </span><span>"balance"</span><span>:</span><span> </span><span>350000</span><span>,</span><span>
    </span><span>"currency"</span><span>:</span><span> </span><span>"GBP"</span><span>,</span><span>
    </span><span>"created"</span><span>:</span><span> </span><span>"2017-11-09T12:30:53.695Z"</span><span>,</span><span>
    </span><span>"updated"</span><span>:</span><span> </span><span>"2018-02-26T07:12:04.925Z"</span><span>,</span><span>
    </span><span>"deleted"</span><span>:</span><span> </span><span>false</span><span>
</span><span>}</span><span>
</span>
```

##### Request arguments

| Parameter | Description |
| --- | --- |
| `destination_account_id`  
Required | The id of the account to deposit into. |
| `amount`  
Required | The amount to deposit, as a 64bit integer in minor units of the currency, eg. pennies for GBP, or cents for EUR and USD. |
| `dedupe_id`  
Required | A unique string used to de-duplicate deposits. Ensure this remains static between retries to ensure only one withdrawal is created. |

##### Response arguments

| Parameter | Description |
| --- | --- |
| `id` | The pot id. |
| `name` | The pot name. |
| `style` | The pot background image. |
| `balance` | The new pot balance. |
| `currency` | The pot currency. |
| `created` | When this pot was created. |
| `updated` | When this pot was last updated. |
| `deleted` | Whether this pot is deleted. The API will be updated soon to not return deleted pots. |

## Transactions

Transactions are movements of funds into or out of an account. Negative transactions represent debits (ie. _spending_ money) and positive transactions represent credits (ie. _receiving_ money).

Most properties on transactions are self-explanatory. We'll eventually get around to documenting them all, but in the meantime let's discuss the most interesting/confusing ones:

##### Properties

| Property | Description |
| --- | --- |
| `amount` | The amount of the transaction in minor units of `currency`. For example pennies in the case of GBP. A negative amount indicates a debit (most card transactions will have a negative amount) |
| `decline_reason` | **This is only present on declined transactions!** Valid values are `INSUFFICIENT_FUNDS`, `CARD_INACTIVE`, `CARD_BLOCKED`, `INVALID_CVC` or `OTHER`. |
| `is_load` | Top-ups to an account are represented as transactions with a positive amount and `is_load = true`. Other transactions such as refunds, reversals or chargebacks may have a positive amount but `is_load = false` |
| `settled` | The timestamp at which the transaction [settled](http://blog.unibulmerchantservices.com/authorization-clearing-and-settlement-of-mastercard-transactions/). In most cases, this happens 24-48 hours after `created`. If this field is an empty string, the transaction is authorised but not yet "complete." |
| `category` | The category can be set for each transaction by the user. Over time we learn which merchant goes in which category and auto-assign the category of a transaction. If the user hasn't set a category, we'll return the default category of the merchant on this transactions. Top-ups have category `mondo`. Valid values are `general`, `eating_out`, `expenses`, `transport`, `cash`, `bills`, `entertainment`, `shopping`, `holidays`, `groceries`. |
| `merchant` | This contains the `merchant_id` of the merchant that this transaction was made at. If you pass `?expand[]=merchant` in your request URL, it will contain lots of information about the merchant. |

## Retrieve transaction

```
<span>$ </span>http <span>"https://api.monzo.com/transactions/</span><span>$transaction_id</span><span>"</span> <span>\</span>
    <span>"Authorization: Bearer </span><span>$access_token</span><span>"</span> <span>\</span>
    <span># Here we are expanding the merchant \</span>
    <span>"expand[]==merchant"</span>
```

```
<span>{</span><span>
    </span><span>"transaction"</span><span>:</span><span> </span><span>{</span><span>
        </span><span>"amount"</span><span>:</span><span> </span><span>-510</span><span>,</span><span>
        </span><span>"created"</span><span>:</span><span> </span><span>"2015-08-22T12:20:18Z"</span><span>,</span><span>
        </span><span>"currency"</span><span>:</span><span> </span><span>"GBP"</span><span>,</span><span>
        </span><span>"description"</span><span>:</span><span> </span><span>"THE DE BEAUVOIR DELI C LONDON        GBR"</span><span>,</span><span>
        </span><span>"id"</span><span>:</span><span> </span><span>"tx_00008zIcpb1TB4yeIFXMzx"</span><span>,</span><span>
        </span><span>"merchant"</span><span>:</span><span> </span><span>{</span><span>
            </span><span>"address"</span><span>:</span><span> </span><span>{</span><span>
                </span><span>"address"</span><span>:</span><span> </span><span>"98 Southgate Road"</span><span>,</span><span>
                </span><span>"city"</span><span>:</span><span> </span><span>"London"</span><span>,</span><span>
                </span><span>"country"</span><span>:</span><span> </span><span>"GB"</span><span>,</span><span>
                </span><span>"latitude"</span><span>:</span><span> </span><span>51.54151</span><span>,</span><span>
                </span><span>"longitude"</span><span>:</span><span> </span><span>-0.08482400000002599</span><span>,</span><span>
                </span><span>"postcode"</span><span>:</span><span> </span><span>"N1 3JD"</span><span>,</span><span>
                </span><span>"region"</span><span>:</span><span> </span><span>"Greater London"</span><span>
            </span><span>},</span><span>
            </span><span>"created"</span><span>:</span><span> </span><span>"2015-08-22T12:20:18Z"</span><span>,</span><span>
            </span><span>"group_id"</span><span>:</span><span> </span><span>"grp_00008zIcpbBOaAr7TTP3sv"</span><span>,</span><span>
            </span><span>"id"</span><span>:</span><span> </span><span>"merch_00008zIcpbAKe8shBxXUtl"</span><span>,</span><span>
            </span><span>"logo"</span><span>:</span><span> </span><span>"https://pbs.twimg.com/profile_images/527043602623389696/68_SgUWJ.jpeg"</span><span>,</span><span>
            </span><span>"emoji"</span><span>:</span><span> </span><span>"🍞"</span><span>,</span><span>
            </span><span>"name"</span><span>:</span><span> </span><span>"The De Beauvoir Deli Co."</span><span>,</span><span>
            </span><span>"category"</span><span>:</span><span> </span><span>"eating_out"</span><span>
        </span><span>},</span><span>
        </span><span>"metadata"</span><span>:</span><span> </span><span>{},</span><span>
        </span><span>"notes"</span><span>:</span><span> </span><span>"Salmon sandwich 🍞"</span><span>,</span><span>
        </span><span>"is_load"</span><span>:</span><span> </span><span>false</span><span>,</span><span>
        </span><span>"settled"</span><span>:</span><span> </span><span>"2015-08-23T12:20:18Z"</span><span>
    </span><span>}</span><span>
</span><span>}</span><span>
</span>
```

Returns an individual transaction, fetched by its id.

##### Request arguments

| Parameter | Description |
| --- | --- |
| [`expand[]`](https://docs.monzo.com/#expanding-objects)  
Repeated | Can be `merchant`. |

## List transactions

```
<span>$ </span>http <span>"https://api.monzo.com/transactions"</span> <span>\</span>
    <span>"Authorization: Bearer </span><span>$access_token</span><span>"</span> <span>\</span>
    <span>"account_id==</span><span>$account_id</span><span>"</span>
```

```
<span>{</span><span>
    </span><span>"transactions"</span><span>:</span><span> </span><span>[</span><span>
        </span><span>{</span><span>
            </span><span>"amount"</span><span>:</span><span> </span><span>-510</span><span>,</span><span>
            </span><span>"created"</span><span>:</span><span> </span><span>"2015-08-22T12:20:18Z"</span><span>,</span><span>
            </span><span>"currency"</span><span>:</span><span> </span><span>"GBP"</span><span>,</span><span>
            </span><span>"description"</span><span>:</span><span> </span><span>"THE DE BEAUVOIR DELI C LONDON        GBR"</span><span>,</span><span>
            </span><span>"id"</span><span>:</span><span> </span><span>"tx_00008zIcpb1TB4yeIFXMzx"</span><span>,</span><span>
            </span><span>"merchant"</span><span>:</span><span> </span><span>"merch_00008zIcpbAKe8shBxXUtl"</span><span>,</span><span>
            </span><span>"metadata"</span><span>:</span><span> </span><span>{},</span><span>
            </span><span>"notes"</span><span>:</span><span> </span><span>"Salmon sandwich 🍞"</span><span>,</span><span>
            </span><span>"is_load"</span><span>:</span><span> </span><span>false</span><span>,</span><span>
            </span><span>"settled"</span><span>:</span><span> </span><span>"2015-08-23T12:20:18Z"</span><span>,</span><span>
            </span><span>"category"</span><span>:</span><span> </span><span>"eating_out"</span><span>
        </span><span>},</span><span>
        </span><span>{</span><span>
            </span><span>"amount"</span><span>:</span><span> </span><span>-679</span><span>,</span><span>
            </span><span>"created"</span><span>:</span><span> </span><span>"2015-08-23T16:15:03Z"</span><span>,</span><span>
            </span><span>"currency"</span><span>:</span><span> </span><span>"GBP"</span><span>,</span><span>
            </span><span>"description"</span><span>:</span><span> </span><span>"VUE BSL LTD            ISLINGTON     GBR"</span><span>,</span><span>
            </span><span>"id"</span><span>:</span><span> </span><span>"tx_00008zL2INM3xZ41THuRF3"</span><span>,</span><span>
            </span><span>"merchant"</span><span>:</span><span> </span><span>"merch_00008z6uFVhVBcaZzSQwCX"</span><span>,</span><span>
            </span><span>"metadata"</span><span>:</span><span> </span><span>{},</span><span>
            </span><span>"notes"</span><span>:</span><span> </span><span>""</span><span>,</span><span>
            </span><span>"is_load"</span><span>:</span><span> </span><span>false</span><span>,</span><span>
            </span><span>"settled"</span><span>:</span><span> </span><span>"2015-08-24T16:15:03Z"</span><span>,</span><span>
            </span><span>"category"</span><span>:</span><span> </span><span>"eating_out"</span><span>
        </span><span>},</span><span>
    </span><span>]</span><span>
</span><span>}</span><span>
</span>
```

Returns a list of transactions on the user's account.

##### Request arguments

| Parameter | Description |
| --- | --- |
| `account_id`  
Required | The account to retrieve transactions from. |
| `since`  
Optional | Start time as RFC3339 encoded timestamp (`2009-11-10T23:00:00Z`) |
| `before`  
Optional | End time time as RFC3339 encoded timestamp (`2009-11-10T23:00:00Z`) |
| Pagination  
Optional | This endpoint can be [paginated](https://docs.monzo.com/#pagination). |

## Annotate transaction

```
<span>$ </span>http <span>--form</span> PATCH <span>"https://api.monzo.com/transactions/</span><span>$transaction_id</span><span>"</span> <span>\</span>
    <span>"Authorization: Bearer </span><span>$access_token</span><span>"</span> <span>\</span>
    <span>"metadata[</span><span>$key1</span><span>]=</span><span>$value1</span><span>"</span> <span>\</span>
    <span>#&nbsp;Set a key's value as empty to delete it</span>
    <span>"metadata[</span><span>$key2</span><span>]="</span>
```

```
<span>{</span><span>
    </span><span>"transaction"</span><span>:</span><span> </span><span>{</span><span>
        </span><span>"amount"</span><span>:</span><span> </span><span>-679</span><span>,</span><span>
        </span><span>"created"</span><span>:</span><span> </span><span>"2015-08-23T16:15:03Z"</span><span>,</span><span>
        </span><span>"currency"</span><span>:</span><span> </span><span>"GBP"</span><span>,</span><span>
        </span><span>"description"</span><span>:</span><span> </span><span>"VUE BSL LTD            ISLINGTON     GBR"</span><span>,</span><span>
        </span><span>"id"</span><span>:</span><span> </span><span>"tx_00008zL2INM3xZ41THuRF3"</span><span>,</span><span>
        </span><span>"merchant"</span><span>:</span><span> </span><span>"merch_00008z6uFVhVBcaZzSQwCX"</span><span>,</span><span>
        </span><span>"metadata"</span><span>:</span><span> </span><span>{</span><span>
            </span><span>"foo"</span><span>:</span><span> </span><span>"bar"</span><span>
        </span><span>},</span><span>
        </span><span>"notes"</span><span>:</span><span> </span><span>""</span><span>,</span><span>
        </span><span>"is_load"</span><span>:</span><span> </span><span>false</span><span>,</span><span>
        </span><span>"settled"</span><span>:</span><span> </span><span>"2015-08-24T16:15:03Z"</span><span>,</span><span>
        </span><span>"category"</span><span>:</span><span> </span><span>"eating_out"</span><span>
    </span><span>}</span><span>
</span><span>}</span><span>
</span>
```

You may store your own key-value annotations against a transaction in its `metadata`.

##### Request arguments

| Parameter | Description |
| --- | --- |
| `metadata[$name]`  
Repeated | Include each key you would like to modify. To delete a key, set its value to an empty string. |

## Feed items

The Monzo app is organised around the feed – a reverse-chronological stream of events. Transactions are one such feed item, and your application can create its own feed items to surface relevant information to the user.

It's important to keep a few principals in mind when creating feed items:

1.  Feed items are _discrete_ events that happen at a _point in time_.
2.  Because of their prominence within the Monzo app, feed items should contain information of _high value_.
3.  While the appearance of feed items can be customised, care should be taken to match the style of the Monzo app so that your feed items feel part of the experience.

## Create feed item

```
<span>$ </span>http <span>--form</span> POST <span>"https://api.monzo.com/feed"</span> <span>\</span>
    <span>"Authorization: Bearer </span><span>$access_token</span><span>"</span> <span>\</span>
    <span>"account_id=</span><span>$account_id</span><span>"</span> <span>\</span>
    <span>"type=basic"</span> <span>\</span>
    <span>"url=https://www.example.com/a_page_to_open_on_tap.html"</span> <span>\</span>
    <span>"params[title]=My custom item"</span> <span>\</span>
    <span>"params[image_url]=www.example.com/image.png"</span> <span>\</span>
    <span>"params[background_color]=#FCF1EE"</span> <span>\</span>
    <span>"params[body_color]=#FCF1EE"</span> <span>\</span>
    <span>"params[title_color]=#333333"</span> <span>\</span>
    <span>"params[body]=Some body text to display"</span>
```

Creates a new feed item on the user's feed. These can be dismissed.

##### Request arguments (for all feed item types)

| Parameter | Description |
| --- | --- |
| `account_id`  
Required | The account to create a feed item for. |
| `type`  
Required | Type of feed item. Currently only `basic` is supported. |
| `params`  
Required | A _map_ of parameters which vary based on `type` |
| `url`  
Optional | A URL to open when the feed item is tapped. If no URL is provided, the app will display a fallback view based on the title & body. |

### Per-type arguments

Each type of feed item supports customisation with a specific list of `params`. Currently we only support creation of the `basic` feed item which requires the parameters below. These should be sent as form parameters as in the example to the right.

##### Basic

The basic type displays an `image`, with `title` text and optional `body` text.  
_Note the image supports animated gifs!_

![](https://docs.monzo.com/images/nyanfeed-93ee2ecb.gif)

##### Request arguments

| Parameter | Description |
| --- | --- |
| `title`  
Required | The title to display. |
| `image_url`  
Required | URL of the image to display. This will be displayed as an icon in the feed, and on the expanded page if no `url` has been provided. |
| `body`  
Optional | The body text of the feed item. |
| `background_color`  
Optional | Hex value for the background colour of the feed item in the format `#RRGGBB`. Defaults to to standard app colours (ie. white background). |
| `title_color`  
Optional | Hex value for the colour of the title text in the format `#RRGGBB`. Defaults to standard app colours. |
| `body_color`  
Optional | Hex value for the colour of the body text in the format `#RRGGBB`. Defaults to standard app colours. |

## Attachments

Images (eg. receipts) can be attached to transactions by uploading these via the `attachment` API. Once an attachment is _registered_ against a transaction, the image will be shown in the transaction detail screen within the Monzo app.

There are two options for attaching images to transactions - either Monzo can host the image, or remote images can be displayed.

If Monzo is hosting the attachment the upload process consists of three steps:

1.  Obtain a temporary authorised URL to [upload](https://docs.monzo.com/#upload-attachment) the attachment to.
2.  Upload the file to this URL.
3.  [Register](https://docs.monzo.com/#register-attachment) the attachment against a `transaction`.

If you are hosting the attachment, you can simply register the attachment with the transaction:

1.  [Register](https://docs.monzo.com/#register-attachment) the attachment against a `transaction`.

## Upload attachment

The first step when uploading an attachment is to obtain a temporary URL to which the file can be uploaded. The response will include a `file_url` which will be the URL of the resulting file, and an `upload_url` to which the file should be uploaded to.

```
<span>$ </span>http <span>--form</span> POST <span>"https://api.monzo.com/attachment/upload"</span> <span>\</span>
    <span>"Authorization: Bearer </span><span>$access_token</span><span>"</span> <span>\</span>
    <span>"file_name=foo.png"</span> <span>\</span>
    <span>"file_type=image/png"</span> <span>\</span>
    <span>"content_length=12345"</span>
```

```
<span>{</span><span>
    </span><span>"file_url"</span><span>:</span><span>"https://s3-eu-west-1.amazonaws.com/mondo-image-uploads/user_00009237hliZellUicKuG1/LcCu4ogv1xW28OCcvOTL-foo.png"</span><span>,</span><span>
    </span><span>"upload_url"</span><span>:</span><span>"https://mondo-image-uploads.s3.amazonaws.com/user_00009237hliZellUicKuG1/LcCu4ogv1xW28OCcvOTL-foo.png?AWSAccessKeyId={EXAMPLE_AWS_ACCESS_KEY_ID}</span><span>\u</span><span>0026Expires=1447353431</span><span>\u</span><span>0026Signature=k2QeDCCQQHaZeynzYKckejqXRGU%!D(MISSING)"</span><span>
</span><span>}</span><span>
</span>
```

##### Request arguments

| Parameter | Description |
| --- | --- |
| `file_name`  
Required | The name of the file to be uploaded |
| `file_type`  
Required | The content type of the file |
| `content_length`  
Required | The HTTP Content-Length of the upload request body, in bytes. |

##### Response arguments

| Parameter | Description |
| --- | --- |
| `file_url` | The URL of the file once it has been uploaded |
| `upload_url` | The URL to `POST` the file to when uploading |

## Register attachment

Once you have obtained a URL for an attachment, either by uploading to the `upload_url` obtained from the `upload` endpoint above or by hosting a remote image, this URL can then be registered against a transaction. Once an attachment is registered against a transaction this will be displayed on the detail page of a transaction within the Monzo app.

```
<span>$ </span>http <span>--form</span> POST <span>"https://api.monzo.com/attachment/register"</span> <span>\</span>
    <span>"Authorization: Bearer </span><span>$access_token</span><span>"</span> <span>\</span>
    <span>"external_id=tx_00008zIcpb1TB4yeIFXMzx"</span> <span>\</span>
    <span>"file_type=image/png"</span> <span>\</span>
    <span>"file_url=https://s3-eu-west-1.amazonaws.com/mondo-image-uploads/user_00009237hliZellUicKuG1/LcCu4ogv1xW28OCcvOTL-foo.png"</span>
```

```
<span>{</span><span>
    </span><span>"attachment"</span><span>:</span><span> </span><span>{</span><span>
        </span><span>"id"</span><span>:</span><span> </span><span>"attach_00009238aOAIvVqfb9LrZh"</span><span>,</span><span>
        </span><span>"user_id"</span><span>:</span><span> </span><span>"user_00009238aMBIIrS5Rdncq9"</span><span>,</span><span>
        </span><span>"external_id"</span><span>:</span><span> </span><span>"tx_00008zIcpb1TB4yeIFXMzx"</span><span>,</span><span>
        </span><span>"file_url"</span><span>:</span><span> </span><span>"https://s3-eu-west-1.amazonaws.com/mondo-image-uploads/user_00009237hliZellUicKuG1/LcCu4ogv1xW28OCcvOTL-foo.png"</span><span>,</span><span>
        </span><span>"file_type"</span><span>:</span><span> </span><span>"image/png"</span><span>,</span><span>
        </span><span>"created"</span><span>:</span><span> </span><span>"2015-11-12T18:37:02Z"</span><span>
    </span><span>}</span><span>
</span><span>}</span><span>
</span>
```

##### Request arguments

| Parameter | Description |
| --- | --- |
| `external_id`  
Required | The id of the `transaction` to associate the `attachment` with. |
| `file_url`  
Required | The URL of the uploaded attachment. |
| `file_type`  
Required | The content type of the attachment. |

##### Response arguments

| Parameter | Description |
| --- | --- |
| `id` | The ID of the attachment. This can be used to deregister at a later date. |
| `user_id` | The id of the `user` who owns this `attachment`. |
| `external_id` | The id of the `transaction` to which the `attachment` is attached. |
| `file_url` | The URL at which the `attachment` is available. |
| `file_type` | The file type of the `attachment`. |
| `created` | The timestamp _in UTC_ when the attachment was created. |

## Deregister attachment

To remove an `attachment`, simply deregister this using its `id`

```
<span>$ </span>http <span>--form</span> POST <span>"https://api.monzo.com/attachment/deregister"</span> <span>\</span>
    <span>"Authorization: Bearer </span><span>$access_token</span><span>"</span> <span>\</span>
    <span>"id=attach_00009238aOAIvVqfb9LrZh"</span>
```

##### Request arguments

| Parameter | Description |
| --- | --- |
| `id`  
Required | The id of the `attachment` to deregister. |

## Receipts

Receipts are line-item purchase data added to a transaction. They contain all the information about the purchase, including the products you bought, any taxes that were added on, and how you paid. They can also contain extra details about the merchant you spent money at, such as how to contact them, but this may not appear in the app yet.

This is the API currently used by [Flux](https://monzo.com/blog/2019/01/31/flux-monzo-launch/) to show receipts at selected retailers in your Monzo app.

##### Properties

```
<span>{</span><span>
    </span><span>"transaction_id"</span><span>:</span><span> </span><span>"tx_00..."</span><span>,</span><span>
    </span><span>"external_id"</span><span>:</span><span> </span><span>"Order-12345678"</span><span>,</span><span>
    </span><span>"total"</span><span>:</span><span> </span><span>1299</span><span>,</span><span>
    </span><span>"currency"</span><span>:</span><span> </span><span>"GBP"</span><span>,</span><span>
    </span><span>"items"</span><span>:</span><span> </span><span>[],</span><span>
    </span><span>"taxes"</span><span>:</span><span> </span><span>[],</span><span>
    </span><span>"payments"</span><span>:</span><span> </span><span>[],</span><span>
    </span><span>"merchant"</span><span>:</span><span> </span><span>{}</span><span>
</span><span>}</span><span>
</span>
```

| Property | Description |
| --- | --- |
| `id` | A unique identifier generated by Monzo when you submit the receipt. |
| `external_id`  
Required | A unique identifier generated by you, which is used as an idempotency key. You might use an order number for example. |
| `transaction_id`  
Required | The ID of the Transaction to associate the Receipt with. |
| `total`  
Required | The amount of the transaction in minor units of `currency`. For example pennies in the case of GBP. The amount should be positive. |
| `currency`  
Required | Usually `GBP`, for Pounds Sterling. |
| `items`  
Required | A list of [Items](https://docs.monzo.com/#receipt-items) detailing the products included in the total. |
| `taxes` | A list of [Taxes](https://docs.monzo.com/#receipt-taxes) (e.g. VAT) added onto the total. |
| `payments` | A list of [Payments](https://docs.monzo.com/#receipt-payments), indicating how the customer paid the total. |
| `merchant` | The [Merchant](https://docs.monzo.com/#receipt-merchant) you shopped at.  
(This is a different type of object than the Merchant on a Transaction.) |

## Receipt Items

```
<span>[</span><span>
    </span><span>{</span><span>
        </span><span>"description"</span><span>:</span><span> </span><span>"Burger"</span><span>,</span><span>
        </span><span>"quantity"</span><span>:</span><span> </span><span>1</span><span>,</span><span>
        </span><span>"unit"</span><span>:</span><span> </span><span>""</span><span>,</span><span>
        </span><span>"amount"</span><span>:</span><span> </span><span>539</span><span>,</span><span>
        </span><span>"currency"</span><span>:</span><span> </span><span>"GBP"</span><span>,</span><span>
        </span><span>"tax"</span><span>:</span><span> </span><span>77</span><span>,</span><span>
        </span><span>"sub_items"</span><span>:</span><span> </span><span>[</span><span>
            </span><span>{</span><span>
                </span><span>"description"</span><span>:</span><span> </span><span>"Extra cheese"</span><span>,</span><span>
                </span><span>"quantity"</span><span>:</span><span> </span><span>1</span><span>,</span><span>
                </span><span>"unit"</span><span>:</span><span> </span><span>""</span><span>,</span><span>
                </span><span>"amount"</span><span>:</span><span> </span><span>100</span><span>,</span><span>
                </span><span>"currency"</span><span>:</span><span> </span><span>"GBP"</span><span>,</span><span>
                </span><span>"tax"</span><span>:</span><span> </span><span>0</span><span>
            </span><span>},</span><span>
            </span><span>{</span><span>
                </span><span>"description"</span><span>:</span><span> </span><span>"Free extra topping promotion"</span><span>,</span><span>
                </span><span>"quantity"</span><span>:</span><span> </span><span>1</span><span>,</span><span>
                </span><span>"unit"</span><span>:</span><span> </span><span>""</span><span>,</span><span>
                </span><span>"amount"</span><span>:</span><span> </span><span>-100</span><span>,</span><span>
                </span><span>"currency"</span><span>:</span><span> </span><span>"GBP"</span><span>,</span><span>
                </span><span>"tax"</span><span>:</span><span> </span><span>0</span><span>
            </span><span>}</span><span>
        </span><span>]</span><span>
    </span><span>},</span><span>
    </span><span>{</span><span>
        </span><span>"description"</span><span>:</span><span> </span><span>"Fries"</span><span>,</span><span>
        </span><span>"quantity"</span><span>:</span><span> </span><span>1</span><span>,</span><span>
        </span><span>"unit"</span><span>:</span><span> </span><span>""</span><span>,</span><span>
        </span><span>"amount"</span><span>:</span><span> </span><span>139</span><span>,</span><span>
        </span><span>"currency"</span><span>:</span><span> </span><span>"GBP"</span><span>,</span><span>
        </span><span>"tax"</span><span>:</span><span> </span><span>19</span><span>
    </span><span>},</span><span>
    </span><span>{</span><span>
        </span><span>"description"</span><span>:</span><span> </span><span>"Milkshake"</span><span>,</span><span>
        </span><span>"quantity"</span><span>:</span><span> </span><span>2</span><span>,</span><span>
        </span><span>"unit"</span><span>:</span><span> </span><span>""</span><span>,</span><span>
        </span><span>"amount"</span><span>:</span><span> </span><span>198</span><span>,</span><span>
        </span><span>"currency"</span><span>:</span><span> </span><span>"GBP"</span><span>,</span><span>
        </span><span>"tax"</span><span>:</span><span> </span><span>38</span><span>
    </span><span>},</span><span>
    </span><span>{</span><span>
        </span><span>"description"</span><span>:</span><span> </span><span>"Bananas, £1 per kg"</span><span>,</span><span>
        </span><span>"quantity"</span><span>:</span><span> </span><span>0.3</span><span>,</span><span>
        </span><span>"unit"</span><span>:</span><span> </span><span>"kg"</span><span>,</span><span>
        </span><span>"amount"</span><span>:</span><span> </span><span>30</span><span>,</span><span>
        </span><span>"currency"</span><span>:</span><span> </span><span>"GBP"</span><span>,</span><span>
        </span><span>"tax"</span><span>:</span><span> </span><span>0</span><span>
    </span><span>}</span><span>
</span><span>]</span><span>
</span>
```

Items detail each product that was included in the transaction. They let you see more detailed data in your Monzo feed than just how much you spent! 🎉

Items can be made up of sub-items, for example an extra topping on a burger. Sub-items have the same format as items (but they cannot in turn have their own sub-items!). The amounts of the sub-items should add up to amount on the item.

All of the items together, plus the taxes, should add up to the Receipt total.

##### Properties

| Property | Description |
| --- | --- |
| `description`  
Required | The product you bought! |
| `amount`  
Required | The amount paid for the item, in pennies.  
If there are sub-items, this should be the total of their amounts. |
| `currency`  
Required | e.g. GBP |
| `quantity` | A number indicating how many of the product were bought, e.g. `2`.  
A floating-point number, so it can represent weights like `1.23` for example |
| `unit` | The unit the quantity is measured in, e.g. `kg` |
| `tax` | The tax, in pennies. |
| `sub_items` | A list of sub-items, as described above |

## Receipt Taxes

```
<span>[</span><span>
    </span><span>{</span><span>
        </span><span>"description"</span><span>:</span><span> </span><span>"VAT"</span><span>,</span><span>
        </span><span>"amount"</span><span>:</span><span> </span><span>10</span><span>,</span><span>
        </span><span>"currency"</span><span>:</span><span> </span><span>"GBP"</span><span>,</span><span>
        </span><span>"tax_number"</span><span>:</span><span> </span><span>"945719291"</span><span>
    </span><span>}</span><span>
</span><span>]</span><span>
</span>
```

Taxes will be shown near the bottom of the receipt, just above the total.

##### Properties

| Property | Description |
| --- | --- |
| `description`  
Required | e.g. “VAT” |
| `amount`  
Required | Total amount of the tax, in pennies |
| `currency`  
Required | e.g. GBP |
| `tax_number` | e.g. “945719291” |

## Receipt Payments

```
<span>[</span><span>
    </span><span>{</span><span>
      </span><span>"type"</span><span>:</span><span> </span><span>"card"</span><span>,</span><span>
      </span><span>"bin"</span><span>:</span><span> </span><span>"543210"</span><span>,</span><span>
      </span><span>"last_four"</span><span>:</span><span> </span><span>"0987"</span><span>,</span><span>
      </span><span>"auth_code"</span><span>:</span><span> </span><span>"123456"</span><span>,</span><span>
      </span><span>"aid"</span><span>:</span><span> </span><span>""</span><span>,</span><span>
      </span><span>"mid"</span><span>:</span><span> </span><span>""</span><span>,</span><span>
      </span><span>"tid"</span><span>:</span><span> </span><span>""</span><span>,</span><span>
      </span><span>"amount"</span><span>:</span><span> </span><span>1000</span><span>,</span><span>
      </span><span>"currency"</span><span>:</span><span> </span><span>"GBP"</span><span>
    </span><span>},</span><span>
    </span><span>{</span><span>
      </span><span>"type"</span><span>:</span><span> </span><span>"cash"</span><span>,</span><span>
      </span><span>"amount"</span><span>:</span><span> </span><span>1000</span><span>,</span><span>
      </span><span>"currency"</span><span>:</span><span> </span><span>"GBP"</span><span>
    </span><span>},</span><span>
    </span><span>{</span><span>
      </span><span>"type"</span><span>:</span><span> </span><span>"gift_card"</span><span>,</span><span>
      </span><span>"gift_card_type"</span><span>:</span><span> </span><span>"One4all"</span><span>,</span><span>
      </span><span>"amount"</span><span>:</span><span> </span><span>1000</span><span>,</span><span>
      </span><span>"currency"</span><span>:</span><span> </span><span>"GBP"</span><span>
    </span><span>}</span><span>
</span><span>]</span><span>
</span>
```

Payments tell us how you paid for your purchase. While it will always include a card payment, sometimes a cash payment or a gift card is included as well. All of the payments together should add up to the Receipt total.

The payment details might not appear in the app just yet.

| Property | Description |
| --- | --- |
| `type`  
Required | `card`, `cash`, or `gift_card` |
| `amount`  
Required | Amount paid in pennies |
| `currency`  
Required | e.g. GBP |
| `last_four` | The last four digits of the card number, for `card` Payments. |
| `gift_card_type` | A description of the gift card, for `gift_card` Payments |

## Receipt Merchant

The merchant gives us more information about where the purchase was made, to help us decide what to show at the top of the receipt.

| Property | Description |
| --- | --- |
| `name` | The merchant name |
| `online` | `true` for Ecommerce merchants like Amazon  
`false` for offline merchants like Pret or Starbucks |
| `phone` | The phone number of the store |
| `email` | The merchant’s email address |
| `store_name` | The name of that particular store, e.g. `Old Street` |
| `store_address` | The store’s address |
| `store_postcode` | The store’s postcode |

## Create receipt

```
<span>$ </span>http PUT <span>"https://api.monzo.com/transaction-receipts"</span> <span>\</span>
    <span>"Authorization: Bearer </span><span>$access_token</span><span>"</span> <span>\</span>
    <span># ... JSON Receipt data ...</span>
```

```
<span>{</span><span>
  </span><span>"transaction_id"</span><span>:</span><span> </span><span>"tx_00..."</span><span>,</span><span> 
  </span><span>"external_id"</span><span>:</span><span> </span><span>"test-receipt-1"</span><span>,</span><span>
  </span><span>"total"</span><span>:</span><span> </span><span>1299</span><span>,</span><span>
  </span><span>"currency"</span><span>:</span><span> </span><span>"GBP"</span><span>,</span><span>
  </span><span>"items"</span><span>:</span><span> </span><span>[</span><span>
    </span><span>{</span><span>
      </span><span>"description"</span><span>:</span><span> </span><span>"Bananas, 70p per kg"</span><span>,</span><span>
      </span><span>"quantity"</span><span>:</span><span> </span><span>18.56</span><span>,</span><span>
      </span><span>"unit"</span><span>:</span><span> </span><span>"kg"</span><span>,</span><span>
      </span><span>"amount"</span><span>:</span><span> </span><span>70</span><span>,</span><span>
      </span><span>"currency"</span><span>:</span><span> </span><span>"GBP"</span><span>
    </span><span>}</span><span>
  </span><span>]</span><span>
</span><span>}</span><span>
</span>
```

```
<span>{</span><span>
    </span><span>"receipt_id"</span><span>:</span><span> </span><span>"receipt_00009NrKwNtI3gKqte"</span><span>,</span><span>
    </span><span>...</span><span>
</span><span>}</span><span>
</span>
```

To attach a receipt to a transaction, make a `PUT` request to the `/transaction-receipts` API. Your request should include a body containing the receipt encoded as JSON.

If you’re successful, you’ll get back a `200 OK` HTTP response with an empty body. After that, the receipt will show up in your Monzo app!

The `external_id` is used as an idempotency key, so if you call this endpoint again with the same external ID, it will **update** the existing receipt.

## Retrieve receipt

You can read back a receipt that you've created based on its external ID.

Note that you'll only be able to read your own receipts in this way.

```
$ http GET "https://api.monzo.com/transaction-receipts" \
    "Authorization: Bearer $access_token" \
    "external_id==test-receipt-1"
```

```
<span>{</span><span>
  </span><span>"receipt"</span><span>:</span><span> </span><span>{</span><span>
    </span><span>"id"</span><span>:</span><span> </span><span>"receipt_00009eNJqNeJvKeoQA"</span><span>,</span><span>
    </span><span>"external_id"</span><span>:</span><span> </span><span>"test-receipt-1"</span><span>,</span><span>
    </span><span>...</span><span>
  </span><span>}</span><span>
</span><span>}</span><span>
</span>
```

##### Request arguments

| Parameter | Description |
| --- | --- |
| `external_id`  
Required | The external ID of the receipt. |

## Delete receipt

You can delete a receipt based on its external ID.

Note that you can also **update** an existing receipt, by [creating it again](https://docs.monzo.com/#create-a-receipt) with different values.

```
$ http DELETE "https://api.monzo.com/transaction-receipts" \
    "Authorization: Bearer $access_token" \
    "external_id==test-receipt-1"
```

##### Request arguments

| Parameter | Description |
| --- | --- |
| `external_id`  
Required | The external ID of the receipt. |

## Webhooks

Webhooks allow your application to receive real-time, push notification of events in an account.

## Registering a webhook

```
<span>$ </span>http <span>--form</span> POST <span>"https://api.monzo.com/webhooks"</span> <span>\</span>
    <span>"Authorization: Bearer </span><span>$access_token</span><span>"</span> <span>\</span>
    <span>"account_id=</span><span>$account_id</span><span>"</span> <span>\</span>
    <span>"url=</span><span>$url</span><span>"</span>
```

```
<span>{</span><span>
    </span><span>"webhook"</span><span>:</span><span> </span><span>{</span><span>
        </span><span>"account_id"</span><span>:</span><span> </span><span>"account_id"</span><span>,</span><span>
        </span><span>"id"</span><span>:</span><span> </span><span>"webhook_id"</span><span>,</span><span>
        </span><span>"url"</span><span>:</span><span> </span><span>"http://example.com"</span><span>
    </span><span>}</span><span>
</span><span>}</span><span>
</span>
```

Each time a matching event occurs, we will make a POST call to the URL you provide. If the call fails, we will retry up to a maximum of 5 attempts, with exponential backoff.

##### Request arguments

| Parameter | Description |
| --- | --- |
| `account_id`  
Required | The account to receive notifications for. |
| `url`  
Required | The URL we will send notifications to. |

## List webhooks

```
<span>$ </span>http <span>"https://api.monzo.com/webhooks"</span> <span>\</span>
    <span>"Authorization: Bearer </span><span>$access_token</span><span>"</span> <span>\</span>
    <span>"account_id=</span><span>$account_id</span><span>"</span>
```

```
<span>{</span><span>
    </span><span>"webhooks"</span><span>:</span><span> </span><span>[</span><span>
        </span><span>{</span><span>
            </span><span>"account_id"</span><span>:</span><span> </span><span>"acc_000091yf79yMwNaZHhHGzp"</span><span>,</span><span>
            </span><span>"id"</span><span>:</span><span> </span><span>"webhook_000091yhhOmrXQaVZ1Irsv"</span><span>,</span><span>
            </span><span>"url"</span><span>:</span><span> </span><span>"http://example.com/callback"</span><span>
        </span><span>},</span><span>
        </span><span>{</span><span>
            </span><span>"account_id"</span><span>:</span><span> </span><span>"acc_000091yf79yMwNaZHhHGzp"</span><span>,</span><span>
            </span><span>"id"</span><span>:</span><span> </span><span>"webhook_000091yhhzvJSxLYGAceC9"</span><span>,</span><span>
            </span><span>"url"</span><span>:</span><span> </span><span>"http://example2.com/anothercallback"</span><span>
        </span><span>}</span><span>
    </span><span>]</span><span>
</span><span>}</span><span>
</span>
```

List the webhooks your application has registered on an account.

##### Request arguments

| Parameter | Description |
| --- | --- |
| `account_id`  
Required | The account to list registered webhooks for. |

## Deleting a webhook

```
<span>$ </span>http DELETE <span>"https://api.monzo.com/webhooks/</span><span>$webhook_id</span><span>"</span> <span>\</span>
    <span>"Authorization: Bearer </span><span>$access_token</span><span>"</span>
```

When you delete a webhook, we will no longer send notifications to it.

## Transaction created

```
<span>{</span><span>
    </span><span>"type"</span><span>:</span><span> </span><span>"transaction.created"</span><span>,</span><span>
    </span><span>"data"</span><span>:</span><span> </span><span>{</span><span>
        </span><span>"account_id"</span><span>:</span><span> </span><span>"acc_00008gju41AHyfLUzBUk8A"</span><span>,</span><span>
        </span><span>"amount"</span><span>:</span><span> </span><span>-350</span><span>,</span><span>
        </span><span>"created"</span><span>:</span><span> </span><span>"2015-09-04T14:28:40Z"</span><span>,</span><span>
        </span><span>"currency"</span><span>:</span><span> </span><span>"GBP"</span><span>,</span><span>
        </span><span>"description"</span><span>:</span><span> </span><span>"Ozone Coffee Roasters"</span><span>,</span><span>
        </span><span>"id"</span><span>:</span><span> </span><span>"tx_00008zjky19HyFLAzlUk7t"</span><span>,</span><span>
        </span><span>"category"</span><span>:</span><span> </span><span>"eating_out"</span><span>,</span><span>
        </span><span>"is_load"</span><span>:</span><span> </span><span>false</span><span>,</span><span>
        </span><span>"settled"</span><span>:</span><span> </span><span>"2015-09-05T14:28:40Z"</span><span>,</span><span>
        </span><span>"merchant"</span><span>:</span><span> </span><span>{</span><span>
            </span><span>"address"</span><span>:</span><span> </span><span>{</span><span>
                </span><span>"address"</span><span>:</span><span> </span><span>"98 Southgate Road"</span><span>,</span><span>
                </span><span>"city"</span><span>:</span><span> </span><span>"London"</span><span>,</span><span>
                </span><span>"country"</span><span>:</span><span> </span><span>"GB"</span><span>,</span><span>
                </span><span>"latitude"</span><span>:</span><span> </span><span>51.54151</span><span>,</span><span>
                </span><span>"longitude"</span><span>:</span><span> </span><span>-0.08482400000002599</span><span>,</span><span>
                </span><span>"postcode"</span><span>:</span><span> </span><span>"N1 3JD"</span><span>,</span><span>
                </span><span>"region"</span><span>:</span><span> </span><span>"Greater London"</span><span>
            </span><span>},</span><span>
            </span><span>"created"</span><span>:</span><span> </span><span>"2015-08-22T12:20:18Z"</span><span>,</span><span>
            </span><span>"group_id"</span><span>:</span><span> </span><span>"grp_00008zIcpbBOaAr7TTP3sv"</span><span>,</span><span>
            </span><span>"id"</span><span>:</span><span> </span><span>"merch_00008zIcpbAKe8shBxXUtl"</span><span>,</span><span>
            </span><span>"logo"</span><span>:</span><span> </span><span>"https://pbs.twimg.com/profile_images/527043602623389696/68_SgUWJ.jpeg"</span><span>,</span><span>
            </span><span>"emoji"</span><span>:</span><span> </span><span>"🍞"</span><span>,</span><span>
            </span><span>"name"</span><span>:</span><span> </span><span>"The De Beauvoir Deli Co."</span><span>,</span><span>
            </span><span>"category"</span><span>:</span><span> </span><span>"eating_out"</span><span>
        </span><span>}</span><span>
    </span><span>}</span><span>
</span><span>}</span><span>
</span>
```

Each time a new transaction is created in a user's account, we will immediately send information about it in a `transaction.created` event.

## Errors

The Monzo API uses conventional HTTP response codes to indicate errors, and includes more detailed information on the exact nature of an error in the HTTP response.

##### HTTP response codes

| Response code | Meaning |
| --- | --- |
| `200`  
OK | All is well. |
| `400`  
Bad Request | Your request has missing arguments or is malformed. |
| `401`  
Unauthorized | Your request is not authenticated. |
| `403`  
Forbidden | Your request is authenticated but has insufficient permissions. |
| `405`  
Method Not Allowed | You are using an incorrect HTTP verb. Double check whether it should be `POST`/`GET`/`DELETE`/etc. |
| `404`  
Page Not Found | The endpoint requested does not exist. |
| `406`  
Not Acceptable | Your application does not accept the content format returned according to the `Accept` headers sent in the request. |
| `429`  
Too Many Requests | Your application is exceeding its rate limit. Back off, buddy. :p |
| `500`  
Internal Server Error | Something is wrong on our end. Whoopsie. |
| `504`  
Gateway Timeout | Something has timed out on our end. Whoopsie. |

### Authentication errors

Errors pertaining to authentication are standard errors but also contain extra information to follow the OAuth specification. Specifically, they contain the `error` key with the following values:

##### `error` argument values

| Value | Meaning |
| --- | --- |
| `invalid_token` | The supplied access token is invalid or has expired. |