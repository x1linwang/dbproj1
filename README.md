# proj1-3
CS4111 Project 1
1,PostgreSQL account: psql -U xw2767 -h 34.75.150.200 -d proj1part2
  Password: 7210
2,URL of your web applicationL:http://0.0.0.0:8111/
3,Description of part 1: 
    What is implemented: Our application does take a user’s input of information about the restaurant and return all restaurants (limit 20 here) that satisfies the user’s input and take a user’s input of a restaurant name and return all details we have on that restaurant. For example, a user specifies a restaurant category (we have Japanese, Italian, American, Chinese in our database), our application will return restaurants that match the user’s inputs if we have them in the database. If we don’t we’ll let the user know that there’s no restaurant that matches the specified requirements. The user can also search for dietary needs and we’ll return 20 restaurants that satisfy the needs (ex. Vegan). If the user’s input is a restaurant name, our application will return the details of that restaurant, such as order options (Dine-in, take-out, delivery, etc), menus, location, recent user reviews and employee reviews. Users of our database will also be able to write reviews for restaurants, which will be stored in the database. 
    What is not implemented: 
    Location query (for instance, “70 Morningside Dr”): There are too many locations for all the restaurants we have in database. It will cost a lot of time to categorize restaurants based on their locations.
    The user will not see the price level of each restaurant (ex. $/$$/$$$$): Some of the restaurants just not have the dollar symbol when we conducted the API requests.
    Each order option shows no different commission fees (this is for the option of delivery): We feel this could be ignored since there are only a few popular delivery apps and users don't really care about the commission fees.

4,index.html has an interesting function that can do a database operation that requests restaurants above the rating given by the users. The function  created in server.py gives the detailed database operations using engine and sql query. 
 Query.html displays the results from the database operations conducted by server.py. 
   
