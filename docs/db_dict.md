# Database Schema Documentation

## Rental Table

| Field            | Type         | Constraints                             | Description                                      |
|------------------|--------------|-----------------------------------------|--------------------------------------------------|
| id               | integer      | Auto Increment, Primary Key             | Unique identifier for each rental listing        |
| title            | text         | NULL                                    | Title of the rental listing                     |
| description      | text         | NULL                                    | Detailed description of the rental listing       |
| show_analytics   | boolean      | NULL                                    | Indicates if analytics are to be displayed      |
| created_at       | timestamp    | NULL                                    | Timestamp indicating when the listing was created|
| is_from_store    | boolean      | NULL                                    | Indicates if the rental is from a store         |
| like_count       | integer      | NULL                                    | Count of likes or favorites for the listing     |
| status           | text         | NULL                                    | Current status of the rental listing            |
| price            | bigint       | NULL                                    | Price of the rental                             |
| price_preview    | bigint       | NULL                                    | Preview price for the rental                    |
| price_unit       | text         | NULL                                    | Unit of currency for the price                  |
| price_type       | text         | NULL                                    | Type of pricing (e.g., per night, per month)    |
| exchange_type    | text         | NULL                                    | Type of exchange (if applicable)                |
| small_description| jsonb        | NULL                                    | Small description in JSON format (are in m2)    |
| category_name    | text         | NULL                                    | Name of the category the rental belongs to      |
| city_id          | integer      | NULL                                    | ID of the city where the rental is located      |
| city_name        | text         | NULL                                    | Name of the city where the rental is located    |
| region_id        | text         | NULL                                    | ID of the region where the rental is located    |
| region_name      | text         | NULL                                    | Name of the region where the rental is located  |
| media_url        | text         | NULL                                    | URL for images associated with the rental        |
| store_id         | integer      | NULL                                    | ID of the store (if applicable)                |
| store_name       | text         | NULL                                    | Name of the store (if applicable)              |
| store_image_url  | text         | NULL                                    | URL for the store's image (if applicable)      |
| user_id          | integer      | NULL                                    | ID of the user associated with the rental       |

